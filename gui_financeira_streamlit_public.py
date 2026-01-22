"""
GUI web (Streamlit) multiusuário simples.
Cada usuário digita seu nome e cria sua própria base (arquivos separados).
Execute localmente ou publique (Streamlit Community Cloud ou similar):
    streamlit run gui_financeira_streamlit_public.py
"""

import re
from datetime import date
import pandas as pd
import streamlit as st
from planilha_financeira import ControleFinanceiro

st.set_page_config(page_title="Controle Financeiro - Público", page_icon="💳", layout="centered")
st.title("💳 Controle Financeiro (multiusuário simples)")
st.caption("Cada pessoa digita um identificador e salva em arquivos separados. O orçamento é só do cartão.")

# Helpers

def slugify(nome: str) -> str:
    nome = nome.strip().lower()
    nome = re.sub(r"[^a-z0-9_-]+", "_", nome)
    return nome or "usuario"

def get_cf(user_slug: str) -> ControleFinanceiro:
    # Usa arquivo_base com o slug para separar dados por usuário
    if "cf" not in st.session_state or st.session_state.get("user_slug") != user_slug:
        st.session_state["user_slug"] = user_slug
        st.session_state["cf"] = ControleFinanceiro(arquivo_base=f"{user_slug}")
    return st.session_state["cf"]

def orcamento_atual(cf: ControleFinanceiro) -> float:
    mask = cf.orcamento['categoria'] == 'Cartão de Crédito'
    if mask.any():
        return float(cf.orcamento.loc[mask, 'limite_mensal'].iloc[0])
    return 1500.0

def checar_estouro_cartao(cf: ControleFinanceiro, limite: float):
    """Retorna dict {mes: total} para faturas que excedem o limite."""
    if len(cf.cartao) == 0:
        return {}
    df = cf.cartao.copy()
    if 'vencimento_fatura' in df:
        df['vencimento_fatura'] = pd.to_datetime(df['vencimento_fatura'])
    df['mes'] = df['vencimento_fatura'].dt.to_period('M')
    soma = df.groupby('mes')['valor'].sum()
    return {str(m): v for m, v in soma.items() if v > limite}

# Login simples por identificador
st.subheader("Identifique-se")
user_input = st.text_input("Digite um identificador (ex: seu_nome)", value="")
iniciar = st.button("Começar")

if iniciar:
    if not user_input.strip():
        st.error("Digite um identificador para separar seus dados.")
    else:
        user_slug = slugify(user_input)
        cf = get_cf(user_slug)
        st.success(f"Sessão iniciada para: {user_slug}")
else:
    if "cf" in st.session_state:
        cf = st.session_state["cf"]
        user_slug = st.session_state.get("user_slug", "usuario")
    else:
        st.info("Digite seu identificador e clique em Começar.")
        st.stop()

# Orçamento do cartão
st.markdown("---")
st.subheader("Orçamento do cartão de crédito")
limite_atual = orcamento_atual(cf)
novo_limite = st.number_input("Limite mensal (R$)", min_value=0.0, step=50.0, value=limite_atual, format="%.2f")
if st.button("Salvar limite"):
    try:
        cf.atualizar_orcamento('Cartão de Crédito', novo_limite)
        cf.salvar_dados()
        st.success(f"Limite salvo: R$ {novo_limite:.2f}")
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

st.markdown("---")

# Receitas
with st.form("form_receita"):
    st.subheader("Receitas")
    r_data = st.date_input("Data", value=date.today())
    r_desc = st.text_input("Descrição")
    r_valor = st.number_input("Valor (R$)", min_value=0.0, step=50.0)
    r_tipo = st.selectbox("Tipo", ["Salário", "Freelance", "Investimento", "Outros"])
    submit = st.form_submit_button("Adicionar receita")
    if submit:
        try:
            cf.adicionar_receita(r_data.isoformat(), r_desc, float(r_valor), r_tipo)
            cf.salvar_dados()
            st.success("Receita adicionada e salva!")
        except Exception as e:
            st.error(f"Erro: {e}")

# Gastos
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
            cf.adicionar_gasto(g_data.isoformat(), g_cat, g_desc, float(g_valor), g_pg)
            cf.salvar_dados()
            st.success("Gasto adicionado e salvo!")
        except Exception as e:
            st.error(f"Erro: {e}")

# Investimentos
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
            cf.adicionar_investimento(i_data.isoformat(), i_tipo, float(i_valor), float(i_rent), i_obj)
            cf.salvar_dados()
            st.success("Investimento adicionado e salvo!")
        except Exception as e:
            st.error(f"Erro: {e}")

# Cartão
with st.form("form_cartao"):
    st.subheader("Cartão de crédito")
    c_data = st.date_input("Data", value=date.today(), key="c_data")
    c_desc = st.text_input("Descrição", key="c_desc")
    c_valor = st.number_input("Valor total (R$)", min_value=0.0, step=50.0, key="c_valor")
    c_parc = st.number_input("Número de parcelas", min_value=1, step=1, value=1, key="c_parc")
    submit_c = st.form_submit_button("Adicionar compra")
    if submit_c:
        try:
            cf.adicionar_compra_cartao(c_data.isoformat(), c_desc, float(c_valor), int(c_parc))
            cf.salvar_dados()
            limite = orcamento_atual(cf)
            estouros = checar_estouro_cartao(cf, limite)
            if estouros:
                msgs = [f"{mes}: R$ {valor:.2f}" for mes, valor in estouros.items()]
                st.error("⚠️ Limite do cartão estourado em: " + "; ".join(msgs))
            else:
                st.success("Compra adicionada e salva! Dentro do limite do cartão.")
        except Exception as e:
            st.error(f"Erro: {e}")

# Visualizar e editar dados
st.markdown("---")
st.subheader("Visualizar e Editar Dados")
tab_view = st.selectbox("Escolha o que visualizar:", ["Gastos", "Receitas", "Investimentos", "Cartão"])

if tab_view == "Gastos":
    st.write("**Seus Gastos:**")
    if len(cf.gastos) > 0:
        st.dataframe(cf.gastos, use_container_width=True)
        idx_deletar = st.number_input("Número da linha para deletar (0 é a primeira):", min_value=0, max_value=len(cf.gastos)-1, step=1)
        if st.button("Deletar gasto"):
            cf.gastos = cf.gastos.drop(idx_deletar).reset_index(drop=True)
            cf.salvar_dados()
            st.success("Gasto deletado!")
            st.rerun()
    else:
        st.info("Nenhum gasto registrado ainda.")

elif tab_view == "Receitas":
    st.write("**Suas Receitas:**")
    if len(cf.receitas) > 0:
        st.dataframe(cf.receitas, use_container_width=True)
        idx_deletar = st.number_input("Número da linha para deletar (0 é a primeira):", min_value=0, max_value=len(cf.receitas)-1, step=1)
        if st.button("Deletar receita"):
            cf.receitas = cf.receitas.drop(idx_deletar).reset_index(drop=True)
            cf.salvar_dados()
            st.success("Receita deletada!")
            st.rerun()
    else:
        st.info("Nenhuma receita registrada ainda.")

elif tab_view == "Investimentos":
    st.write("**Seus Investimentos:**")
    if len(cf.investimentos) > 0:
        st.dataframe(cf.investimentos, use_container_width=True)
        idx_deletar = st.number_input("Número da linha para deletar (0 é a primeira):", min_value=0, max_value=len(cf.investimentos)-1, step=1)
        if st.button("Deletar investimento"):
            cf.investimentos = cf.investimentos.drop(idx_deletar).reset_index(drop=True)
            cf.salvar_dados()
            st.success("Investimento deletado!")
            st.rerun()
    else:
        st.info("Nenhum investimento registrado ainda.")

elif tab_view == "Cartão":
    st.write("**Suas Compras no Cartão:**")
    if len(cf.cartao) > 0:
        st.dataframe(cf.cartao, use_container_width=True)
        idx_deletar = st.number_input("Número da linha para deletar (0 é a primeira):", min_value=0, max_value=len(cf.cartao)-1, step=1)
        if st.button("Deletar compra"):
            cf.cartao = cf.cartao.drop(idx_deletar).reset_index(drop=True)
            cf.salvar_dados()
            st.success("Compra deletada!")
            st.rerun()
    else:
        st.info("Nenhuma compra no cartão registrada ainda.")

st.markdown("---")
if st.button("📊 Gerar Excel"):
    try:
        caminho = cf.exportar_para_excel()
        st.success("Excel gerado com sucesso!")
        
        # Ler o arquivo para download
        with open(caminho, "rb") as file:
            excel_data = file.read()
        
        # Botão de download
        st.download_button(
            label="⬇️ Baixar Excel",
            data=excel_data,
            file_name=f"controle_financeiro_{user_slug}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Erro ao gerar: {e}")

st.caption("Dica: cada usuário fica em arquivos separados com base no identificador. Orçamento: apenas cartão.")
