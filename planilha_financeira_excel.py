"""
Exportador para Excel - Sistema de Controle Financeiro
Cria planilhas Excel interativas e visuais com gráficos e formatação
"""

import pandas as pd
import xlsxwriter
from datetime import datetime
from pathlib import Path

class ExportadorExcel:
    def __init__(self, controle_financeiro):
        """Inicializa o exportador com uma instância de ControleFinanceiro"""
        self.cf = controle_financeiro
        
    def criar_planilha_completa(self, nome_arquivo=None):
        """Cria planilha Excel completa com todas as abas e gráficos"""
        if nome_arquivo is None:
            data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"controle_financeiro_{data_atual}.xlsx"
        
        # Garantir extensão .xlsx
        if not nome_arquivo.endswith('.xlsx'):
            nome_arquivo += '.xlsx'
        
        caminho_completo = self.cf.pasta_dados / nome_arquivo
        
        # Criar arquivo Excel
        writer = pd.ExcelWriter(caminho_completo, engine='xlsxwriter')
        workbook = writer.book
        
        # Definir formatos
        self._definir_formatos(workbook)
        
        # Criar cada aba
        print("\n📊 Criando planilha Excel...")
        self._criar_aba_dashboard(writer, workbook)
        self._criar_aba_resumo_anual(writer, workbook)
        self._criar_aba_gastos(writer, workbook)
        self._criar_aba_receitas(writer, workbook)
        self._criar_aba_investimentos(writer, workbook)
        self._criar_aba_cartao(writer, workbook)
        self._criar_aba_orcamento(writer, workbook)
        self._criar_aba_analise_categorias(writer, workbook)
        
        # Salvar arquivo
        writer.close()
        
        print(f"\n✅ Planilha Excel criada com sucesso!")
        print(f"📁 Arquivo: {caminho_completo}")
        print(f"📊 Tamanho: {caminho_completo.stat().st_size / 1024:.1f} KB")
        
        return caminho_completo
    
    def _definir_formatos(self, workbook):
        """Define os formatos de células"""
        # Títulos
        self.fmt_titulo = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'font_color': 'white',
            'bg_color': '#2C3E50',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        self.fmt_subtitulo = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': '#34495E',
            'font_color': 'white',
            'align': 'center',
            'border': 1
        })
        
        # Cabeçalhos
        self.fmt_header = workbook.add_format({
            'bold': True,
            'bg_color': '#3498DB',
            'font_color': 'white',
            'align': 'center',
            'border': 1
        })
        
        # Valores monetários
        self.fmt_moeda = workbook.add_format({
            'num_format': 'R$ #,##0.00',
            'border': 1
        })
        
        self.fmt_moeda_verde = workbook.add_format({
            'num_format': 'R$ #,##0.00',
            'bg_color': '#D5F4E6',
            'border': 1
        })
        
        self.fmt_moeda_vermelho = workbook.add_format({
            'num_format': 'R$ #,##0.00',
            'bg_color': '#FADBD8',
            'border': 1
        })
        
        self.fmt_moeda_amarelo = workbook.add_format({
            'num_format': 'R$ #,##0.00',
            'bg_color': '#FCF3CF',
            'border': 1
        })
        
        # Percentuais
        self.fmt_percent = workbook.add_format({
            'num_format': '0.0%',
            'border': 1
        })
        
        # Datas
        self.fmt_data = workbook.add_format({
            'num_format': 'dd/mm/yyyy',
            'border': 1,
            'align': 'center'
        })
        
        # Células normais
        self.fmt_normal = workbook.add_format({
            'border': 1
        })
        
        self.fmt_centro = workbook.add_format({
            'border': 1,
            'align': 'center'
        })
        
        # Totais
        self.fmt_total = workbook.add_format({
            'bold': True,
            'num_format': 'R$ #,##0.00',
            'bg_color': '#85C1E9',
            'border': 2
        })
    
    def _criar_aba_dashboard(self, writer, workbook):
        """Cria aba Dashboard com resumo visual"""
        worksheet = workbook.add_worksheet('Dashboard')
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:E', 12)
        
        # Título
        worksheet.merge_range('A1:E1', 'DASHBOARD FINANCEIRO', self.fmt_titulo)
        worksheet.set_row(0, 30)
        
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        
        # Calcular dados do mês
        mask_gastos = (self.cf.gastos['data'].dt.month == mes_atual) & (self.cf.gastos['data'].dt.year == ano_atual) if len(self.cf.gastos) > 0 else pd.Series(dtype=bool)
        mask_receitas = (self.cf.receitas['data'].dt.month == mes_atual) & (self.cf.receitas['data'].dt.year == ano_atual) if len(self.cf.receitas) > 0 else pd.Series(dtype=bool)
        mask_investimentos = (self.cf.investimentos['data'].dt.month == mes_atual) & (self.cf.investimentos['data'].dt.year == ano_atual) if len(self.cf.investimentos) > 0 else pd.Series(dtype=bool)
        
        total_receitas = self.cf.receitas[mask_receitas]['valor'].sum() if len(self.cf.receitas) > 0 else 0
        total_gastos = self.cf.gastos[mask_gastos]['valor'].sum() if len(self.cf.gastos) > 0 else 0
        total_investimentos = self.cf.investimentos[mask_investimentos]['valor'].sum() if len(self.cf.investimentos) > 0 else 0
        
        if len(self.cf.cartao) > 0 and 'pago' in self.cf.cartao.columns:
            mask_cartao = (self.cf.cartao['vencimento_fatura'].dt.month == mes_atual) & (self.cf.cartao['vencimento_fatura'].dt.year == ano_atual)
            total_cartao = self.cf.cartao[mask_cartao & (self.cf.cartao['pago'] == False)]['valor'].sum()
        else:
            total_cartao = 0
        
        saldo = total_receitas - total_gastos - total_investimentos - total_cartao
        
        # Resumo financeiro
        row = 2
        worksheet.merge_range(f'A{row+1}:E{row+1}', f'Resumo - {mes_atual:02d}/{ano_atual}', self.fmt_subtitulo)
        
        row += 2
        worksheet.write(f'A{row+1}', 'Receitas do Mês', self.fmt_header)
        worksheet.write(f'B{row+1}', total_receitas, self.fmt_moeda_verde)
        
        row += 1
        worksheet.write(f'A{row+1}', 'Gastos do Mês', self.fmt_header)
        worksheet.write(f'B{row+1}', total_gastos, self.fmt_moeda_vermelho)
        
        row += 1
        worksheet.write(f'A{row+1}', 'Investimentos do Mês', self.fmt_header)
        worksheet.write(f'B{row+1}', total_investimentos, self.fmt_moeda_amarelo)
        
        row += 1
        worksheet.write(f'A{row+1}', 'Fatura do Cartão', self.fmt_header)
        worksheet.write(f'B{row+1}', total_cartao, self.fmt_moeda_amarelo)
        
        row += 1
        worksheet.write(f'A{row+1}', 'SALDO DO MÊS', self.fmt_header)
        fmt_saldo = self.fmt_moeda_verde if saldo >= 0 else self.fmt_moeda_vermelho
        worksheet.write(f'B{row+1}', saldo, fmt_saldo)
        
        # Taxa de poupança
        if total_receitas > 0:
            taxa_poupanca = saldo / total_receitas
            row += 2
            worksheet.write(f'A{row+1}', 'Taxa de Poupança', self.fmt_header)
            worksheet.write(f'B{row+1}', taxa_poupanca, self.fmt_percent)
        
        # Gráfico de pizza - Distribuição de Gastos
        if len(self.cf.gastos[mask_gastos]) > 0:
            row += 3
            worksheet.merge_range(f'A{row+1}:E{row+1}', 'Gastos por Categoria', self.fmt_subtitulo)
            
            gastos_cat = self.cf.gastos[mask_gastos].groupby('categoria')['valor'].sum().sort_values(ascending=False)
            
            row += 1
            start_row = row
            for cat, valor in gastos_cat.items():
                row += 1
                worksheet.write(f'A{row+1}', cat, self.fmt_normal)
                worksheet.write(f'B{row+1}', valor, self.fmt_moeda)
            
            # Criar gráfico de pizza
            chart = workbook.add_chart({'type': 'pie'})
            chart.add_series({
                'name': 'Gastos por Categoria',
                'categories': f'=Dashboard!$A${start_row+2}:$A${row+1}',
                'values': f'=Dashboard!$B${start_row+2}:$B${row+1}',
                'data_labels': {'percentage': True, 'leader_lines': True}
            })
            chart.set_title({'name': 'Distribuição de Gastos'})
            chart.set_size({'width': 480, 'height': 300})
            worksheet.insert_chart('D4', chart)
    
    def _criar_aba_resumo_anual(self, writer, workbook):
        """Cria aba com resumo anual e gráfico de evolução"""
        worksheet = workbook.add_worksheet('Resumo Anual')
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:E', 15)
        
        # Título
        ano = datetime.now().year
        worksheet.merge_range('A1:E1', f'RESUMO ANUAL - {ano}', self.fmt_titulo)
        worksheet.set_row(0, 30)
        
        # Cabeçalhos
        row = 2
        headers = ['Mês', 'Receitas', 'Gastos', 'Investimentos', 'Saldo']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.fmt_header)
        
        # Dados mensais
        dados_mensais = []
        for mes in range(1, 13):
            mask_g = (self.cf.gastos['data'].dt.month == mes) & (self.cf.gastos['data'].dt.year == ano) if len(self.cf.gastos) > 0 else pd.Series(dtype=bool)
            mask_r = (self.cf.receitas['data'].dt.month == mes) & (self.cf.receitas['data'].dt.year == ano) if len(self.cf.receitas) > 0 else pd.Series(dtype=bool)
            mask_i = (self.cf.investimentos['data'].dt.month == mes) & (self.cf.investimentos['data'].dt.year == ano) if len(self.cf.investimentos) > 0 else pd.Series(dtype=bool)
            
            rec = self.cf.receitas[mask_r]['valor'].sum() if len(self.cf.receitas) > 0 else 0
            gas = self.cf.gastos[mask_g]['valor'].sum() if len(self.cf.gastos) > 0 else 0
            inv = self.cf.investimentos[mask_i]['valor'].sum() if len(self.cf.investimentos) > 0 else 0
            saldo = rec - gas - inv
            
            dados_mensais.append({
                'mes': f'{mes:02d}/{ano}',
                'receitas': rec,
                'gastos': gas,
                'investimentos': inv,
                'saldo': saldo
            })
            
            row += 1
            worksheet.write(row, 0, f'{mes:02d}/{ano}', self.fmt_centro)
            worksheet.write(row, 1, rec, self.fmt_moeda_verde)
            worksheet.write(row, 2, gas, self.fmt_moeda_vermelho)
            worksheet.write(row, 3, inv, self.fmt_moeda_amarelo)
            fmt_saldo = self.fmt_moeda_verde if saldo >= 0 else self.fmt_moeda_vermelho
            worksheet.write(row, 4, saldo, fmt_saldo)
        
        # Totais
        row += 1
        worksheet.write(row, 0, 'TOTAL', self.fmt_header)
        for col in range(1, 5):
            worksheet.write(row, col, f'=SUM({chr(66+col-1)}4:{chr(66+col-1)}{row})', self.fmt_total)
        
        # Gráfico de linhas
        chart = workbook.add_chart({'type': 'line'})
        chart.add_series({
            'name': 'Receitas',
            'categories': f'=\'Resumo Anual\'!$A$4:$A$15',
            'values': f'=\'Resumo Anual\'!$B$4:$B$15',
            'line': {'color': 'green', 'width': 2}
        })
        chart.add_series({
            'name': 'Gastos',
            'categories': f'=\'Resumo Anual\'!$A$4:$A$15',
            'values': f'=\'Resumo Anual\'!$C$4:$C$15',
            'line': {'color': 'red', 'width': 2}
        })
        chart.add_series({
            'name': 'Investimentos',
            'categories': f'=\'Resumo Anual\'!$A$4:$A$15',
            'values': f'=\'Resumo Anual\'!$D$4:$D$15',
            'line': {'color': 'blue', 'width': 2}
        })
        chart.set_title({'name': 'Evolução Mensal'})
        chart.set_x_axis({'name': 'Mês'})
        chart.set_y_axis({'name': 'Valor (R$)'})
        chart.set_size({'width': 720, 'height': 400})
        chart.set_legend({'position': 'bottom'})
        worksheet.insert_chart('G3', chart)
    
    def _criar_aba_gastos(self, writer, workbook):
        """Cria aba detalhada de gastos"""
        if len(self.cf.gastos) == 0:
            return
        
        worksheet = workbook.add_worksheet('Gastos')
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 35)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        
        # Título
        worksheet.merge_range('A1:E1', 'GASTOS DETALHADOS', self.fmt_titulo)
        worksheet.set_row(0, 30)
        
        # Cabeçalhos
        headers = ['Data', 'Categoria', 'Descrição', 'Valor', 'Forma Pgto']
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.fmt_header)
        
        # Dados ordenados por data
        gastos_ordenados = self.cf.gastos.sort_values('data', ascending=False)
        
        for idx, (_, row_data) in enumerate(gastos_ordenados.iterrows(), start=3):
            worksheet.write_datetime(idx, 0, row_data['data'], self.fmt_data)
            worksheet.write(idx, 1, row_data['categoria'], self.fmt_normal)
            worksheet.write(idx, 2, row_data['descricao'], self.fmt_normal)
            worksheet.write(idx, 3, row_data['valor'], self.fmt_moeda)
            worksheet.write(idx, 4, row_data['forma_pagamento'], self.fmt_centro)
        
        # Total
        total_row = len(gastos_ordenados) + 3
        worksheet.write(total_row, 2, 'TOTAL', self.fmt_header)
        worksheet.write(total_row, 3, f'=SUM(D4:D{total_row})', self.fmt_total)
        
        # Filtros automáticos
        worksheet.autofilter(2, 0, total_row, 4)
    
    def _criar_aba_receitas(self, writer, workbook):
        """Cria aba detalhada de receitas"""
        if len(self.cf.receitas) == 0:
            return
        
        worksheet = workbook.add_worksheet('Receitas')
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:C', 25)
        worksheet.set_column('D:D', 15)
        
        # Título
        worksheet.merge_range('A1:D1', 'RECEITAS DETALHADAS', self.fmt_titulo)
        worksheet.set_row(0, 30)
        
        # Cabeçalhos
        headers = ['Data', 'Fonte', 'Tipo', 'Valor']
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.fmt_header)
        
        # Dados
        receitas_ordenadas = self.cf.receitas.sort_values('data', ascending=False)
        
        for idx, (_, row_data) in enumerate(receitas_ordenadas.iterrows(), start=3):
            worksheet.write_datetime(idx, 0, row_data['data'], self.fmt_data)
            worksheet.write(idx, 1, row_data['fonte'], self.fmt_normal)
            worksheet.write(idx, 2, row_data['tipo'], self.fmt_normal)
            worksheet.write(idx, 3, row_data['valor'], self.fmt_moeda_verde)
        
        # Total
        total_row = len(receitas_ordenadas) + 3
        worksheet.write(total_row, 2, 'TOTAL', self.fmt_header)
        worksheet.write(total_row, 3, f'=SUM(D4:D{total_row})', self.fmt_total)
        
        worksheet.autofilter(2, 0, total_row, 3)
    
    def _criar_aba_investimentos(self, writer, workbook):
        """Cria aba detalhada de investimentos"""
        if len(self.cf.investimentos) == 0:
            return
        
        worksheet = workbook.add_worksheet('Investimentos')
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        
        # Título
        worksheet.merge_range('A1:E1', 'INVESTIMENTOS', self.fmt_titulo)
        worksheet.set_row(0, 30)
        
        # Cabeçalhos
        headers = ['Data', 'Tipo', 'Objetivo', 'Valor', 'Rent. Mensal %']
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.fmt_header)
        
        # Dados
        invest_ordenados = self.cf.investimentos.sort_values('data', ascending=False)
        
        for idx, (_, row_data) in enumerate(invest_ordenados.iterrows(), start=3):
            worksheet.write_datetime(idx, 0, row_data['data'], self.fmt_data)
            worksheet.write(idx, 1, row_data['tipo'], self.fmt_normal)
            worksheet.write(idx, 2, row_data.get('objetivo', 'Geral'), self.fmt_normal)
            worksheet.write(idx, 3, row_data['valor'], self.fmt_moeda_amarelo)
            worksheet.write(idx, 4, (row_data['rentabilidade_mensal'] or 0) / 100, self.fmt_percent)
        
        # Total investido
        total_row = len(invest_ordenados) + 3
        worksheet.write(total_row, 2, 'TOTAL INVESTIDO', self.fmt_header)
        worksheet.write(total_row, 3, f'=SUM(D4:D{total_row})', self.fmt_total)
    
    def _criar_aba_cartao(self, writer, workbook):
        """Cria aba de controle de cartão de crédito"""
        if len(self.cf.cartao) == 0:
            return
        
        worksheet = workbook.add_worksheet('Cartão de Crédito')
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 35)
        worksheet.set_column('C:D', 15)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 18)
        worksheet.set_column('H:H', 10)
        
        # Título
        worksheet.merge_range('A1:H1', 'CARTÃO DE CRÉDITO', self.fmt_titulo)
        worksheet.set_row(0, 30)
        
        # Cabeçalhos
        headers = ['Data Compra', 'Descrição', 'Valor', 'Parcelas', 'Parcela', 'Vencimento', 'Cartão', 'Pago?']
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.fmt_header)
        
        # Garantir coluna pago
        if 'pago' not in self.cf.cartao.columns:
            self.cf.cartao['pago'] = False
        
        # Dados
        cartao_ordenado = self.cf.cartao.sort_values('vencimento_fatura')
        
        for idx, (_, row_data) in enumerate(cartao_ordenado.iterrows(), start=3):
            worksheet.write_datetime(idx, 0, row_data['data_compra'], self.fmt_data)
            worksheet.write(idx, 1, row_data['descricao'], self.fmt_normal)
            worksheet.write(idx, 2, row_data['valor'], self.fmt_moeda)
            worksheet.write(idx, 3, row_data['parcelas'], self.fmt_centro)
            worksheet.write(idx, 4, f"{row_data['parcela_atual']}/{row_data['parcelas']}", self.fmt_centro)
            worksheet.write_datetime(idx, 5, row_data['vencimento_fatura'], self.fmt_data)
            worksheet.write(idx, 6, row_data.get('cartao', 'Cartão'), self.fmt_normal)
            
            pago_text = 'SIM' if row_data['pago'] else 'NÃO'
            fmt = self.fmt_moeda_verde if row_data['pago'] else self.fmt_moeda_vermelho
            worksheet.write(idx, 7, pago_text, fmt)
        
        # Total a pagar
        total_row = len(cartao_ordenado) + 3
        worksheet.write(total_row, 1, 'TOTAL EM ABERTO', self.fmt_header)
        worksheet.write_formula(total_row, 2, 
                               f'=SUMIF(H4:H{total_row},"NÃO",C4:C{total_row})',
                               self.fmt_total)
        
        worksheet.autofilter(2, 0, total_row, 7)
    
    def _criar_aba_orcamento(self, writer, workbook):
        """Cria aba de orçamento vs realizado"""
        worksheet = workbook.add_worksheet('Orçamento')
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:E', 15)
        
        # Título
        worksheet.merge_range('A1:E1', 'ORÇAMENTO VS REALIZADO', self.fmt_titulo)
        worksheet.set_row(0, 30)
        
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        
        # Cabeçalhos
        headers = ['Categoria', 'Orçado', 'Realizado', 'Diferença', '% Usado']
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.fmt_header)
        
        # Gastos do mês atual por categoria
        mask_mes = (self.cf.gastos['data'].dt.month == mes_atual) & (self.cf.gastos['data'].dt.year == ano_atual) if len(self.cf.gastos) > 0 else pd.Series(dtype=bool)
        gastos_cat = self.cf.gastos[mask_mes].groupby('categoria')['valor'].sum() if len(self.cf.gastos) > 0 else pd.Series(dtype='float64')
        
        row = 3
        for _, orc_row in self.cf.orcamento.iterrows():
            categoria = orc_row['categoria']
            orcado = orc_row['limite_mensal']
            realizado = gastos_cat.get(categoria, 0)
            diferenca = orcado - realizado
            percentual = (realizado / orcado) if orcado > 0 else 0
            
            worksheet.write(row, 0, categoria, self.fmt_normal)
            worksheet.write(row, 1, orcado, self.fmt_moeda)
            worksheet.write(row, 2, realizado, self.fmt_moeda)
            
            # Diferença com cor
            fmt_dif = self.fmt_moeda_verde if diferenca >= 0 else self.fmt_moeda_vermelho
            worksheet.write(row, 3, diferenca, fmt_dif)
            
            # Percentual com cor
            if percentual >= 0.9:
                fmt_perc = self.fmt_moeda_vermelho
            elif percentual >= 0.7:
                fmt_perc = self.fmt_moeda_amarelo
            else:
                fmt_perc = self.fmt_percent
            worksheet.write(row, 4, percentual, fmt_perc)
            
            row += 1
        
        # Totais
        worksheet.write(row, 0, 'TOTAL', self.fmt_header)
        worksheet.write(row, 1, f'=SUM(B4:B{row})', self.fmt_total)
        worksheet.write(row, 2, f'=SUM(C4:C{row})', self.fmt_total)
        worksheet.write(row, 3, f'=SUM(D4:D{row})', self.fmt_total)
        
        # Gráfico de comparação
        chart = workbook.add_chart({'type': 'column'})
        chart.add_series({
            'name': 'Orçado',
            'categories': f'=Orçamento!$A$4:$A${row}',
            'values': f'=Orçamento!$B$4:$B${row}',
            'fill': {'color': '#85C1E9'}
        })
        chart.add_series({
            'name': 'Realizado',
            'categories': f'=Orçamento!$A$4:$A${row}',
            'values': f'=Orçamento!$C$4:$C${row}',
            'fill': {'color': '#EC7063'}
        })
        chart.set_title({'name': 'Orçamento vs Realizado'})
        chart.set_x_axis({'name': 'Categoria'})
        chart.set_y_axis({'name': 'Valor (R$)'})
        chart.set_size({'width': 720, 'height': 400})
        worksheet.insert_chart('G3', chart)
    
    def _criar_aba_analise_categorias(self, writer, workbook):
        """Cria aba com análise detalhada por categoria"""
        if len(self.cf.gastos) == 0:
            return
        
        worksheet = workbook.add_worksheet('Análise Categorias')
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:F', 15)
        
        # Título
        worksheet.merge_range('A1:F1', 'ANÁLISE POR CATEGORIA', self.fmt_titulo)
        worksheet.set_row(0, 30)
        
        ano = datetime.now().year
        
        # Cabeçalhos
        headers = ['Categoria', 'Total Ano', 'Média Mensal', 'Maior Gasto', 'Menor Gasto', '% do Total']
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, self.fmt_header)
        
        # Filtrar gastos do ano
        mask_ano = self.cf.gastos['data'].dt.year == ano
        gastos_ano = self.cf.gastos[mask_ano]
        
        # Análise por categoria
        total_geral = gastos_ano['valor'].sum()
        
        row = 3
        for categoria in gastos_ano['categoria'].unique():
            cat_gastos = gastos_ano[gastos_ano['categoria'] == categoria]['valor']
            
            total = cat_gastos.sum()
            media = cat_gastos.mean()
            maior = cat_gastos.max()
            menor = cat_gastos.min()
            percentual = total / total_geral if total_geral > 0 else 0
            
            worksheet.write(row, 0, categoria, self.fmt_normal)
            worksheet.write(row, 1, total, self.fmt_moeda)
            worksheet.write(row, 2, media, self.fmt_moeda)
            worksheet.write(row, 3, maior, self.fmt_moeda)
            worksheet.write(row, 4, menor, self.fmt_moeda)
            worksheet.write(row, 5, percentual, self.fmt_percent)
            
            row += 1
        
        # Total
        worksheet.write(row, 0, 'TOTAL', self.fmt_header)
        worksheet.write(row, 1, f'=SUM(B4:B{row})', self.fmt_total)


def exportar_para_excel(controle_financeiro, nome_arquivo=None):
    """Função auxiliar para exportar dados para Excel"""
    exportador = ExportadorExcel(controle_financeiro)
    return exportador.criar_planilha_completa(nome_arquivo)


# ================= IMPORTAÇÃO DO EXCEL =================

def importar_de_excel(controle_financeiro, nome_arquivo, preferir_excel=True):
    """Importa dados de um arquivo Excel gerado/editado.

    preferir_excel=True: Excel é a fonte principal (sobrescreve dados existentes).
    preferir_excel=False: somente adiciona novos registros (não altera existentes).
    """
    caminho = Path(nome_arquivo)
    if not caminho.exists():
        alt = controle_financeiro.pasta_dados / nome_arquivo
        if alt.exists():
            caminho = alt
        else:
            raise FileNotFoundError(f"Arquivo Excel não encontrado: {nome_arquivo}")

    # Backup simples dos CSVs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = controle_financeiro.pasta_dados / f"backup_import_{timestamp}"
    backup_dir.mkdir(exist_ok=True)
    for src in [controle_financeiro.arquivo_gastos, controle_financeiro.arquivo_receitas,
                controle_financeiro.arquivo_investimentos, controle_financeiro.arquivo_cartao,
                controle_financeiro.arquivo_orcamento]:
        if src.exists():
            dst = backup_dir / src.name
            dst.write_bytes(src.read_bytes())

    print(f"📦 Backup criado em {backup_dir}")

    xls = pd.ExcelFile(caminho)

    def merge_or_replace(existing_df, new_df, subset_keys):
        if preferir_excel:
            return new_df.reset_index(drop=True)
        # append uniques
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=subset_keys, keep='last')
        return combined.reset_index(drop=True)

    # Gastos
    if 'Gastos' in xls.sheet_names:
        gastos = pd.read_excel(xls, 'Gastos', skiprows=2)
        gastos = gastos.dropna(subset=['Data', 'Categoria', 'Descrição', 'Valor'])
        gastos = gastos.rename(columns={'Data': 'data', 'Categoria': 'categoria', 'Descrição': 'descricao',
                                        'Valor': 'valor', 'Forma Pgto': 'forma_pagamento'})
        gastos['data'] = pd.to_datetime(gastos['data'])
        controle_financeiro.gastos = merge_or_replace(controle_financeiro.gastos, gastos,
                                                      ['data', 'descricao', 'valor', 'categoria'])

    # Receitas
    if 'Receitas' in xls.sheet_names:
        receitas = pd.read_excel(xls, 'Receitas', skiprows=2)
        receitas = receitas.dropna(subset=['Data', 'Fonte', 'Valor'])
        receitas = receitas.rename(columns={'Data': 'data', 'Fonte': 'fonte', 'Tipo': 'tipo', 'Valor': 'valor'})
        receitas['data'] = pd.to_datetime(receitas['data'])
        controle_financeiro.receitas = merge_or_replace(controle_financeiro.receitas, receitas,
                                                        ['data', 'fonte', 'valor', 'tipo'])

    # Investimentos
    if 'Investimentos' in xls.sheet_names:
        inv = pd.read_excel(xls, 'Investimentos', skiprows=2)
        inv = inv.dropna(subset=['Data', 'Tipo', 'Valor'])
        inv = inv.rename(columns={'Data': 'data', 'Tipo': 'tipo', 'Objetivo': 'objetivo',
                                  'Valor': 'valor', 'Rent. Mensal %': 'rentabilidade_mensal'})
        inv['data'] = pd.to_datetime(inv['data'])
        inv['objetivo'] = inv['objetivo'].fillna('Geral')
        inv['rentabilidade_mensal'] = (inv['rentabilidade_mensal'].fillna(0) * 100).astype(float)
        controle_financeiro.investimentos = merge_or_replace(controle_financeiro.investimentos, inv,
                                                             ['data', 'tipo', 'objetivo', 'valor'])

    # Cartão
    if 'Cartão de Crédito' in xls.sheet_names:
        cartao = pd.read_excel(xls, 'Cartão de Crédito', skiprows=2)
        cartao = cartao.dropna(subset=['Data Compra', 'Descrição', 'Valor'])
        cartao = cartao.rename(columns={'Data Compra': 'data_compra', 'Descrição': 'descricao',
                                        'Valor': 'valor', 'Parcelas': 'parcelas', 'Parcela': 'parcela_str',
                                        'Vencimento': 'vencimento_fatura', 'Pago?': 'pago'})
        cartao['data_compra'] = pd.to_datetime(cartao['data_compra'])
        cartao['vencimento_fatura'] = pd.to_datetime(cartao['vencimento_fatura'])
        # Extrair parcela_atual de texto "1/3"
        cartao['parcela_atual'] = cartao['parcela_str'].astype(str).str.split('/').str[0].astype(int)
        cartao['parcelas'] = cartao['parcelas'].fillna(cartao['parcela_str'].astype(str).str.split('/').str[-1]).astype(int)
        cartao['pago'] = cartao['pago'].astype(str).str.upper().str.strip().isin(['SIM', 'TRUE', 'VERDADEIRO'])
        cartao = cartao[['data_compra', 'descricao', 'valor', 'parcelas', 'parcela_atual', 'vencimento_fatura', 'pago']]
        controle_financeiro.cartao = merge_or_replace(controle_financeiro.cartao, cartao,
                                                      ['data_compra', 'descricao', 'valor', 'parcela_atual'])

    # Orçamento
    if 'Orçamento' in xls.sheet_names:
        orc = pd.read_excel(xls, 'Orçamento', skiprows=2)
        orc = orc.dropna(subset=['Categoria', 'Orçado'])
        orc = orc.rename(columns={'Categoria': 'categoria', 'Orçado': 'limite_mensal'})
        controle_financeiro.orcamento = orc[['categoria', 'limite_mensal']].reset_index(drop=True)

    # Salvar nos CSVs
    controle_financeiro.salvar_dados()
    print("✅ Importação concluída e dados salvos.")
