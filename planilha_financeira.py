"""
Sistema de Controle Financeiro Pessoal
Autor: Alexis
Data: Janeiro 2026

Funcionalidades:
- Registro de gastos por categoria
- Controle de investimentos
- Gestão de orçamento
- Controle de cartão de crédito
- Dashboard com visualizações
- Projeções e análise anual
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# Configuração visual
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

class ControleFinanceiro:
    def __init__(self, arquivo_base="controle_financeiro"):
        """Inicializa o sistema de controle financeiro"""
        self.arquivo_base = arquivo_base
        self.pasta_dados = Path("dados_financeiros")
        self.pasta_dados.mkdir(exist_ok=True)
        
        # Arquivos de dados
        self.arquivo_gastos = self.pasta_dados / f"{arquivo_base}_gastos.csv"
        self.arquivo_investimentos = self.pasta_dados / f"{arquivo_base}_investimentos.csv"
        self.arquivo_orcamento = self.pasta_dados / f"{arquivo_base}_orcamento.csv"
        self.arquivo_cartao = self.pasta_dados / f"{arquivo_base}_cartao.csv"
        self.arquivo_receitas = self.pasta_dados / f"{arquivo_base}_receitas.csv"
        
        # Carregar ou criar DataFrames
        self.carregar_dados()
        
    def carregar_dados(self):
        """Carrega os dados existentes ou cria novos DataFrames"""
        # Gastos
        if self.arquivo_gastos.exists():
            self.gastos = pd.read_csv(self.arquivo_gastos, parse_dates=['data'])
        else:
            self.gastos = pd.DataFrame({
                'data': pd.Series(dtype='datetime64[ns]'),
                'categoria': pd.Series(dtype='str'),
                'descricao': pd.Series(dtype='str'),
                'valor': pd.Series(dtype='float64'),
                'forma_pagamento': pd.Series(dtype='str')
            })
        
        # Investimentos
        if self.arquivo_investimentos.exists():
            self.investimentos = pd.read_csv(self.arquivo_investimentos, parse_dates=['data'])
        else:
            self.investimentos = pd.DataFrame({
                'data': pd.Series(dtype='datetime64[ns]'),
                'tipo': pd.Series(dtype='str'),
                'objetivo': pd.Series(dtype='str'),
                'valor': pd.Series(dtype='float64'),
                'rentabilidade_mensal': pd.Series(dtype='float64')
            })

        # Garantir coluna objetivo existe mesmo em dados antigos
        if 'objetivo' not in self.investimentos.columns:
            self.investimentos['objetivo'] = 'Geral'
        
        # Orçamento
        if self.arquivo_orcamento.exists():
            self.orcamento = pd.read_csv(self.arquivo_orcamento)
        else:
            self.orcamento = pd.DataFrame(columns=['categoria', 'limite_mensal'])
            self._criar_orcamento_padrao()
        
        # Cartão de Crédito
        if self.arquivo_cartao.exists():
            self.cartao = pd.read_csv(self.arquivo_cartao, parse_dates=['data_compra', 'vencimento_fatura'])
        else:
            self.cartao = pd.DataFrame({
                'data_compra': pd.Series(dtype='datetime64[ns]'),
                'descricao': pd.Series(dtype='str'),
                'valor': pd.Series(dtype='float64'),
                'parcelas': pd.Series(dtype='int64'),
                'parcela_atual': pd.Series(dtype='int64'),
                'vencimento_fatura': pd.Series(dtype='datetime64[ns]'),
                'pago': pd.Series(dtype='bool')
            })
        
        # Receitas
        if self.arquivo_receitas.exists():
            self.receitas = pd.read_csv(self.arquivo_receitas, parse_dates=['data'])
        else:
            self.receitas = pd.DataFrame({
                'data': pd.Series(dtype='datetime64[ns]'),
                'fonte': pd.Series(dtype='str'),
                'valor': pd.Series(dtype='float64'),
                'tipo': pd.Series(dtype='str')
            })
    
    def _criar_orcamento_padrao(self):
        """Cria orçamento padrão apenas para o cartão de crédito."""
        self.orcamento = pd.DataFrame([
            {'categoria': 'Cartão de Crédito', 'limite_mensal': 1500}
        ])
    
    def salvar_dados(self):
        """Salva todos os dados em arquivos CSV"""
        self.gastos.to_csv(self.arquivo_gastos, index=False)
        self.investimentos.to_csv(self.arquivo_investimentos, index=False)
        self.orcamento.to_csv(self.arquivo_orcamento, index=False)
        self.cartao.to_csv(self.arquivo_cartao, index=False)
        self.receitas.to_csv(self.arquivo_receitas, index=False)
        print("✓ Dados salvos com sucesso!")
    
    # ========== RECEITAS ==========
    def adicionar_receita(self, data, fonte, valor, tipo='Salário'):
        """
        Adiciona uma receita
        
        Parâmetros:
        - data: Data da receita (formato 'YYYY-MM-DD')
        - fonte: Origem da receita
        - valor: Valor recebido
        - tipo: Tipo de receita (Salário, Freelance, Investimento, Outros)
        """
        nova_receita = pd.DataFrame([{
            'data': pd.to_datetime(data),
            'fonte': fonte,
            'valor': float(valor),
            'tipo': tipo
        }])
        self.receitas = pd.concat([self.receitas, nova_receita], ignore_index=True)
        print(f"✓ Receita adicionada: R$ {valor:.2f} - {fonte}")
    
    # ========== GASTOS ==========
    def adicionar_gasto(self, data, categoria, descricao, valor, forma_pagamento='Débito'):
        """
        Adiciona um gasto
        
        Parâmetros:
        - data: Data do gasto (formato 'YYYY-MM-DD')
        - categoria: Categoria do gasto
        - descricao: Descrição detalhada
        - valor: Valor gasto
        - forma_pagamento: Débito, Dinheiro, PIX, etc.
        """
        novo_gasto = pd.DataFrame([{
            'data': pd.to_datetime(data),
            'categoria': categoria,
            'descricao': descricao,
            'valor': float(valor),
            'forma_pagamento': forma_pagamento
        }])
        self.gastos = pd.concat([self.gastos, novo_gasto], ignore_index=True)
        print(f"✓ Gasto adicionado: R$ {valor:.2f} - {descricao}")
    
    # ========== INVESTIMENTOS ==========
    def adicionar_investimento(self, data, tipo, valor, rentabilidade_mensal=0.0, objetivo='Geral'):
        """
        Adiciona um investimento
        
        Parâmetros:
        - data: Data do investimento
        - tipo: Tipo (Poupança, Tesouro Direto, CDB, Ações, etc.)
        - valor: Valor investido
        - rentabilidade_mensal: Taxa de rentabilidade mensal em % (ex: 0.5 para 0.5%)
        - objetivo: Meta/caixinha (ex: Casa, Viagem, Emergência)
        """
        novo_investimento = pd.DataFrame([{
            'data': pd.to_datetime(data),
            'tipo': tipo,
            'objetivo': objetivo,
            'valor': float(valor),
            'rentabilidade_mensal': float(rentabilidade_mensal)
        }])
        self.investimentos = pd.concat([self.investimentos, novo_investimento], ignore_index=True)
        print(f"✓ Investimento adicionado: R$ {valor:.2f} em {tipo} (objetivo: {objetivo})")
    
    # ========== CARTÃO DE CRÉDITO ==========
    def adicionar_compra_cartao(self, data_compra, descricao, valor, parcelas=1, vencimento_fatura=None):
        """
        Adiciona uma compra no cartão de crédito
        
        Parâmetros:
        - data_compra: Data da compra
        - descricao: Descrição da compra
        - valor: Valor total
        - parcelas: Número de parcelas
        - vencimento_fatura: Data de vencimento da fatura (se None, usa dia 10 do próximo mês)
        """
        data_compra = pd.to_datetime(data_compra)
        
        if vencimento_fatura is None:
            # Assume vencimento no dia 10 do próximo mês
            if data_compra.day <= 10:
                vencimento = data_compra.replace(day=10)
            else:
                if data_compra.month == 12:
                    vencimento = data_compra.replace(year=data_compra.year+1, month=1, day=10)
                else:
                    vencimento = data_compra.replace(month=data_compra.month+1, day=10)
        else:
            vencimento = pd.to_datetime(vencimento_fatura)
        
        valor_parcela = valor / parcelas
        
        # Adiciona cada parcela
        for i in range(parcelas):
            nova_compra = pd.DataFrame([{
                'data_compra': data_compra,
                'descricao': f"{descricao} ({i+1}/{parcelas})" if parcelas > 1 else descricao,
                'valor': valor_parcela,
                'parcelas': parcelas,
                'parcela_atual': i+1,
                'vencimento_fatura': vencimento + pd.DateOffset(months=i),
                'pago': False
            }])
            self.cartao = pd.concat([self.cartao, nova_compra], ignore_index=True)
        
        # Garantir que as colunas de data sejam datetime
        self.cartao['data_compra'] = pd.to_datetime(self.cartao['data_compra'])
        self.cartao['vencimento_fatura'] = pd.to_datetime(self.cartao['vencimento_fatura'])

        # Aviso de estouro de orçamento do cartão
        try:
            limite_cartao = self.orcamento.loc[self.orcamento['categoria'] == 'Cartão de Crédito', 'limite_mensal']
            if not limite_cartao.empty:
                limite = float(limite_cartao.iloc[0])
                mes_fatura = (vencimento).to_period('M')
                total_mes = self.cartao[self.cartao['vencimento_fatura'].dt.to_period('M') == mes_fatura]['valor'].sum()
                if total_mes > limite:
                    estouro = total_mes - limite
                    print(f"⚠️  Orçamento do cartão estourado em R$ {estouro:.2f} para a fatura de {mes_fatura}.")
        except Exception:
            # Não bloqueia o fluxo se algo der errado no cálculo do aviso
            pass
        
        print(f"✓ Compra no cartão adicionada: R$ {valor:.2f} em {parcelas}x")
    
    def marcar_fatura_paga(self, mes, ano):
        """Marca uma fatura como paga"""
        mask = (self.cartao['vencimento_fatura'].dt.month == mes) & \
               (self.cartao['vencimento_fatura'].dt.year == ano)
        self.cartao.loc[mask, 'pago'] = True
        valor_total = self.cartao[mask]['valor'].sum()
        print(f"✓ Fatura de {mes}/{ano} marcada como paga: R$ {valor_total:.2f}")
    
    # ========== ORÇAMENTO ==========
    def atualizar_orcamento(self, categoria, limite_mensal):
        """Atualiza o limite de orçamento de uma categoria"""
        if categoria in self.orcamento['categoria'].values:
            self.orcamento.loc[self.orcamento['categoria'] == categoria, 'limite_mensal'] = limite_mensal
        else:
            nova_categoria = pd.DataFrame([{'categoria': categoria, 'limite_mensal': limite_mensal}])
            self.orcamento = pd.concat([self.orcamento, nova_categoria], ignore_index=True)
        print(f"✓ Orçamento atualizado: {categoria} - R$ {limite_mensal:.2f}/mês")
    
    def visualizar_orcamento(self):
        """Exibe o orçamento atual"""
        print("\n" + "="*50)
        print("ORÇAMENTO MENSAL")
        print("="*50)
        for _, row in self.orcamento.iterrows():
            print(f"{row['categoria']:20s}: R$ {row['limite_mensal']:10.2f}")
        print("="*50)
        print(f"{'TOTAL':20s}: R$ {self.orcamento['limite_mensal'].sum():10.2f}")
        print("="*50)
    
    # ========== ANÁLISES ==========
    def resumo_mensal(self, mes=None, ano=None):
        """Gera resumo financeiro do mês"""
        if mes is None:
            mes = datetime.now().month
        if ano is None:
            ano = datetime.now().year
        
        print("\n" + "="*60)
        print(f"RESUMO FINANCEIRO - {mes:02d}/{ano}")
        print("="*60)
        
        # Garantir que coluna 'pago' existe no cartão
        if len(self.cartao) > 0 and 'pago' not in self.cartao.columns:
            self.cartao['pago'] = False
        
        # Filtrar dados do mês
        mask_gastos = (self.gastos['data'].dt.month == mes) & (self.gastos['data'].dt.year == ano) if len(self.gastos) > 0 else pd.Series(dtype=bool)
        mask_receitas = (self.receitas['data'].dt.month == mes) & (self.receitas['data'].dt.year == ano) if len(self.receitas) > 0 else pd.Series(dtype=bool)
        mask_investimentos = (self.investimentos['data'].dt.month == mes) & (self.investimentos['data'].dt.year == ano) if len(self.investimentos) > 0 else pd.Series(dtype=bool)
        
        # Calcular totais
        total_receitas = self.receitas[mask_receitas]['valor'].sum() if len(self.receitas) > 0 else 0
        total_gastos = self.gastos[mask_gastos]['valor'].sum() if len(self.gastos) > 0 else 0
        total_investimentos = self.investimentos[mask_investimentos]['valor'].sum() if len(self.investimentos) > 0 else 0
        
        # Calcular total do cartão
        if len(self.cartao) > 0:
            mask_cartao = (self.cartao['vencimento_fatura'].dt.month == mes) & (self.cartao['vencimento_fatura'].dt.year == ano)
            total_cartao = self.cartao[mask_cartao & (self.cartao['pago'] == False)]['valor'].sum()
        else:
            total_cartao = 0
        
        print(f"\n💰 RECEITAS:              R$ {total_receitas:10.2f}")
        print(f"💸 GASTOS:                R$ {total_gastos:10.2f}")
        print(f"📊 INVESTIMENTOS:         R$ {total_investimentos:10.2f}")
        print(f"💳 FATURA DO CARTÃO:      R$ {total_cartao:10.2f}")
        print("-" * 60)
        
        saldo = total_receitas - total_gastos - total_investimentos - total_cartao
        print(f"💵 SALDO DO MÊS:          R$ {saldo:10.2f}")
        
        # Gastos por categoria
        if mask_gastos.sum() > 0:
            print("\n📌 GASTOS POR CATEGORIA:")
            gastos_categoria = self.gastos[mask_gastos].groupby('categoria')['valor'].sum().sort_values(ascending=False)
            for cat, valor in gastos_categoria.items():
                # Comparar com orçamento
                if cat in self.orcamento['categoria'].values:
                    limite = self.orcamento[self.orcamento['categoria'] == cat]['limite_mensal'].values[0]
                    percentual = (valor / limite) * 100
                    status = "⚠️" if percentual > 90 else "✓"
                    print(f"  {status} {cat:20s}: R$ {valor:8.2f} / R$ {limite:8.2f} ({percentual:.0f}%)")
                else:
                    print(f"    {cat:20s}: R$ {valor:8.2f}")
        
        print("="*60)
        
        return {
            'mes': mes,
            'ano': ano,
            'receitas': total_receitas,
            'gastos': total_gastos,
            'investimentos': total_investimentos,
            'cartao': total_cartao,
            'saldo': saldo
        }
    
    def resumo_anual(self, ano=None):
        """Gera resumo financeiro anual"""
        if ano is None:
            ano = datetime.now().year
        
        print("\n" + "="*70)
        print(f"RESUMO FINANCEIRO ANUAL - {ano}")
        print("="*70)
        
        resumos_mensais = []
        for mes in range(1, 13):
            mask_gastos = (self.gastos['data'].dt.month == mes) & (self.gastos['data'].dt.year == ano)
            mask_receitas = (self.receitas['data'].dt.month == mes) & (self.receitas['data'].dt.year == ano)
            mask_investimentos = (self.investimentos['data'].dt.month == mes) & (self.investimentos['data'].dt.year == ano)
            
            total_receitas = self.receitas[mask_receitas]['valor'].sum()
            total_gastos = self.gastos[mask_gastos]['valor'].sum()
            total_investimentos = self.investimentos[mask_investimentos]['valor'].sum()
            saldo = total_receitas - total_gastos - total_investimentos
            
            resumos_mensais.append({
                'Mês': f"{mes:02d}/{ano}",
                'Receitas': total_receitas,
                'Gastos': total_gastos,
                'Investimentos': total_investimentos,
                'Saldo': saldo
            })
        
        df_anual = pd.DataFrame(resumos_mensais)
        print(df_anual.to_string(index=False))
        
        print("\n" + "="*70)
        print(f"{'TOTAL ANUAL':15s}")
        print("-"*70)
        print(f"💰 Receitas:       R$ {df_anual['Receitas'].sum():12.2f}")
        print(f"💸 Gastos:         R$ {df_anual['Gastos'].sum():12.2f}")
        print(f"📊 Investimentos:  R$ {df_anual['Investimentos'].sum():12.2f}")
        print(f"💵 Saldo Total:    R$ {df_anual['Saldo'].sum():12.2f}")
        
        # Média mensal
        print("\n" + "-"*70)
        print(f"{'MÉDIA MENSAL':15s}")
        print("-"*70)
        print(f"💰 Receitas:       R$ {df_anual['Receitas'].mean():12.2f}")
        print(f"💸 Gastos:         R$ {df_anual['Gastos'].mean():12.2f}")
        print(f"📊 Investimentos:  R$ {df_anual['Investimentos'].mean():12.2f}")
        print(f"💵 Saldo Médio:    R$ {df_anual['Saldo'].mean():12.2f}")
        print("="*70)
        
        return df_anual
    
    def projecao_anual(self, ano=None):
        """Projeta quanto poderá poupar no ano mantendo o padrão atual"""
        if ano is None:
            ano = datetime.now().year
        
        # Calcular média dos últimos 3 meses
        data_limite = datetime.now() - timedelta(days=90)
        mask_recente_gastos = self.gastos['data'] >= data_limite
        mask_recente_receitas = self.receitas['data'] >= data_limite
        mask_recente_investimentos = self.investimentos['data'] >= data_limite
        
        if len(self.gastos[mask_recente_gastos]) > 0:
            # Calcular médias mensais
            meses_unicos = len(self.gastos[mask_recente_gastos]['data'].dt.to_period('M').unique())
            media_gastos = self.gastos[mask_recente_gastos]['valor'].sum() / max(meses_unicos, 1)
        else:
            media_gastos = 0
        
        if len(self.receitas[mask_recente_receitas]) > 0:
            meses_unicos = len(self.receitas[mask_recente_receitas]['data'].dt.to_period('M').unique())
            media_receitas = self.receitas[mask_recente_receitas]['valor'].sum() / max(meses_unicos, 1)
        else:
            media_receitas = 0
        
        if len(self.investimentos[mask_recente_investimentos]) > 0:
            meses_unicos = len(self.investimentos[mask_recente_investimentos]['data'].dt.to_period('M').unique())
            media_investimentos = self.investimentos[mask_recente_investimentos]['valor'].sum() / max(meses_unicos, 1)
        else:
            media_investimentos = 0
        
        # Projeção para 12 meses
        meses_restantes = 12 - datetime.now().month + 1
        
        print("\n" + "="*70)
        print(f"PROJEÇÃO ANUAL - {ano}")
        print("="*70)
        print("\nBaseado na média dos últimos 3 meses:\n")
        print(f"📊 Receita Mensal Média:      R$ {media_receitas:12.2f}")
        print(f"💸 Gastos Mensais Médios:     R$ {media_gastos:12.2f}")
        print(f"📈 Investimentos Mensais:     R$ {media_investimentos:12.2f}")
        
        saldo_mensal = media_receitas - media_gastos - media_investimentos
        print(f"\n💵 Sobra Mensal Estimada:     R$ {saldo_mensal:12.2f}")
        
        print("\n" + "-"*70)
        print("PROJEÇÃO ANUAL:")
        print("-"*70)
        print(f"💰 Total de Receitas:         R$ {media_receitas * 12:12.2f}")
        print(f"💸 Total de Gastos:           R$ {media_gastos * 12:12.2f}")
        print(f"📊 Total em Investimentos:    R$ {media_investimentos * 12:12.2f}")
        print(f"\n💵 POUPANÇA ANUAL ESTIMADA:   R$ {saldo_mensal * 12:12.2f}")
        
        if meses_restantes > 0:
            print(f"\n📅 Até o final de {ano}:       R$ {saldo_mensal * meses_restantes:12.2f}")
        
        # Taxa de poupança
        if media_receitas > 0:
            taxa_poupanca = (saldo_mensal / media_receitas) * 100
            print(f"\n📈 Taxa de Poupança:          {taxa_poupanca:.1f}%")
            
            if taxa_poupanca < 10:
                print("   ⚠️ Atenção: Taxa de poupança baixa!")
            elif taxa_poupanca >= 20:
                print("   ✓ Excelente! Você está poupando bem!")
        
        print("="*70)
        
        return {
            'media_receitas': media_receitas,
            'media_gastos': media_gastos,
            'media_investimentos': media_investimentos,
            'saldo_mensal': saldo_mensal,
            'poupanca_anual': saldo_mensal * 12,
            'meses_restantes': meses_restantes
        }
    
    def status_cartao_credito(self):
        """Exibe o status atual do cartão de crédito"""
        print("\n" + "="*70)
        print("STATUS DO CARTÃO DE CRÉDITO")
        print("="*70)
        
        if len(self.cartao) == 0:
            print("\nNenhuma compra no cartão registrada.")
            return
        
        # Garantir que a coluna 'pago' existe e é booleana
        if 'pago' not in self.cartao.columns:
            self.cartao['pago'] = False
        else:
            # Converter para booleano se necessário
            self.cartao['pago'] = self.cartao['pago'].astype(bool)
        
        # Faturas não pagas
        cartao_aberto = self.cartao[self.cartao['pago'] == False]
        
        if len(cartao_aberto) == 0:
            print("\n✓ Todas as faturas estão pagas!")
            return
        
        # Agrupar por mês de vencimento
        cartao_aberto['mes_vencimento'] = cartao_aberto['vencimento_fatura'].dt.to_period('M')
        faturas = cartao_aberto.groupby('mes_vencimento')['valor'].sum().sort_index()
        
        print("\n💳 FATURAS EM ABERTO:\n")
        total_devido = 0
        for periodo, valor in faturas.items():
            mes_ano = periodo.strftime('%m/%Y')
            vencimento = cartao_aberto[cartao_aberto['mes_vencimento'] == periodo]['vencimento_fatura'].iloc[0]
            dias_vencimento = (vencimento - datetime.now()).days
            
            status = ""
            if dias_vencimento < 0:
                status = "⚠️ VENCIDA"
            elif dias_vencimento <= 5:
                status = "⚠️ VENCE EM BREVE"
            else:
                status = f"Vence em {dias_vencimento} dias"
            
            print(f"  {mes_ano}: R$ {valor:10.2f} - {status}")
            total_devido += valor
        
        print("\n" + "-"*70)
        print(f"{'TOTAL DEVIDO:':30s} R$ {total_devido:10.2f}")
        print("="*70)
        
        # Próximas parcelas
        print("\n📋 PRÓXIMAS PARCELAS:\n")
        proximas = cartao_aberto.sort_values('vencimento_fatura').head(10)
        for _, row in proximas.iterrows():
            print(f"  {row['vencimento_fatura'].strftime('%d/%m/%Y')}: R$ {row['valor']:8.2f} - {row['descricao']}")
    
    # ========== DASHBOARD ==========
    def gerar_dashboard(self, mes=None, ano=None):
        """Gera dashboard visual com gráficos"""
        if mes is None:
            mes = datetime.now().month
        if ano is None:
            ano = datetime.now().year
        
        # Filtrar dados
        mask_gastos = (self.gastos['data'].dt.month == mes) & (self.gastos['data'].dt.year == ano)
        mask_receitas = (self.receitas['data'].dt.month == mes) & (self.receitas['data'].dt.year == ano)
        
        # Criar figura com subplots
        fig = plt.figure(figsize=(16, 10))
        fig.suptitle(f'Dashboard Financeiro - {mes:02d}/{ano}', fontsize=16, fontweight='bold')
        
        # 1. Pizza de gastos por categoria
        ax1 = plt.subplot(2, 3, 1)
        if mask_gastos.sum() > 0:
            gastos_cat = self.gastos[mask_gastos].groupby('categoria')['valor'].sum()
            colors = sns.color_palette('husl', len(gastos_cat))
            ax1.pie(gastos_cat.values, labels=gastos_cat.index, autopct='%1.1f%%', colors=colors)
            ax1.set_title('Gastos por Categoria')
        else:
            ax1.text(0.5, 0.5, 'Sem dados', ha='center', va='center')
            ax1.set_title('Gastos por Categoria')
        
        # 2. Comparação Orçamento vs Real
        ax2 = plt.subplot(2, 3, 2)
        if mask_gastos.sum() > 0 and len(self.orcamento) > 0:
            gastos_cat = self.gastos[mask_gastos].groupby('categoria')['valor'].sum()
            categorias = []
            orcado = []
            realizado = []
            
            for _, row in self.orcamento.iterrows():
                cat = row['categoria']
                if cat in gastos_cat.index:
                    categorias.append(cat)
                    orcado.append(row['limite_mensal'])
                    realizado.append(gastos_cat[cat])
            
            x = np.arange(len(categorias))
            width = 0.35
            ax2.bar(x - width/2, orcado, width, label='Orçado', color='lightblue')
            ax2.bar(x + width/2, realizado, width, label='Realizado', color='coral')
            ax2.set_xlabel('Categoria')
            ax2.set_ylabel('Valor (R$)')
            ax2.set_title('Orçamento vs Realizado')
            ax2.set_xticks(x)
            ax2.set_xticklabels(categorias, rotation=45, ha='right')
            ax2.legend()
            ax2.grid(axis='y', alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'Sem dados', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Orçamento vs Realizado')
        
        # 3. Fluxo de caixa mensal
        ax3 = plt.subplot(2, 3, 3)
        meses_analise = []
        receitas_mes = []
        gastos_mes = []
        
        for m in range(max(1, mes-5), mes+1):
            mask_g = (self.gastos['data'].dt.month == m) & (self.gastos['data'].dt.year == ano)
            mask_r = (self.receitas['data'].dt.month == m) & (self.receitas['data'].dt.year == ano)
            
            if mask_g.sum() > 0 or mask_r.sum() > 0:
                meses_analise.append(f"{m:02d}")
                receitas_mes.append(self.receitas[mask_r]['valor'].sum())
                gastos_mes.append(self.gastos[mask_g]['valor'].sum())
        
        if meses_analise:
            x = np.arange(len(meses_analise))
            width = 0.35
            ax3.bar(x - width/2, receitas_mes, width, label='Receitas', color='green', alpha=0.7)
            ax3.bar(x + width/2, gastos_mes, width, label='Gastos', color='red', alpha=0.7)
            ax3.set_xlabel('Mês')
            ax3.set_ylabel('Valor (R$)')
            ax3.set_title('Fluxo de Caixa (últimos 6 meses)')
            ax3.set_xticks(x)
            ax3.set_xticklabels(meses_analise)
            ax3.legend()
            ax3.grid(axis='y', alpha=0.3)
        else:
            ax3.text(0.5, 0.5, 'Sem dados', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Fluxo de Caixa')
        
        # 4. Evolução dos investimentos
        ax4 = plt.subplot(2, 3, 4)
        if len(self.investimentos) > 0:
            invest_mensal = self.investimentos.copy()
            invest_mensal['mes'] = invest_mensal['data'].dt.to_period('M')
            invest_acum = invest_mensal.groupby('mes')['valor'].sum().cumsum()
            
            ax4.plot(range(len(invest_acum)), invest_acum.values, marker='o', color='darkgreen', linewidth=2)
            ax4.fill_between(range(len(invest_acum)), invest_acum.values, alpha=0.3, color='green')
            ax4.set_xlabel('Mês')
            ax4.set_ylabel('Valor Acumulado (R$)')
            ax4.set_title('Evolução dos Investimentos')
            ax4.grid(True, alpha=0.3)
            
            # Adicionar labels dos meses
            labels = [str(p) for p in invest_acum.index]
            ax4.set_xticks(range(len(invest_acum)))
            ax4.set_xticklabels(labels, rotation=45, ha='right')
        else:
            ax4.text(0.5, 0.5, 'Sem dados', ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Evolução dos Investimentos')
        
        # 5. Status do cartão de crédito
        ax5 = plt.subplot(2, 3, 5)
        cartao_aberto = self.cartao[~self.cartao['pago']]
        if len(cartao_aberto) > 0:
            cartao_aberto['mes_venc'] = cartao_aberto['vencimento_fatura'].dt.to_period('M')
            faturas = cartao_aberto.groupby('mes_venc')['valor'].sum().sort_index()
            
            colors_bar = ['red' if (pd.Period(p, freq='M').to_timestamp() < datetime.now()) else 'orange' 
                         for p in faturas.index]
            
            ax5.bar(range(len(faturas)), faturas.values, color=colors_bar)
            ax5.set_xlabel('Mês de Vencimento')
            ax5.set_ylabel('Valor (R$)')
            ax5.set_title('Faturas do Cartão de Crédito')
            ax5.set_xticks(range(len(faturas)))
            ax5.set_xticklabels([str(p) for p in faturas.index], rotation=45, ha='right')
            ax5.grid(axis='y', alpha=0.3)
        else:
            ax5.text(0.5, 0.5, 'Nenhuma fatura em aberto', ha='center', va='center', transform=ax5.transAxes)
            ax5.set_title('Faturas do Cartão de Crédito')
        
        # 6. Resumo em texto
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        
        total_receitas = self.receitas[mask_receitas]['valor'].sum()
        total_gastos = self.gastos[mask_gastos]['valor'].sum()
        saldo = total_receitas - total_gastos
        
        resumo_text = f"""
        RESUMO DO MÊS
        
        Receitas:      R$ {total_receitas:,.2f}
        Gastos:        R$ {total_gastos:,.2f}
        ────────────────────────────
        Saldo:         R$ {saldo:,.2f}
        
        """
        
        if total_receitas > 0:
            taxa_poupanca = ((total_receitas - total_gastos) / total_receitas) * 100
            resumo_text += f"Taxa de Poupança: {taxa_poupanca:.1f}%\n"
        
        # Status geral
        if saldo > 0:
            resumo_text += "\n✓ Situação: POSITIVA"
        elif saldo == 0:
            resumo_text += "\n⚠️ Situação: EQUILIBRADA"
        else:
            resumo_text += "\n⚠️ Situação: NEGATIVA"
        
        ax6.text(0.1, 0.5, resumo_text, fontsize=12, family='monospace',
                verticalalignment='center')
        
        plt.tight_layout()
        
        # Salvar dashboard
        arquivo_dashboard = self.pasta_dados / f"dashboard_{ano}_{mes:02d}.png"
        plt.savefig(arquivo_dashboard, dpi=150, bbox_inches='tight')
        print(f"\n✓ Dashboard salvo em: {arquivo_dashboard}")
        
        plt.show()
    
    def exportar_para_excel(self, nome_arquivo=None):
        """Exporta todos os dados para uma planilha Excel formatada com gráficos"""
        try:
            from planilha_financeira_excel import exportar_para_excel
            caminho = exportar_para_excel(self, nome_arquivo)
            return caminho
        except ImportError:
            print("⚠️ Módulo de exportação Excel não encontrado.")
            print("Certifique-se de que o arquivo planilha_financeira_excel.py está na mesma pasta.")
            return None

    def importar_de_excel(self, nome_arquivo=None, preferir_excel=True):
        """Importa dados a partir de um arquivo Excel gerado (ou editado) pelo sistema.

        preferir_excel=True -> Excel é a fonte de verdade e sobrescreve os CSVs.
        preferir_excel=False -> Apenas importa novas linhas; mantém existentes quando houver conflito.
        """
        try:
            from planilha_financeira_excel import importar_de_excel
            importar_de_excel(self, nome_arquivo, preferir_excel)
        except ImportError:
            print("⚠️ Módulo de importação Excel não encontrado.")
            print("Certifique-se de que o arquivo planilha_financeira_excel.py está na mesma pasta.")
    
    def dashboard_anual(self, ano=None):
        """Gera dashboard com visão anual"""
        if ano is None:
            ano = datetime.now().year
        
        fig = plt.figure(figsize=(18, 10))
        fig.suptitle(f'Dashboard Anual - {ano}', fontsize=16, fontweight='bold')
        
        # Preparar dados mensais
        meses = []
        receitas_mensais = []
        gastos_mensais = []
        investimentos_mensais = []
        saldo_mensais = []
        
        for mes in range(1, 13):
            mask_g = (self.gastos['data'].dt.month == mes) & (self.gastos['data'].dt.year == ano)
            mask_r = (self.receitas['data'].dt.month == mes) & (self.receitas['data'].dt.year == ano)
            mask_i = (self.investimentos['data'].dt.month == mes) & (self.investimentos['data'].dt.year == ano)
            
            meses.append(mes)
            rec = self.receitas[mask_r]['valor'].sum()
            gas = self.gastos[mask_g]['valor'].sum()
            inv = self.investimentos[mask_i]['valor'].sum()
            
            receitas_mensais.append(rec)
            gastos_mensais.append(gas)
            investimentos_mensais.append(inv)
            saldo_mensais.append(rec - gas - inv)
        
        # 1. Evolução mensal de receitas e gastos
        ax1 = plt.subplot(2, 3, 1)
        ax1.plot(meses, receitas_mensais, marker='o', label='Receitas', color='green', linewidth=2)
        ax1.plot(meses, gastos_mensais, marker='s', label='Gastos', color='red', linewidth=2)
        ax1.plot(meses, investimentos_mensais, marker='^', label='Investimentos', color='blue', linewidth=2)
        ax1.set_xlabel('Mês')
        ax1.set_ylabel('Valor (R$)')
        ax1.set_title('Evolução Mensal')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(meses)
        
        # 2. Saldo mensal
        ax2 = plt.subplot(2, 3, 2)
        cores_saldo = ['green' if s >= 0 else 'red' for s in saldo_mensais]
        ax2.bar(meses, saldo_mensais, color=cores_saldo, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.set_xlabel('Mês')
        ax2.set_ylabel('Saldo (R$)')
        ax2.set_title('Saldo Mensal')
        ax2.grid(axis='y', alpha=0.3)
        ax2.set_xticks(meses)
        
        # 3. Gastos por categoria (ano completo)
        ax3 = plt.subplot(2, 3, 3)
        mask_ano = self.gastos['data'].dt.year == ano
        if mask_ano.sum() > 0:
            gastos_cat_ano = self.gastos[mask_ano].groupby('categoria')['valor'].sum().sort_values(ascending=False)
            colors = sns.color_palette('husl', len(gastos_cat_ano))
            ax3.barh(range(len(gastos_cat_ano)), gastos_cat_ano.values, color=colors)
            ax3.set_yticks(range(len(gastos_cat_ano)))
            ax3.set_yticklabels(gastos_cat_ano.index)
            ax3.set_xlabel('Valor Total (R$)')
            ax3.set_title('Gastos por Categoria (Anual)')
            ax3.grid(axis='x', alpha=0.3)
        
        # 4. Investimentos acumulados
        ax4 = plt.subplot(2, 3, 4)
        invest_acum = np.cumsum(investimentos_mensais)
        ax4.plot(meses, invest_acum, marker='o', color='darkgreen', linewidth=2)
        ax4.fill_between(meses, invest_acum, alpha=0.3, color='green')
        ax4.set_xlabel('Mês')
        ax4.set_ylabel('Valor Acumulado (R$)')
        ax4.set_title('Investimentos Acumulados')
        ax4.grid(True, alpha=0.3)
        ax4.set_xticks(meses)
        
        # 5. Taxa de poupança mensal
        ax5 = plt.subplot(2, 3, 5)
        taxa_poupanca = []
        for rec, gas, inv in zip(receitas_mensais, gastos_mensais, investimentos_mensais):
            if rec > 0:
                taxa = ((rec - gas - inv) / rec) * 100
                taxa_poupanca.append(taxa)
            else:
                taxa_poupanca.append(0)
        
        cores_taxa = ['green' if t >= 10 else 'orange' if t >= 0 else 'red' for t in taxa_poupanca]
        ax5.bar(meses, taxa_poupanca, color=cores_taxa, alpha=0.7)
        ax5.axhline(y=10, color='green', linestyle='--', linewidth=1, label='Meta: 10%')
        ax5.axhline(y=20, color='darkgreen', linestyle='--', linewidth=1, label='Ideal: 20%')
        ax5.set_xlabel('Mês')
        ax5.set_ylabel('Taxa (%)')
        ax5.set_title('Taxa de Poupança Mensal')
        ax5.legend()
        ax5.grid(axis='y', alpha=0.3)
        ax5.set_xticks(meses)
        
        # 6. Resumo estatístico
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        
        total_rec = sum(receitas_mensais)
        total_gas = sum(gastos_mensais)
        total_inv = sum(investimentos_mensais)
        total_saldo = sum(saldo_mensais)
        
        media_rec = np.mean(receitas_mensais)
        media_gas = np.mean(gastos_mensais)
        media_inv = np.mean(investimentos_mensais)
        media_saldo = np.mean(saldo_mensais)
        
        resumo_text = f"""
        RESUMO ANUAL {ano}
        
        TOTAIS:
        Receitas:         R$ {total_rec:,.2f}
        Gastos:           R$ {total_gas:,.2f}
        Investimentos:    R$ {total_inv:,.2f}
        Saldo Final:      R$ {total_saldo:,.2f}
        
        MÉDIAS MENSAIS:
        Receitas:         R$ {media_rec:,.2f}
        Gastos:           R$ {media_gas:,.2f}
        Investimentos:    R$ {media_inv:,.2f}
        Saldo:            R$ {media_saldo:,.2f}
        
        Taxa Poupança:    {np.mean(taxa_poupanca):.1f}%
        """
        
        ax6.text(0.1, 0.5, resumo_text, fontsize=11, family='monospace',
                verticalalignment='center')
        
        plt.tight_layout()
        
        # Salvar
        arquivo_dashboard = self.pasta_dados / f"dashboard_anual_{ano}.png"
        plt.savefig(arquivo_dashboard, dpi=150, bbox_inches='tight')
        print(f"\n✓ Dashboard anual salvo em: {arquivo_dashboard}")
        
        plt.show()


# ========== FUNÇÕES AUXILIARES ==========

def exemplo_uso():
    """Demonstra o uso do sistema"""
    print("\n" + "="*70)
    print("EXEMPLO DE USO DO SISTEMA DE CONTROLE FINANCEIRO")
    print("="*70)
    
    # Criar instância
    cf = ControleFinanceiro()
    
    # Adicionar algumas receitas
    cf.adicionar_receita('2026-01-05', 'Salário', 5000, 'Salário')
    cf.adicionar_receita('2026-01-15', 'Freelance', 1500, 'Freelance')
    
    # Adicionar gastos
    cf.adicionar_gasto('2026-01-10', 'Alimentação', 'Supermercado', 450, 'Débito')
    cf.adicionar_gasto('2026-01-12', 'Transporte', 'Gasolina', 200, 'Débito')
    cf.adicionar_gasto('2026-01-15', 'Lazer', 'Cinema', 80, 'PIX')
    cf.adicionar_gasto('2026-01-20', 'Alimentação', 'Restaurante', 150, 'Débito')
    
    # Adicionar investimentos
    cf.adicionar_investimento('2026-01-05', 'Tesouro Direto', 1000, 0.8)
    cf.adicionar_investimento('2026-01-05', 'Ações', 500, 1.2)
    
    # Compras no cartão
    cf.adicionar_compra_cartao('2026-01-08', 'Notebook', 3000, 10)
    cf.adicionar_compra_cartao('2026-01-15', 'Roupa', 300, 3)
    
    # Visualizar dados
    cf.visualizar_orcamento()
    cf.resumo_mensal(1, 2026)
    cf.status_cartao_credito()
    cf.projecao_anual(2026)
    
    # Salvar dados
    cf.salvar_dados()
    
    # Gerar dashboards
    cf.gerar_dashboard(1, 2026)
    
    print("\n✓ Exemplo concluído! Verifique a pasta 'dados_financeiros'.")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SISTEMA DE CONTROLE FINANCEIRO PESSOAL")
    print("="*70)
    print("\nPara começar a usar:")
    print("1. Crie uma instância: cf = ControleFinanceiro()")
    print("2. Adicione suas receitas, gastos e investimentos")
    print("3. Visualize relatórios e dashboards")
    print("\nExecute exemplo_uso() para ver uma demonstração completa.")
    print("="*70)
