"""
GUI web (Streamlit) multiusuario simples.
Cada usuario digita seu nome e cria sua propria base (arquivos separados).
Execute localmente ou publique (Streamlit Community Cloud ou similar):
    streamlit run gui_financeira_streamlit_public.py
"""

import re
from datetime import date
import pandas as pd
import streamlit as st
from planilha_financeira import ControleFinanceiro

st.set_page_config(page_title="Controle Financeiro - Publico", page_icon="💳", layout="centered")
st.title("💳 Controle Financeiro (multiusuario simples)")
st.caption("Cada pessoa digita um identificador e salva em arquivos separados. Orcamento: apenas cartao.")

# Helpers

def slugify(nome: str) -> str:
    nome = nome.strip().lower()
    nome = re.sub(r"[^a-z0-9_-]+", "_", nome)
    return nome or "usuario"

def get_cf(user_slug: str) -> ControleFinanceiro:
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
    if len(cf.cartao) == 0:
        return {}
    df = cf.cartao.copy()
    if 'vencimento_fatura' in df:
        df['vencimento_fatura'] = pd.to_datetime(df['vencimento_fatura'])
    df['mes'] = df['vencimento_fatura'].dt.to_period('M')
    soma = df.groupby('mes')['valor'].sum()
    return {str(m): v for m, v in soma.items() if v > limite}

def vencimento_padrao(cf: ControleFinanceiro, cartao_nome: str, fallback: int = 10) -> int:
    if hasattr(cf, 'cartoes') and len(cf.cartoes) > 0:
        match = cf.cartoes[cf.cartoes['cartao'] == cartao_nome]
        if len(match) > 0 and 'vencimento_dia' in match:
            return int(match['vencimento_dia'].iloc[0])
    return fallback

def iso(d):
    return d.isoformat() if hasattr(d, "isoformat") else str(d)

# Login simples por identificador
st.subheader("Identifique-se")
user_input = st.text_input("Digite um identificador (ex: seu_nome)", value="")
iniciar = st.button("Comecar")

if iniciar:
    if not user_input.strip():
        st.error("Digite um identificador para separar seus dados.")
    else:
        user_slug = slugify(user_input)
        cf = get_cf(user_slug)
        st.success(f"Sessao iniciada para: {user_slug}")
else:
    if "cf" in st.session_state:
        cf = st.session_state["cf"]
        user_slug = st.session_state.get("user_slug", "usuario")
    else:
        st.info("Digite seu identificador e clique em Comecar.")
        st.stop()

# Orcamento do cartao
st.markdown("---")
st.subheader("Orcamento do cartao de credito")
limite_atual = orcamento_atual(cf)
novo_limite = st.number_input("Limite mensal (R$)", min_value=0.0, step=50.0, value=limite_atual, format="%.2f")
if st.button("Salvar limite"):
    try:
        cf.atualizar_orcamento('Cartao de Credito', novo_limite)
        cf.salvar_dados()
        st.success(f"Limite salvo: R$ {novo_limite:.2f}")
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

st.markdown("---")

# Receitas
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
            st.success("Receita adicionada e salva!")
        except Exception as e:
            st.error(f"Erro: {e}")

# Gastos
with st.form("form_gasto"):
    st.subheader("Gastos")
    g_data = st.date_input("Data", value=date.today(), key="g_data")
    g_cat = st.selectbox("Categoria", ["Alimentacao", "Transporte", "Moradia", "Saude", "Lazer", "Servicos", "Educacao", "Pet", "Outros"], key="g_cat")
    g_desc = st.text_input("Descricao", key="g_desc")
    g_valor = st.number_input("Valor (R$)", min_value=0.0, step=20.0, key="g_valor")
    g_pg = st.selectbox("Forma de pagamento", ["Debito", "Credito", "PIX", "Dinheiro"], key="g_pg")
    submit_g = st.form_submit_button("Adicionar gasto")
    if submit_g:
        try:
            cf.adicionar_gasto(iso(g_data), g_cat, g_desc, float(g_valor), g_pg)
            cf.salvar_dados()
            st.success("Gasto adicionado e salvo!")
        except Exception as e:
            st.error(f"Erro: {e}")

# Investimentos
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
            st.success("Investimento adicionado e salvo!")
        except Exception as e:
            st.error(f"Erro: {e}")

# Cartoes (cadastro, remocao e compras)
st.markdown("---")
st.subheader("Cartoes de credito")
col_a, col_b = st.columns(2)
cartao_nome = col_a.text_input("Nome do cartao", value="")
venc_dia = col_b.number_input("Dia de vencimento", min_value=1, max_value=31, value=10, step=1)
if st.button("Salvar cartao"):
    if not cartao_nome.strip():
        st.error("Informe um nome para o cartao.")
    else:
        try:
            cf.definir_cartao(cartao_nome.strip(), venc_dia)
            cf.salvar_dados()
            st.success("Cartao salvo/atualizado!")
        except Exception as e:
            st.error(f"Erro: {e}")

cartoes_disponiveis = list(cf.cartoes['cartao'].unique()) if hasattr(cf, 'cartoes') and len(cf.cartoes) > 0 else []
if cartoes_disponiveis:
    cartao_remover = st.selectbox("Remover cartao (tambem remove compras dele)", cartoes_disponiveis, key="remover_cartao")
    if st.button("Deletar cartao selecionado"):
        try:
            cf.cartoes = cf.cartoes[cf.cartoes['cartao'] != cartao_remover].reset_index(drop=True)
            if len(cf.cartao) > 0 and 'cartao' in cf.cartao.columns:
                cf.cartao = cf.cartao[cf.cartao['cartao'] != cartao_remover].reset_index(drop=True)
            cf.salvar_dados()
            st.success("Cartao e compras associadas removidos.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")
else:
    st.info("Nenhum cartao cadastrado ainda. Cadastre um acima.")

with st.form("form_cartao"):
    st.subheader("Compra no cartao")
    c_data = st.date_input("Data", value=date.today(), key="c_data")
    c_cartao = st.selectbox("Qual cartao?", cartoes_disponiveis if cartoes_disponiveis else ["Cadastre um cartao acima"], key="c_cartao")
    valor_venc = vencimento_padrao(cf, c_cartao, fallback=venc_dia)
    c_venc = st.number_input("Vencimento deste cartao (dia)", min_value=1, max_value=31, value=valor_venc, step=1, key="c_venc")
    c_desc = st.text_input("Descricao", key="c_desc")
    c_valor = st.number_input("Valor total (R$)", min_value=0.0, step=50.0, key="c_valor")
    c_parc = st.number_input("Numero de parcelas", min_value=1, step=1, value=1, key="c_parc")
    submit_c = st.form_submit_button("Adicionar compra")
    if submit_c:
        if not cartoes_disponiveis:
            st.error("Cadastre um cartao antes de lancar compras.")
        else:
            try:
                cf.adicionar_compra_cartao(iso(c_data), c_desc, float(c_valor), int(c_parc), cartao=c_cartao, vencimento_dia=int(c_venc))
                cf.salvar_dados()
                limite = orcamento_atual(cf)
                estouros = checar_estouro_cartao(cf, limite)
                if estouros:
                    msgs = [f"{mes}: R$ {valor:.2f}" for mes, valor in estouros.items()]
                    st.error("⚠️ Limite do cartao estourado em: " + "; ".join(msgs))
                else:
                    st.success("Compra adicionada e salva! Dentro do limite do cartao.")
            except Exception as e:
                st.error(f"Erro: {e}")

# Visualizar e editar dados
st.markdown("---")
st.subheader("Visualizar e Editar Dados")
tab_view = st.selectbox("Escolha o que visualizar:", ["Gastos", "Receitas", "Investimentos", "Cartao"])

if tab_view == "Gastos":
    st.write("**Seus Gastos:**")
    if len(cf.gastos) > 0:
        st.dataframe(cf.gastos, use_container_width=True)
        idx_deletar = st.number_input("Numero da linha para deletar (0 e a primeira):", min_value=0, max_value=len(cf.gastos)-1, step=1)
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
        idx_deletar = st.number_input("Numero da linha para deletar (0 e a primeira):", min_value=0, max_value=len(cf.receitas)-1, step=1)
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
        idx_deletar = st.number_input("Numero da linha para deletar (0 e a primeira):", min_value=0, max_value=len(cf.investimentos)-1, step=1)
        if st.button("Deletar investimento"):
            cf.investimentos = cf.investimentos.drop(idx_deletar).reset_index(drop=True)
            cf.salvar_dados()
            st.success("Investimento deletado!")
            st.rerun()
    else:
        st.info("Nenhum investimento registrado ainda.")

elif tab_view == "Cartao":
    st.write("**Suas Compras no Cartao:**")
    if len(cf.cartao) > 0:
        st.dataframe(cf.cartao, use_container_width=True)
        idx_deletar = st.number_input("Numero da linha para deletar (0 e a primeira):", min_value=0, max_value=len(cf.cartao)-1, step=1)
        pago_flag = st.checkbox("Marcar como pago?", value=True)
        col1, col2, col3 = st.columns(3)
        if col1.button("Deletar compra"):
            cf.cartao = cf.cartao.drop(idx_deletar).reset_index(drop=True)
            cf.salvar_dados()
            st.success("Compra deletada!")
            st.rerun()
        if col2.button("Atualizar pago/nao pago"):
            cf.cartao.loc[idx_deletar, 'pago'] = pago_flag
            cf.salvar_dados()
            st.success("Status atualizado!")
            st.rerun()
        if col3.button("Marcar fatura do mes como paga"):
            data_venc = pd.to_datetime(cf.cartao.loc[idx_deletar, 'vencimento_fatura'])
            cartao_sel = cf.cartao.loc[idx_deletar, 'cartao'] if 'cartao' in cf.cartao.columns else None
            cf.marcar_fatura_paga(data_venc.month, data_venc.year, cartao=cartao_sel, pago=pago_flag)
            cf.salvar_dados()
            st.success("Fatura marcada!")
            st.rerun()
    else:
        st.info("Nenhuma compra no cartao registrada ainda.")

st.markdown("---")
if st.button("📊 Gerar Excel"):
    try:
        caminho = cf.exportar_para_excel()
        st.success("Excel gerado com sucesso!")

        with open(caminho, "rb") as file:
            excel_data = file.read()

        st.download_button(
            label="⬇️ Baixar Excel",
            data=excel_data,
            file_name=f"controle_financeiro_{user_slug}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Erro ao gerar: {e}")

st.caption("Dica: cada usuario fica em arquivos separados com base no identificador. Orcamento: apenas cartao.")
