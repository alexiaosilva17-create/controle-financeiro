"""
GUI web (Streamlit) multiusu

ario completo com dashboard e graficos.
Cada usuario digita seu nome e cria sua propria base (arquivos separados).
Execute localmente ou publique (Streamlit Community Cloud ou similar):
    streamlit run gui_financeira_streamlit_public.py
"""

import re
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from planilha_financeira import ControleFinanceiro

st.set_page_config(page_title="Controle Financeiro", page_icon="💳", layout="wide")

# Helpers
def slugify(nome: str) -> str:
    nome = nome.strip().lower()
    nome = re.sub(r"[^a-z0-9_-]+", "_", nome)
    return nome or "usuario"

def gerar_meses_disponiveis():
    """Gera lista de meses: 12 meses atras ate 12 meses a frente"""
    hoje = datetime.now()
    meses = []
    for i in range(-12, 13):
        mes_data = hoje + relativedelta(months=i)
        mes_nome = mes_data.strftime('%B/%Y').capitalize()
        traducao = {
            'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Marco',
            'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
            'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
            'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
        }
        for ing, pt in traducao.items():
            mes_nome = mes_nome.replace(ing, pt)
        meses.append((mes_nome, mes_data.strftime('%Y-%m-01')))
    return meses

def get_cf(user_slug: str) -> ControleFinanceiro:
    if "cf" not in st.session_state or st.session_state.get("user_slug") != user_slug:
        st.session_state["user_slug"] = user_slug
        st.session_state["cf"] = ControleFinanceiro(arquivo_base=f"{user_slug}")
    return st.session_state["cf"]

def iso(d):
    return d.isoformat() if hasattr(d, "isoformat") else str(d)

# Login
st.title("💳 Controle Financeiro")

with st.sidebar:
    st.subheader("Identifique-se")
    user_input = st.text_input("Seu identificador", value="")
    iniciar = st.button("Comecar")
    
    if iniciar:
        if not user_input.strip():
            st.error("Digite um identificador.")
        else:
            user_slug = slugify(user_input)
            cf = get_cf(user_slug)
            st.success(f"Sessao: {user_slug}")
    else:
        if "cf" in st.session_state:
            cf = st.session_state["cf"]
            user_slug = st.session_state.get("user_slug", "usuario")
            st.info(f"Usuario: {user_slug}")
        else:
            st.info("Digite seu identificador.")
            st.stop()
    
    st.markdown("---")
    menu = st.selectbox("Menu", ["📊 Dashboard", "➕ Adicionar Dados", "📋 Visualizar e Editar", "💳 Faturas"])
    st.markdown("---")
    st.caption("💡 Sistema financeiro completo")

# Dashboard
if menu == "📊 Dashboard":
    st.header("Dashboard Financeiro")
    
    col1, col2, col3, col4 = st.columns(4)
    total_receitas = cf.receitas['valor'].sum() if len(cf.receitas) > 0 else 0
    total_gastos = cf.gastos['valor'].sum() if len(cf.gastos) > 0 else 0
    total_cartao = cf.cartao['valor'].sum() if len(cf.cartao) > 0 else 0
    total_investido = cf.investimentos['valor'].sum() if len(cf.investimentos) > 0 else 0
    
    col1.metric("Receitas", f"R$ {total_receitas:,.2f}")
    col2.metric("Gastos", f"R$ {total_gastos:,.2f}")
    col3.metric("Cartao", f"R$ {total_cartao:,.2f}")
    col4.metric("Investido", f"R$ {total_investido:,.2f}")
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    saldo = total_receitas - total_gastos - total_cartao
    col1.metric("Saldo", f"R$ {saldo:,.2f}", delta="Positivo" if saldo >= 0 else "Negativo")
    
    if len(cf.investimentos) > 0:
        rendimentos = cf.calcular_rendimentos()
        valor_atual_inv = rendimentos['valor_atual'].sum()
        rendimento_total = rendimentos['rendimento_acumulado'].sum()
        col2.metric("Valor Atual Investimentos", f"R$ {valor_atual_inv:,.2f}")
        col3.metric("Rendimento Acumulado", f"R$ {rendimento_total:,.2f}",
                   delta=f"{(rendimento_total/total_investido*100):.1f}%" if total_investido > 0 else "0%")
    
    st.markdown("---")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Gastos por Categoria")
        if len(cf.gastos) > 0:
            gastos_cat = cf.gastos.groupby('categoria')['valor'].sum().reset_index()
            fig = px.pie(gastos_cat, values='valor', names='categoria', title="Distribuicao de Gastos")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum gasto registrado.")
    
    with col_right:
        st.subheader("Investimentos por Objetivo")
        if len(cf.investimentos) > 0:
            inv_obj = cf.investimentos.groupby('objetivo')['valor'].sum().reset_index()
            fig = px.pie(inv_obj, values='valor', names='objetivo', title="Distribuicao de Investimentos")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum investimento registrado.")
    
    st.markdown("---")
    st.subheader("Faturas Pendentes")
    if len(cf.cartao) > 0:
        df_pendentes = cf.cartao[cf.cartao['pago'] == False].copy()
        if len(df_pendentes) > 0:
            df_pendentes['vencimento_fatura'] = pd.to_datetime(df_pendentes['vencimento_fatura'])
            if 'mes_fatura' not in df_pendentes.columns:
                df_pendentes['mes_fatura'] = df_pendentes['vencimento_fatura'].dt.strftime('%Y-%m')
            pendentes_grupo = df_pendentes.groupby(['mes_fatura', 'cartao'])['valor'].sum().reset_index()
            pendentes_grupo.columns = ['Mes da Fatura', 'Cartao', 'Valor Total']
            pendentes_grupo['Valor Total'] = pendentes_grupo['Valor Total'].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(pendentes_grupo, use_container_width=True)
        else:
            st.success("Todas as faturas estao pagas!")
    else:
        st.info("Nenhuma compra no cartao registrada.")

# Adicionar Dados
elif menu == "➕ Adicionar Dados":
    st.header("Adicionar Novos Registros")
    
    with st.form("form_receita"):
        st.subheader("Receitas")
        r_data = st.date_input("Data", value=date.today())
        r_desc = st.text_input("Descricao")
        r_valor = st.number_input("Valor (R$)", min_value=0.0, step=50.0)
        r_tipo = st.selectbox("Tipo", ["Salario", "Freelance", "Investimento", "Outros"])
        submit = st.form_submit_button("Adicionar receita")
        if submit:
            try:
                cf.adicionar_receita(iso(r_data), r_desc, float(r_valor), r_tipo)
                cf.salvar_dados()
                st.success("Receita adicionada!")
            except Exception as e:
                st.error(f"Erro: {e}")
    
    with st.form("form_gasto"):
        st.subheader("Gastos")
        g_data = st.date_input("Data", value=date.today(), key="g_data")
        g_cat = st.selectbox("Categoria", ["Alimentacao", "Transporte", "Moradia", "Saude", "Lazer", "Outros"], key="g_cat")
        g_desc = st.text_input("Descricao", key="g_desc")
        g_valor = st.number_input("Valor (R$)", min_value=0.0, step=20.0, key="g_valor")
        g_pg = st.selectbox("Pagamento", ["Debito", "Credito", "PIX", "Dinheiro"], key="g_pg")
        submit_g = st.form_submit_button("Adicionar gasto")
        if submit_g:
            try:
                cf.adicionar_gasto(iso(g_data), g_cat, g_desc, float(g_valor), g_pg)
                cf.salvar_dados()
                st.success("Gasto adicionado!")
            except Exception as e:
                st.error(f"Erro: {e}")
    
    with st.form("form_inv"):
        st.subheader("Investimentos")
        i_data = st.date_input("Data", value=date.today(), key="i_data")
        i_tipo = st.selectbox("Tipo", ["Tesouro Selic", "CDB", "ETF", "Acoes", "Poupanca", "Outros"], key="i_tipo")
        i_valor = st.number_input("Valor (R$)", min_value=0.0, step=50.0, key="i_valor")
        i_rent = st.number_input("Rentabilidade mensal (%)", min_value=0.0, step=0.1, value=0.7, key="i_rent")
        i_obj = st.selectbox("Objetivo", ["Emergencia", "Casa", "Viagem", "Geral"], key="i_obj")
        submit_i = st.form_submit_button("Adicionar investimento")
        if submit_i:
            try:
                cf.adicionar_investimento(iso(i_data), i_tipo, float(i_valor), float(i_rent), i_obj)
                cf.salvar_dados()
                st.success("Investimento adicionado!")
            except Exception as e:
                st.error(f"Erro: {e}")
    
    st.markdown("---")
    st.subheader("Cartoes de Credito")
    col_a, col_b = st.columns(2)
    cartao_nome = col_a.text_input("Nome do cartao")
    venc_dia = col_b.number_input("Dia vencimento", min_value=1, max_value=31, value=10, step=1)
    if st.button("Salvar cartao"):
        if cartao_nome.strip():
            cf.definir_cartao(cartao_nome.strip(), venc_dia)
            cf.salvar_dados()
            st.success("Cartao salvo!")
        else:
            st.error("Informe o nome.")
    
    cartoes_disponiveis = list(cf.cartoes['cartao'].unique()) if hasattr(cf, 'cartoes') and len(cf.cartoes) > 0 else []
    
    with st.form("form_cartao"):
        st.subheader("Compra no Cartao")
        c_data = st.date_input("Data da compra", value=date.today(), key="c_data")
        c_cartao = st.selectbox("Cartao", cartoes_disponiveis if cartoes_disponiveis else ["Cadastre um cartao"], key="c_cartao")
        c_venc = st.number_input("Vencimento (dia)", min_value=1, max_value=31, value=venc_dia, step=1, key="c_venc")
        
        meses_opcoes = gerar_meses_disponiveis()
        meses_labels = [m[0] for m in meses_opcoes]
        c_mes_fatura_label = st.selectbox("Mes da fatura", meses_labels, index=12, key="c_mes_fatura")
        idx_selecionado = meses_labels.index(c_mes_fatura_label)
        c_mes_fatura_data = meses_opcoes[idx_selecionado][1]
        
        c_desc = st.text_input("Descricao", key="c_desc")
        c_valor = st.number_input("Valor (R$)", min_value=0.0, step=50.0, key="c_valor")
        c_parc = st.number_input("Parcelas", min_value=1, step=1, value=1, key="c_parc")
        submit_c = st.form_submit_button("Adicionar compra")
        if submit_c:
            if cartoes_disponiveis:
                try:
                    cf.adicionar_compra_cartao(iso(c_data), c_desc, float(c_valor), int(c_parc), cartao=c_cartao, vencimento_dia=c_venc, mes_fatura_ref=c_mes_fatura_data)
                    cf.salvar_dados()
                    st.success("Compra adicionada!")
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("Cadastre um cartao primeiro.")

# Visualizar e Editar
elif menu == "📋 Visualizar e Editar":
    st.header("Visualizar e Editar")
    tab = st.selectbox("Escolha:", ["Gastos", "Receitas", "Investimentos", "Cartao"])
    
    if tab == "Gastos":
        if len(cf.gastos) > 0:
            st.dataframe(cf.gastos, use_container_width=True)
            idx = st.number_input("Linha para deletar:", min_value=0, max_value=len(cf.gastos)-1, step=1)
            if st.button("Deletar"):
                cf.gastos = cf.gastos.drop(idx).reset_index(drop=True)
                cf.salvar_dados()
                st.success("Deletado!")
                st.rerun()
        else:
            st.info("Nenhum gasto.")
    
    elif tab == "Receitas":
        if len(cf.receitas) > 0:
            st.dataframe(cf.receitas, use_container_width=True)
            idx = st.number_input("Linha para deletar:", min_value=0, max_value=len(cf.receitas)-1, step=1)
            if st.button("Deletar"):
                cf.receitas = cf.receitas.drop(idx).reset_index(drop=True)
                cf.salvar_dados()
                st.success("Deletado!")
                st.rerun()
        else:
            st.info("Nenhuma receita.")
    
    elif tab == "Investimentos":
        if len(cf.investimentos) > 0:
            st.dataframe(cf.investimentos, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Rendimentos")
            rendimentos = cf.calcular_rendimentos()
            if len(rendimentos) > 0:
                st.dataframe(rendimentos[['data', 'tipo', 'valor', 'valor_atual', 'rendimento_acumulado']].round(2), use_container_width=True)
                
                total_investido = rendimentos['valor'].sum()
                total_atual = rendimentos['valor_atual'].sum()
                total_rendimento = rendimentos['rendimento_acumulado'].sum()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Investido", f"R$ {total_investido:,.2f}")
                col2.metric("Valor Atual", f"R$ {total_atual:,.2f}")
                col3.metric("Rendimento", f"R$ {total_rendimento:,.2f}")
            
            st.markdown("---")
            idx = st.number_input("Linha para deletar:", min_value=0, max_value=len(cf.investimentos)-1, step=1)
            if st.button("Deletar"):
                cf.investimentos = cf.investimentos.drop(idx).reset_index(drop=True)
                cf.salvar_dados()
                st.success("Deletado!")
                st.rerun()
        else:
            st.info("Nenhum investimento.")
    
    elif tab == "Cartao":
        if len(cf.cartao) > 0:
            st.dataframe(cf.cartao, use_container_width=True)
            idx = st.number_input("Linha:", min_value=0, max_value=len(cf.cartao)-1, step=1)
            pago = st.checkbox("Pago?", value=True)
            
            col1, col2 = st.columns(2)
            if col1.button("Atualizar Status"):
                cf.cartao.loc[idx, 'pago'] = pago
                cf.salvar_dados()
                st.success("Atualizado!")
                st.rerun()
            if col2.button("Deletar"):
                cf.cartao = cf.cartao.drop(idx).reset_index(drop=True)
                cf.salvar_dados()
                st.success("Deletado!")
                st.rerun()
        else:
            st.info("Nenhuma compra.")

# Faturas
elif menu == "💳 Faturas":
    st.header("Faturas do Cartao")
    
    if len(cf.cartao) > 0:
        df_cartao = cf.cartao.copy()
        df_cartao['vencimento_fatura'] = pd.to_datetime(df_cartao['vencimento_fatura'])
        if 'mes_fatura' not in df_cartao.columns:
            df_cartao['mes_fatura'] = df_cartao['vencimento_fatura'].dt.strftime('%Y-%m')
        
        col1, col2 = st.columns(2)
        cartoes_lista = list(df_cartao['cartao'].unique()) if 'cartao' in df_cartao.columns else []
        filtro_cartao = col1.selectbox("Filtrar cartao:", ["Todos"] + cartoes_lista)
        meses_lista = sorted(df_cartao['mes_fatura'].unique())
        filtro_mes = col2.selectbox("Filtrar mes:", ["Todos"] + meses_lista)
        
        df_filtrado = df_cartao.copy()
        if filtro_cartao != "Todos":
            df_filtrado = df_filtrado[df_filtrado['cartao'] == filtro_cartao]
        if filtro_mes != "Todos":
            df_filtrado = df_filtrado[df_filtrado['mes_fatura'] == filtro_mes]
        
        st.markdown("---")
        st.subheader("Resumo")
        resumo = df_filtrado.groupby(['mes_fatura', 'cartao', 'pago'])['valor'].sum().reset_index()
        resumo_pivot = resumo.pivot_table(index=['mes_fatura', 'cartao'], columns='pago', values='valor', fill_value=0).reset_index()
        
        if True in resumo_pivot.columns:
            resumo_pivot.rename(columns={True: 'Pago'}, inplace=True)
        else:
            resumo_pivot['Pago'] = 0.0
            
        if False in resumo_pivot.columns:
            resumo_pivot.rename(columns={False: 'Nao Pago'}, inplace=True)
        else:
            resumo_pivot['Nao Pago'] = 0.0
        
        resumo_pivot['Total'] = resumo_pivot['Pago'] + resumo_pivot['Nao Pago']
        st.dataframe(resumo_pivot, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Detalhes")
        st.dataframe(df_filtrado, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Evolucao")
        faturas_mes = df_filtrado.groupby('mes_fatura')['valor'].sum().reset_index()
        fig = px.bar(faturas_mes, x='mes_fatura', y='valor', title='Total por Mes')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma compra no cartao.")

st.sidebar.markdown("---")
st.sidebar.caption("Dados salvos localmente")
