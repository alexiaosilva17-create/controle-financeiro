"""
GUI web com Streamlit para adicionar dados financeiros
Execute com: streamlit run gui_financeira_streamlit.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from planilha_financeira import ControleFinanceiro

# Manter instância única na sessão
if "cf" not in st.session_state:
    st.session_state.cf = ControleFinanceiro()
cf = st.session_state.cf

def iso(d):
    return d.isoformat() if hasattr(d, "isoformat") else str(d)

st.set_page_config(page_title="Controle Financeiro", page_icon="💰", layout="wide")
st.title("💰 Controle Financeiro")

# Menu lateral
menu = st.sidebar.selectbox(
    "Menu",
    ["📊 Dashboard", "➕ Adicionar Dados", "📋 Visualizar e Editar", "💳 Faturas do Cartão", "📈 Excel"]
)

st.sidebar.markdown("---")
st.sidebar.caption("💡 Sistema completo de controle financeiro")

# ========== DASHBOARD ==========
if menu == "📊 Dashboard":
    st.header("Dashboard Financeiro")
    
    # Métricas principais
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Calcular dados do mês atual
    mes_atual = datetime.now().strftime('%Y-%m')
    
    total_receitas = cf.receitas['valor'].sum() if len(cf.receitas) > 0 else 0
    total_gastos = cf.gastos['valor'].sum() if len(cf.gastos) > 0 else 0
    total_investido = cf.investimentos['valor'].sum() if len(cf.investimentos) > 0 else 0
    
    # Fatura do cartão (mês atual e total)
    if len(cf.cartao) > 0:
        df_cartao = cf.cartao.copy()
        if 'mes_fatura' not in df_cartao.columns:
            df_cartao['vencimento_fatura'] = pd.to_datetime(df_cartao['vencimento_fatura'])
            df_cartao['mes_fatura'] = df_cartao['vencimento_fatura'].dt.strftime('%Y-%m')
        total_cartao_mes = df_cartao[df_cartao['mes_fatura'] == mes_atual]['valor'].sum()
        total_cartao_todos = df_cartao['valor'].sum()
    else:
        total_cartao_mes = 0
        total_cartao_todos = 0
    
    col1.metric("💵 Receitas", f"R$ {total_receitas:,.2f}")
    col2.metric("💸 Gastos", f"R$ {total_gastos:,.2f}")
    col3.metric("💳 Cartão (Mês)", f"R$ {total_cartao_mes:,.2f}")
    col4.metric("💳 Cartão (Total)", f"R$ {total_cartao_todos:,.2f}")
    col5.metric("📈 Investido", f"R$ {total_investido:,.2f}")
    
    # Saldo do mês atual
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    saldo_mes_atual = total_receitas - total_gastos - total_cartao_mes
    col1.metric("💰 Saldo do Mês Atual", f"R$ {saldo_mes_atual:,.2f}", 
                delta=f"{'Positivo' if saldo_mes_atual >= 0 else 'Negativo'}")
    
    # Rendimentos
    if len(cf.investimentos) > 0:
        rendimentos = cf.calcular_rendimentos()
        valor_atual_inv = rendimentos['valor_atual'].sum()
        rendimento_total = rendimentos['rendimento_acumulado'].sum()
        col2.metric("💎 Valor Atual Investimentos", f"R$ {valor_atual_inv:,.2f}")
        col3.metric("✨ Rendimento Acumulado", f"R$ {rendimento_total:,.2f}",
                   delta=f"{(rendimento_total/total_investido*100):.1f}%" if total_investido > 0 else "0%")
    
    st.markdown("---")
    
    # Gráficos
    col_left, col_right = st.columns(2)
    
    # Gráfico de gastos por categoria
    with col_left:
        st.subheader("📊 Gastos por Categoria")
        if len(cf.gastos) > 0:
            gastos_cat = cf.gastos.groupby('categoria')['valor'].sum().reset_index()
            fig = px.pie(gastos_cat, values='valor', names='categoria', 
                        title="Distribuição de Gastos")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum gasto registrado ainda.")
    
    # Gráfico de investimentos por objetivo
    with col_right:
        st.subheader("🎯 Investimentos por Objetivo")
        if len(cf.investimentos) > 0:
            inv_obj = cf.investimentos.groupby('objetivo')['valor'].sum().reset_index()
            fig = px.pie(inv_obj, values='valor', names='objetivo',
                        title="Distribuição de Investimentos")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum investimento registrado ainda.")
    
    # Evolução mensal
    st.markdown("---")
    st.subheader("📈 Evolução Mensal")
    
    if len(cf.receitas) > 0 or len(cf.gastos) > 0:
        # Preparar dados
        df_rec = cf.receitas.copy() if len(cf.receitas) > 0 else pd.DataFrame()
        df_gas = cf.gastos.copy() if len(cf.gastos) > 0 else pd.DataFrame()
        
        if len(df_rec) > 0:
            df_rec['data'] = pd.to_datetime(df_rec['data'])
            df_rec['mes'] = df_rec['data'].dt.to_period('M').astype(str)
            rec_mes = df_rec.groupby('mes')['valor'].sum()
        else:
            rec_mes = pd.Series(dtype=float)
        
        if len(df_gas) > 0:
            df_gas['data'] = pd.to_datetime(df_gas['data'])
            df_gas['mes'] = df_gas['data'].dt.to_period('M').astype(str)
            gas_mes = df_gas.groupby('mes')['valor'].sum()
        else:
            gas_mes = pd.Series(dtype=float)
        
        # Cartão de crédito por mês
        if len(cf.cartao) > 0:
            df_cartao = cf.cartao.copy()
            df_cartao['vencimento_fatura'] = pd.to_datetime(df_cartao['vencimento_fatura'])
            if 'mes_fatura' not in df_cartao.columns:
                df_cartao['mes_fatura'] = df_cartao['vencimento_fatura'].dt.strftime('%Y-%m')
            cart_mes = df_cartao.groupby('mes_fatura')['valor'].sum()
            cart_mes.index.name = 'mes'
        else:
            cart_mes = pd.Series(dtype=float)
        
        # Combinar
        df_evo = pd.DataFrame({
            'Receitas': rec_mes,
            'Gastos': gas_mes,
            'Cartão': cart_mes
        }).fillna(0).reset_index()
        df_evo.columns = ['Mês', 'Receitas', 'Gastos', 'Cartão']
        
        # Criar coluna "Gastos + Cartão" para visualização
        df_evo['Gastos + Cartão'] = df_evo['Gastos'] + df_evo['Cartão']
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_evo['Mês'], y=df_evo['Receitas'], name='Receitas', marker_color='green'))
        fig.add_trace(go.Bar(x=df_evo['Mês'], y=df_evo['Gastos + Cartão'], name='Gastos + Cartão', marker_color='red'))
        fig.update_layout(barmode='group', title='Receitas vs Gastos + Cartão de Crédito por Mês')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Adicione receitas ou gastos para ver a evolução mensal.")
    
    # Faturas pendentes
    st.markdown("---")
    st.subheader("⚠️ Faturas Pendentes (Não Pagas)")
    if len(cf.cartao) > 0:
        df_pendentes = cf.cartao[cf.cartao['pago'] == False].copy()
        if len(df_pendentes) > 0:
            df_pendentes['vencimento_fatura'] = pd.to_datetime(df_pendentes['vencimento_fatura'])
            # Criar coluna mes_fatura se não existir
            if 'mes_fatura' not in df_pendentes.columns:
                df_pendentes['mes_fatura'] = df_pendentes['vencimento_fatura'].dt.strftime('%Y-%m')
            pendentes_grupo = df_pendentes.groupby(['mes_fatura', 'cartao'])['valor'].sum().reset_index()
            pendentes_grupo.columns = ['Mês da Fatura', 'Cartão', 'Valor Total']
            pendentes_grupo['Valor Total'] = pendentes_grupo['Valor Total'].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(pendentes_grupo, use_container_width=True)
        else:
            st.success("✅ Todas as faturas estão pagas!")
    else:
        st.info("Nenhuma compra no cartão registrada ainda.")

# ========== ADICIONAR DADOS ==========
elif menu == "➕ Adicionar Dados":
    st.header("Adicionar Novos Registros")
    
    with st.form("form_receita"):
        st.subheader("Receitas")
        r_data = st.date_input("Data", value=date.today())
        r_desc = st.text_input("Descrição")
        r_valor = st.number_input("Valor (R$)", min_value=0.0, step=50.0)
        r_tipo = st.selectbox("Tipo", ["Salário", "Freelance", "Investimento", "Outros"])
        submit = st.form_submit_button("Adicionar receita")
        if submit:
            try:
                cf.adicionar_receita(iso(r_data), r_desc, float(r_valor), r_tipo)
                cf.salvar_dados()
                st.success("Receita adicionada e salva!")
            except Exception as e:
                st.error(f"Erro: {e}")

    with st.form("form_gasto"):
        st.subheader("Gastos")
        g_data = st.date_input("Data", value=date.today(), key="g_data")
        g_cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Saúde", "Lazer", "Serviços", "Educação", "Pet", "Outros"], key="g_cat")
        g_desc = st.text_input("Descrição", key="g_desc")
        g_valor = st.number_input("Valor (R$)", min_value=0.0, step=20.0, key="g_valor")
        g_pg = st.selectbox("Forma de pagamento", ["Débito", "Crédito", "PIX", "Dinheiro"], key="g_pg")
        submit_g = st.form_submit_button("Adicionar gasto")
        if submit_g:
            try:
                cf.adicionar_gasto(iso(g_data), g_cat, g_desc, float(g_valor), g_pg)
                cf.salvar_dados()
                st.success("Gasto adicionado e salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")

    with st.form("form_inv"):
        st.subheader("Investimentos")
        i_data = st.date_input("Data", value=date.today(), key="i_data")
        i_tipo = st.selectbox("Tipo", ["Tesouro Selic", "CDB", "ETF", "Ações", "Poupança", "Outros"], key="i_tipo")
        i_valor = st.number_input("Valor (R$)", min_value=0.0, step=50.0, key="i_valor")
        i_rent = st.number_input("Rentabilidade mensal (%)", min_value=0.0, step=0.1, value=0.7, key="i_rent")
        i_obj = st.selectbox("Objetivo", ["Emergência", "Casa", "Viagem", "Geral"], key="i_obj")
        submit_i = st.form_submit_button("Adicionar investimento")
        if submit_i:
            try:
                cf.adicionar_investimento(iso(i_data), i_tipo, float(i_valor), float(i_rent), i_obj)
                cf.salvar_dados()
                st.success("Investimento adicionado e salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")

    # Configurar cartões
    st.markdown("---")
    st.subheader("Cartões de crédito")
    col_a, col_b = st.columns(2)
    cartao_nome = col_a.text_input("Nome do cartão", value="Cartão Principal")
    venc_dia = col_b.number_input("Dia de vencimento", min_value=1, max_value=31, value=10, step=1)
    if st.button("Salvar cartão"):
        try:
            cf.definir_cartao(cartao_nome, venc_dia)
            cf.salvar_dados()
            st.success("Cartão salvo/atualizado!")
        except Exception as e:
            st.error(f"Erro: {e}")

    cartoes_disponiveis = list(cf.cartoes['cartao'].unique()) if hasattr(cf, 'cartoes') else ["Cartão Principal"]

    def gerar_meses_disponiveis():
        """Gera lista de meses: 12 meses atrás até 12 meses à frente"""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        hoje = datetime.now()
        meses = []
        
        for i in range(-12, 13):  # -12 até +12 meses
            mes_data = hoje + relativedelta(months=i)
            mes_nome = mes_data.strftime('%B/%Y').capitalize()
            # Traduzir nomes dos meses
            traducao = {
                'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
                'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
                'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
                'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
            }
            for ing, pt in traducao.items():
                mes_nome = mes_nome.replace(ing, pt)
            meses.append((mes_nome, mes_data.strftime('%Y-%m-01')))
        
        return meses

    with st.form("form_cartao"):
        st.subheader("Cartão de crédito")
        c_data = st.date_input("Data da compra", value=date.today(), key="c_data")
        c_cartao = st.selectbox("Qual cartão?", cartoes_disponiveis, key="c_cartao")
        c_venc = st.number_input("Vencimento deste cartão (dia)", min_value=1, max_value=31, value=venc_dia, step=1, key="c_venc")
        
        # Gerar opções de meses dinamicamente
        meses_opcoes = gerar_meses_disponiveis()
        meses_labels = [m[0] for m in meses_opcoes]
        mes_atual_idx = 12  # Índice do mês atual (0-12 são passados, 12 é atual, 13-24 são futuros)
        
        c_mes_fatura_label = st.selectbox("Mês da fatura", meses_labels, index=mes_atual_idx, key="c_mes_fatura", 
                                          help="Escolha o mês em que esta compra vai entrar na fatura")
        
        # Converter label selecionado para data
        idx_selecionado = meses_labels.index(c_mes_fatura_label)
        c_mes_fatura_data = meses_opcoes[idx_selecionado][1]
        
        c_desc = st.text_input("Descrição", key="c_desc")
        c_valor = st.number_input("Valor total (R$)", min_value=0.0, step=50.0, key="c_valor")
        c_parc = st.number_input("Número de parcelas", min_value=1, step=1, value=1, key="c_parc")
        submit_c = st.form_submit_button("Adicionar compra")
        if submit_c:
            try:
                cf.adicionar_compra_cartao(iso(c_data), c_desc, float(c_valor), int(c_parc), cartao=c_cartao, vencimento_dia=c_venc, mes_fatura_ref=c_mes_fatura_data)
                cf.salvar_dados()
                st.success("Compra adicionada e salva!")
            except Exception as e:
                st.error(f"Erro: {e}")

# ========== VISUALIZAR E EDITAR ==========
elif menu == "📋 Visualizar e Editar":
    st.header("Visualizar e Editar Dados")
    tab_view = st.selectbox("Escolha o que visualizar:", ["Gastos", "Receitas", "Investimentos", "Cartão"])
    
    if tab_view == "Gastos":
        st.subheader("**Seus Gastos:**")
        if len(cf.gastos) > 0:
            st.dataframe(cf.gastos, use_container_width=True)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✏️ Editar Gasto")
                idx_editar = st.number_input("Linha para editar:", min_value=0, max_value=len(cf.gastos)-1, step=1, key="edit_gasto_idx")
                
                # Preencher com dados atuais
                gasto_atual = cf.gastos.iloc[idx_editar]
                nova_data = st.date_input("Nova data:", value=pd.to_datetime(gasto_atual['data']).date(), key="edit_g_data")
                nova_cat = st.selectbox("Nova categoria:", ["Alimentação", "Transporte", "Moradia", "Saúde", "Lazer", "Serviços", "Educação", "Pet", "Outros"], 
                                       index=["Alimentação", "Transporte", "Moradia", "Saúde", "Lazer", "Serviços", "Educação", "Pet", "Outros"].index(gasto_atual['categoria']) if gasto_atual['categoria'] in ["Alimentação", "Transporte", "Moradia", "Saúde", "Lazer", "Serviços", "Educação", "Pet", "Outros"] else 0,
                                       key="edit_g_cat")
                nova_desc = st.text_input("Nova descrição:", value=gasto_atual['descricao'], key="edit_g_desc")
                novo_valor = st.number_input("Novo valor:", min_value=0.0, value=float(gasto_atual['valor']), step=10.0, key="edit_g_valor")
                nova_pg = st.selectbox("Nova forma de pagamento:", ["Débito", "Crédito", "PIX", "Dinheiro"],
                                      index=["Débito", "Crédito", "PIX", "Dinheiro"].index(gasto_atual['forma_pagamento']) if gasto_atual['forma_pagamento'] in ["Débito", "Crédito", "PIX", "Dinheiro"] else 0,
                                      key="edit_g_pg")
                
                if st.button("💾 Salvar Edição", key="save_edit_gasto"):
                    cf.gastos.loc[idx_editar, 'data'] = iso(nova_data)
                    cf.gastos.loc[idx_editar, 'categoria'] = nova_cat
                    cf.gastos.loc[idx_editar, 'descricao'] = nova_desc
                    cf.gastos.loc[idx_editar, 'valor'] = novo_valor
                    cf.gastos.loc[idx_editar, 'forma_pagamento'] = nova_pg
                    cf.salvar_dados()
                    st.success("Gasto editado com sucesso!")
                    st.rerun()
            
            with col2:
                st.markdown("### 🗑️ Deletar Gasto")
                idx_deletar = st.number_input("Linha para deletar:", min_value=0, max_value=len(cf.gastos)-1, step=1, key="del_gasto_idx")
                if st.button("❌ Deletar", key="del_gasto"):
                    cf.gastos = cf.gastos.drop(idx_deletar).reset_index(drop=True)
                    cf.salvar_dados()
                    st.success("Gasto deletado!")
                    st.rerun()
        else:
            st.info("Nenhum gasto registrado ainda.")
    
    elif tab_view == "Receitas":
        st.subheader("**Suas Receitas:**")
        if len(cf.receitas) > 0:
            st.dataframe(cf.receitas, use_container_width=True)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✏️ Editar Receita")
                idx_editar = st.number_input("Linha para editar:", min_value=0, max_value=len(cf.receitas)-1, step=1, key="edit_rec_idx")
                
                receita_atual = cf.receitas.iloc[idx_editar]
                nova_data = st.date_input("Nova data:", value=pd.to_datetime(receita_atual['data']).date(), key="edit_r_data")
                nova_fonte = st.text_input("Nova fonte:", value=receita_atual['fonte'], key="edit_r_fonte")
                novo_valor = st.number_input("Novo valor:", min_value=0.0, value=float(receita_atual['valor']), step=50.0, key="edit_r_valor")
                novo_tipo = st.selectbox("Novo tipo:", ["Salário", "Freelance", "Investimento", "Outros"],
                                        index=["Salário", "Freelance", "Investimento", "Outros"].index(receita_atual['tipo']) if receita_atual['tipo'] in ["Salário", "Freelance", "Investimento", "Outros"] else 0,
                                        key="edit_r_tipo")
                
                if st.button("💾 Salvar Edição", key="save_edit_receita"):
                    cf.receitas.loc[idx_editar, 'data'] = iso(nova_data)
                    cf.receitas.loc[idx_editar, 'fonte'] = nova_fonte
                    cf.receitas.loc[idx_editar, 'valor'] = novo_valor
                    cf.receitas.loc[idx_editar, 'tipo'] = novo_tipo
                    cf.salvar_dados()
                    st.success("Receita editada com sucesso!")
                    st.rerun()
            
            with col2:
                st.markdown("### 🗑️ Deletar Receita")
                idx_deletar = st.number_input("Linha para deletar:", min_value=0, max_value=len(cf.receitas)-1, step=1, key="del_rec_idx")
                if st.button("❌ Deletar", key="del_receita"):
                    cf.receitas = cf.receitas.drop(idx_deletar).reset_index(drop=True)
                    cf.salvar_dados()
                    st.success("Receita deletada!")
                    st.rerun()
        else:
            st.info("Nenhuma receita registrada ainda.")
    
    elif tab_view == "Investimentos":
        st.subheader("**Seus Investimentos:**")
        if len(cf.investimentos) > 0:
            st.dataframe(cf.investimentos, use_container_width=True)
            
            # Calcular e mostrar rendimentos
            st.markdown("---")
            st.subheader("💰 Rendimentos Acumulados")
            rendimentos = cf.calcular_rendimentos()
            if len(rendimentos) > 0:
                cols_mostrar = ['data', 'tipo', 'objetivo', 'valor', 'rentabilidade_mensal', 
                               'meses_decorridos', 'valor_atual', 'rendimento_acumulado']
                st.dataframe(rendimentos[cols_mostrar].round(2), use_container_width=True)
                
                total_investido = rendimentos['valor'].sum()
                total_atual = rendimentos['valor_atual'].sum()
                total_rendimento = rendimentos['rendimento_acumulado'].sum()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Investido", f"R$ {total_investido:,.2f}")
                col2.metric("Valor Atual", f"R$ {total_atual:,.2f}")
                col3.metric("Rendimento Total", f"R$ {total_rendimento:,.2f}", 
                           delta=f"{(total_rendimento/total_investido*100):.1f}%" if total_investido > 0 else "0%")
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✏️ Editar Investimento")
                idx_editar = st.number_input("Linha para editar:", min_value=0, max_value=len(cf.investimentos)-1, step=1, key="edit_inv_idx")
                
                inv_atual = cf.investimentos.iloc[idx_editar]
                nova_data = st.date_input("Nova data:", value=pd.to_datetime(inv_atual['data']).date(), key="edit_i_data")
                novo_tipo = st.selectbox("Novo tipo:", ["Tesouro Selic", "CDB", "ETF", "Ações", "Poupança", "Outros"],
                                        index=["Tesouro Selic", "CDB", "ETF", "Ações", "Poupança", "Outros"].index(inv_atual['tipo']) if inv_atual['tipo'] in ["Tesouro Selic", "CDB", "ETF", "Ações", "Poupança", "Outros"] else 0,
                                        key="edit_i_tipo")
                novo_valor = st.number_input("Novo valor:", min_value=0.0, value=float(inv_atual['valor']), step=50.0, key="edit_i_valor")
                nova_rent = st.number_input("Nova rentabilidade mensal (%):", min_value=0.0, value=float(inv_atual['rentabilidade_mensal']), step=0.1, key="edit_i_rent")
                novo_obj = st.selectbox("Novo objetivo:", ["Emergência", "Casa", "Viagem", "Geral"],
                                       index=["Emergência", "Casa", "Viagem", "Geral"].index(inv_atual['objetivo']) if inv_atual['objetivo'] in ["Emergência", "Casa", "Viagem", "Geral"] else 0,
                                       key="edit_i_obj")
                
                if st.button("💾 Salvar Edição", key="save_edit_inv"):
                    cf.investimentos.loc[idx_editar, 'data'] = iso(nova_data)
                    cf.investimentos.loc[idx_editar, 'tipo'] = novo_tipo
                    cf.investimentos.loc[idx_editar, 'valor'] = novo_valor
                    cf.investimentos.loc[idx_editar, 'rentabilidade_mensal'] = nova_rent
                    cf.investimentos.loc[idx_editar, 'objetivo'] = novo_obj
                    cf.salvar_dados()
                    st.success("Investimento editado com sucesso!")
                    st.rerun()
            
            with col2:
                st.markdown("### 🗑️ Deletar Investimento")
                idx_deletar = st.number_input("Linha para deletar:", min_value=0, max_value=len(cf.investimentos)-1, step=1, key="del_inv_idx")
                if st.button("❌ Deletar", key="del_inv"):
                    cf.investimentos = cf.investimentos.drop(idx_deletar).reset_index(drop=True)
                    cf.salvar_dados()
                    st.success("Investimento deletado!")
                    st.rerun()
        else:
            st.info("Nenhum investimento registrado ainda.")
    
    elif tab_view == "Cartão":
        st.subheader("**Suas Compras no Cartão:**")
        if len(cf.cartao) > 0:
            st.dataframe(cf.cartao, use_container_width=True)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✔️ Marcar Pago/Não Pago")
                idx_pago = st.number_input("Linha:", min_value=0, max_value=len(cf.cartao)-1, step=1, key="pago_idx")
                pago_flag = st.checkbox("Marcar como pago?", value=True, key="pago_flag")
                
                if st.button("💾 Atualizar Status", key="update_pago"):
                    cf.cartao.loc[idx_pago, 'pago'] = pago_flag
                    cf.salvar_dados()
                    st.success("Status atualizado!")
                    st.rerun()
                
                st.markdown("### 📅 Marcar Fatura Inteira")
                if st.button("✔️ Marcar Fatura do Mês", key="mark_fatura"):
                    data_venc = pd.to_datetime(cf.cartao.loc[idx_pago, 'vencimento_fatura'])
                    cartao_sel = cf.cartao.loc[idx_pago, 'cartao'] if 'cartao' in cf.cartao.columns else None
                    cf.marcar_fatura_paga(data_venc.month, data_venc.year, cartao=cartao_sel, pago=pago_flag)
                    cf.salvar_dados()
                    st.success("Fatura marcada!")
                    st.rerun()
            
            with col2:
                st.markdown("### 🗑️ Deletar Compra")
                idx_deletar = st.number_input("Linha para deletar:", min_value=0, max_value=len(cf.cartao)-1, step=1, key="del_cartao_idx")
                if st.button("❌ Deletar", key="del_cartao"):
                    cf.cartao = cf.cartao.drop(idx_deletar).reset_index(drop=True)
                    cf.salvar_dados()
                    st.success("Compra deletada!")
                    st.rerun()
        else:
            st.info("Nenhuma compra no cartão registrada ainda.")

# ========== FATURAS DO CARTÃO ==========
elif menu == "💳 Faturas do Cartão":
    st.header("Faturas do Cartão de Crédito")
    
    if len(cf.cartao) > 0:
        df_cartao = cf.cartao.copy()
        df_cartao['vencimento_fatura'] = pd.to_datetime(df_cartao['vencimento_fatura'])
        
        # Criar coluna mes_fatura se não existir
        if 'mes_fatura' not in df_cartao.columns:
            df_cartao['mes_fatura'] = df_cartao['vencimento_fatura'].dt.strftime('%Y-%m')
        
        # Filtros
        col1, col2 = st.columns(2)
        
        cartoes_lista = list(df_cartao['cartao'].unique()) if 'cartao' in df_cartao.columns else ["Todos"]
        filtro_cartao = col1.selectbox("Filtrar por cartão:", ["Todos"] + cartoes_lista)
        
        meses_lista = sorted(df_cartao['mes_fatura'].unique())
        filtro_mes = col2.selectbox("Filtrar por mês da fatura:", ["Todos"] + meses_lista)
        
        # Aplicar filtros
        df_filtrado = df_cartao.copy()
        if filtro_cartao != "Todos":
            df_filtrado = df_filtrado[df_filtrado['cartao'] == filtro_cartao]
        if filtro_mes != "Todos":
            df_filtrado = df_filtrado[df_filtrado['mes_fatura'] == filtro_mes]
        
        st.markdown("---")
        
        # Resumo por mês e cartão
        st.subheader("📊 Resumo de Faturas")
        resumo = df_filtrado.groupby(['mes_fatura', 'cartao', 'pago'])['valor'].sum().reset_index()
        resumo_pivot = resumo.pivot_table(index=['mes_fatura', 'cartao'], columns='pago', values='valor', fill_value=0).reset_index()
        
        # Garantir que as colunas de pago existam
        if True in resumo_pivot.columns:
            resumo_pivot.rename(columns={True: 'Pago'}, inplace=True)
        else:
            resumo_pivot['Pago'] = 0.0
            
        if False in resumo_pivot.columns:
            resumo_pivot.rename(columns={False: 'Não Pago'}, inplace=True)
        else:
            resumo_pivot['Não Pago'] = 0.0
        
        resumo_pivot['Total'] = resumo_pivot['Pago'] + resumo_pivot['Não Pago']
        resumo_pivot = resumo_pivot[['mes_fatura', 'cartao', 'Pago', 'Não Pago', 'Total']]
        resumo_pivot.columns = ['Mês da Fatura', 'Cartão', 'Pago (R$)', 'Não Pago (R$)', 'Total (R$)']
        
        st.dataframe(resumo_pivot.style.format({
            'Pago (R$)': 'R$ {:,.2f}',
            'Não Pago (R$)': 'R$ {:,.2f}',
            'Total (R$)': 'R$ {:,.2f}'
        }), use_container_width=True)
        
        # Detalhes
        st.markdown("---")
        st.subheader("📝 Detalhes das Compras")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Gráfico
        st.markdown("---")
        st.subheader("📈 Evolução das Faturas")
        faturas_mes = df_filtrado.groupby('mes_fatura')['valor'].sum().reset_index()
        fig = px.bar(faturas_mes, x='mes_fatura', y='valor', 
                    title='Total por Mês da Fatura',
                    labels={'mes_fatura': 'Mês da Fatura', 'valor': 'Valor (R$)'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma compra no cartão registrada ainda.")

# ========== EXCEL ==========
elif menu == "📈 Excel":
    st.header("Exportar para Excel")
    st.write("Clique no botão abaixo para gerar/atualizar o arquivo Excel com todos os seus dados financeiros.")
    
    if st.button("📊 Gerar/Atualizar Excel", use_container_width=True):
        try:
            caminho = cf.exportar_para_excel()
            st.success(f"✅ Excel criado/atualizado: {caminho}")
        except Exception as e:
            st.error(f"❌ Erro ao gerar: {e}")
    
    st.markdown("---")
    st.info("💡 O arquivo Excel contém todas as suas receitas, gastos, investimentos e compras de cartão organizadas em abas separadas.")

st.sidebar.markdown("---")
st.sidebar.caption("📁 Dados salvos em: dados_financeiros/")
