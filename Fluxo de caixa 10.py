import streamlit as st
import pandas as pd
import altair as alt
import os

st.set_page_config(page_title="Fluxo de Caixa CFO", layout="wide")

ARQUIVO = "fluxo_caixa.csv"

# =====================================================
# FUNÇÃO PARA CRIAR BASE
# =====================================================

def criar_base():

    colunas = [
        "data_lancamento",
        "data_vencimento",
        "tipo",
        "categoria",
        "subcategoria",
        "descricao",
        "valor",
        "status"
    ]

    if not os.path.exists(ARQUIVO):

        df_base = pd.DataFrame(columns=colunas)
        df_base.to_csv(ARQUIVO, index=False)

# =====================================================
# CARREGAR BASE
# =====================================================

def carregar_dados():

    try:
        df = pd.read_csv(ARQUIVO)
    except:
        df = pd.DataFrame()

    colunas = [
        "data_lancamento",
        "data_vencimento",
        "tipo",
        "categoria",
        "subcategoria",
        "descricao",
        "valor",
        "status"
    ]

    for c in colunas:
        if c not in df.columns:
            df[c] = None

    df = df[colunas]

    df["data_lancamento"] = pd.to_datetime(df["data_lancamento"], errors="coerce")
    df["data_vencimento"] = pd.to_datetime(df["data_vencimento"], errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)

    return df


def salvar_dados(df):
    df.to_csv(ARQUIVO, index=False)


# =====================================================
# INICIAR BASE
# =====================================================

criar_base()
df = carregar_dados()

# =====================================================
# ESTRUTURA FINANCEIRA
# =====================================================

entradas = ["Comissões", "Outras Entradas"]

saidas = {
"Pessoal":[
"Folha CLT","Folha PJ","Outras Pessoal","Bonus/Dividendos"
],

"Administrativas":[
"Aluguel","Condomínio e IPTU","Conselho","Materiais e Limpeza",
"Vagas Garagem sócios","Viagem e Hospedagem","Manutenções",
"Desp. De representação","Outras adm"
],

"Serv. Terceiro":[
"Contabilidade/Juridico","Tecnologia","Outros"
],

"Marketing":[
"Eventos","Marketing","Patrocínio"
],

"Outras":[
"Ativo Fixo","Financeiras","Parcelamentos","Impostos"
]
}

# =====================================================
# MENU
# =====================================================

menu = st.sidebar.radio(
"Menu",
["Dashboard","Novo Lançamento","Fluxo de Caixa","DRE","Previsão Caixa"]
)

st.title("💰 Sistema Inteligente de Fluxo de Caixa")

# =====================================================
# DASHBOARD
# =====================================================

if menu == "Dashboard":

    if df.empty:
        st.info("Nenhum dado cadastrado.")
    else:

        df["valor_real"] = df.apply(
            lambda x: x["valor"] if x["tipo"]=="Entrada" else -x["valor"],
            axis=1
        )

        saldo = df["valor_real"].sum()
        receitas = df[df["tipo"]=="Entrada"]["valor"].sum()
        despesas = df[df["tipo"]=="Saída"]["valor"].sum()

        col1,col2,col3 = st.columns(3)

        col1.metric("Saldo Atual", f"R$ {saldo:,.2f}")
        col2.metric("Entradas", f"R$ {receitas:,.2f}")
        col3.metric("Saídas", f"R$ {despesas:,.2f}")

        despesas_cat = df[df["tipo"]=="Saída"].groupby("categoria")["valor"].sum().reset_index()

        if not despesas_cat.empty:

            graf = alt.Chart(despesas_cat).mark_bar().encode(
                x="categoria",
                y="valor"
            )

            st.altair_chart(graf, use_container_width=True)

# =====================================================
# NOVO LANÇAMENTO
# =====================================================

if menu == "Novo Lançamento":

    st.subheader("Cadastrar lançamento")

    tipo = st.selectbox("Tipo",["Entrada","Saída"])
    data_lanc = st.date_input("Data lançamento")
    data_venc = st.date_input("Data vencimento")

    if tipo == "Entrada":

        categoria = "Entradas"
        subcategoria = st.selectbox("Subcategoria", entradas)

    else:

        categoria = st.selectbox("Categoria", list(saidas.keys()))
        subcategoria = st.selectbox("Subcategoria", saidas[categoria])

    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.0)
    status = st.selectbox("Status",["Pendente","Pago"])

    if st.button("Salvar"):

        novo = pd.DataFrame([{
            "data_lancamento":data_lanc,
            "data_vencimento":data_venc,
            "tipo":tipo,
            "categoria":categoria,
            "subcategoria":subcategoria,
            "descricao":descricao,
            "valor":valor,
            "status":status
        }])

        df = pd.concat([df,novo], ignore_index=True)
        salvar_dados(df)

        st.success("Lançamento salvo!")
        st.rerun()

# =====================================================
# FLUXO DE CAIXA
# =====================================================

if menu == "Fluxo de Caixa":

    st.subheader("Fluxo financeiro")

    if df.empty:
        st.warning("Sem dados")
    else:

        df["mes"] = df["data_lancamento"].dt.to_period("M")

        meses = sorted(df["mes"].astype(str).unique())

        mes = st.selectbox("Filtrar mês", meses)

        filtrado = df[df["mes"].astype(str)==mes]

        st.dataframe(filtrado, use_container_width=True)

# =====================================================
# DRE
# =====================================================

if menu == "DRE":

    receitas = df[df["tipo"]=="Entrada"]["valor"].sum()
    despesas = df[df["tipo"]=="Saída"]["valor"].sum()
    resultado = receitas - despesas

    st.subheader("Demonstrativo de Resultado")

    st.metric("Receitas", f"R$ {receitas:,.2f}")
    st.metric("Despesas", f"R$ {despesas:,.2f}")
    st.metric("Resultado", f"R$ {resultado:,.2f}")

# =====================================================
# PREVISÃO
# =====================================================

if menu == "Previsão Caixa":

    st.subheader("Previsão de Caixa")

    if not df.empty:

        df["mes"] = df["data_vencimento"].dt.to_period("M")

        previsao = df.groupby(["mes","tipo"])["valor"].sum().unstack(fill_value=0)

        previsao["saldo"] = previsao.get("Entrada",0) - previsao.get("Saída",0)

        previsao["saldo_acumulado"] = previsao["saldo"].cumsum()

        previsao = previsao.reset_index()

        graf = alt.Chart(previsao).mark_line().encode(
            x="mes",
            y="saldo_acumulado"
        )

        st.altair_chart(graf, use_container_width=True)

        st.dataframe(previsao)

# =====================================================
# EXPORTAR
# =====================================================

st.sidebar.download_button(
"Baixar CSV",
df.to_csv(index=False).encode(),
"fluxo_caixa.csv",
" text/csv"
)