#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime
from hashlib import sha256
import io
import base64
import json
import os

# =====================================================================
# --- CONFIGURAÇÃO DA PÁGINA ---
# =====================================================================
st.set_page_config(
    page_title="Controle - Carga e Descarga",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================================
# --- CSS GLOBAL (visual escuro + imagem de fundo) ---
# =====================================================================
def get_base64_image(path):
    """Converte imagem local para base64 para usar como fundo."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

# Caminho da imagem de fundo — ajuste conforme necessário
CAMINHO_FUNDO = r"C:\Users\erick.silva\Desktop\cardes V3 - usuários\fundo_logistica.png"
img_b64 = get_base64_image(CAMINHO_FUNDO)

bg_style = f"""
    background-image: url("data:image/png;base64,{img_b64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
""" if img_b64 else "background-color: #111921;"

st.markdown(f"""
<style>
    /* Fundo geral */
    .stApp {{
        {bg_style}
    }}

    /* Overlay escuro sobre o fundo */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(10, 15, 20, 0.72);
        z-index: 0;
        pointer-events: none;
    }}

    /* Todo conteúdo acima do overlay */
    .block-container {{
        position: relative;
        z-index: 1;
        padding-top: 1rem !important;
    }}

    /* Título */
    h1 {{
        color: #ffffff !important;
        text-align: center;
        font-size: 2rem !important;
        letter-spacing: 2px;
        padding: 0.5rem 0 1rem 0;
        border-bottom: 1px solid #1f3a60;
        margin-bottom: 1.5rem;
    }}

    h2, h3 {{
        color: #a0aec0 !important;
    }}

    /* Labels dos campos */
    label, .stSelectbox label, .stTextInput label,
    .stDateInput label, .stNumberInput label {{
        color: #a0aec0 !important;
        font-weight: bold !important;
        font-size: 0.82rem !important;
    }}

    /* Inputs */
    .stTextInput input, .stNumberInput input {{
        background-color: #1a222d !important;
        color: #dce3ea !important;
        border: 1px solid #2d3e50 !important;
        border-radius: 4px !important;
    }}

    /* Selectbox */
    .stSelectbox div[data-baseweb="select"] > div {{
        background-color: #1a222d !important;
        color: #dce3ea !important;
        border: 1px solid #2d3e50 !important;
    }}

    /* DateInput */
    .stDateInput input {{
        background-color: #1a222d !important;
        color: #dce3ea !important;
        border: 1px solid #2d3e50 !important;
    }}

    /* Campos readonly (Tarifa / Total) */
    .readonly-field {{
        background-color: #1a222d;
        color: #e74c3c;
        font-weight: bold;
        font-size: 1rem;
        border: 1px solid #2d3e50;
        border-radius: 4px;
        padding: 8px 12px;
        text-align: center;
        margin-top: 4px;
    }}

    .readonly-label {{
        color: #a0aec0;
        font-size: 0.82rem;
        font-weight: bold;
        margin-bottom: 2px;
    }}

    /* Frame do formulário */
    .form-container {{
        background-color: rgba(10, 15, 20, 0.85);
        border: 1px solid #34495e;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }}

    /* Botões */
    .stButton > button {{
        border-radius: 5px !important;
        font-weight: bold !important;
        font-size: 0.9rem !important;
        height: 2.5rem !important;
        border: none !important;
        cursor: pointer !important;
    }}

    /* Tabela */
    .stDataFrame {{
        background-color: transparent !important;
    }}

    .stDataFrame table {{
        background-color: transparent !important;
        color: #dce3ea !important;
    }}

    .stDataFrame th {{
        background-color: #0a1118 !important;
        color: #a0aec0 !important;
        font-weight: bold !important;
    }}

    .stDataFrame td {{
        background-color: transparent !important;
        color: #dce3ea !important;
        border-bottom: 1px solid #1f2d3d !important;
    }}

    /* Mensagens */
    .stAlert {{
        background-color: rgba(10, 15, 20, 0.85) !important;
    }}

    /* Login box */
    .login-box {{
        background-color: rgba(10, 15, 20, 0.90);
        border: 1px solid #34495e;
        border-radius: 10px;
        padding: 2rem;
        max-width: 420px;
        margin: 4rem auto;
    }}

    /* Esconde menu padrão do Streamlit */
    #MainMenu, footer, header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)


# =====================================================================
# --- CONEXÃO GOOGLE SHEETS ---
# =====================================================================
@st.cache_resource
def conectar_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Tenta carregar credenciais do secrets (produção) ou arquivo local
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except Exception:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)

    client = gspread.authorize(creds)
    planilha = client.open_by_key("1jq0YByg8407tE1dM_-__r588W6yqgkfjSt824nYURsE")
    return planilha

try:
    planilha = conectar_sheets()
    sheet_dados    = planilha.worksheet("CADASTRO")
    sheet_usuarios = planilha.worksheet("USUARIOS")
except Exception as e:
    st.error(f"❌ Falha ao conectar na nuvem: {e}")
    st.stop()


# =====================================================================
# --- CARREGAR LISTAS E CONFIGURAÇÕES ---
# =====================================================================
@st.cache_data(ttl=300)
def carregar_configuracoes():
    try:
        listas = {
            "COBRANÇA":       planilha.worksheet("COBRANÇA").col_values(1)[1:],
            "TIPO CARGA":     planilha.worksheet("TIPO CARGA").col_values(1)[1:],
            "OPERAÇÃO":       planilha.worksheet("OPERAÇÃO").col_values(1)[1:],
            "TRANSPORTADORA": planilha.worksheet("TRANSPORTADORA").col_values(1)[1:],
            "TIPO CARRO":     planilha.worksheet("TIPO CARRO").col_values(1)[1:],
            "FILIAL":         planilha.worksheet("FILIAL").col_values(1)[1:],
        }
        aba_val = planilha.worksheet("VALORES").get_all_values()
        tarifas = {r[0].strip().upper(): r[1] for r in aba_val[1:] if len(r) >= 2}
        clientes = sorted([r[0] for r in aba_val[1:] if len(r) >= 1])
        return listas, clientes, tarifas
    except Exception as e:
        st.error(f"Erro ao carregar configurações: {e}")
        return {}, [], {}

listas, clientes, banco_tarifas = carregar_configuracoes()


# =====================================================================
# --- HELPERS ---
# =====================================================================
def senha_hash(senha):
    return sha256(senha.encode("utf-8")).hexdigest()

def normalizar(txt):
    return str(txt).strip().lower()

def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def parse_moeda(valor):
    try:
        return float(str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", "."))
    except:
        return 0.0


# =====================================================================
# --- USUÁRIOS ---
# =====================================================================
def get_usuarios_df():
    valores = sheet_usuarios.get_all_values()
    if len(valores) < 2:
        return pd.DataFrame(columns=["FILIAL","USUARIO_EMAIL","NOME","SENHA_HASH","ATIVO","CRIADO_EM","ULTIMO_LOGIN"])
    df = pd.DataFrame(valores[1:], columns=valores[0])
    df.columns = [c.strip().upper() for c in df.columns]
    for col in ["FILIAL","USUARIO_EMAIL","NOME","SENHA_HASH","ATIVO","CRIADO_EM","ULTIMO_LOGIN"]:
        if col not in df.columns:
            df[col] = ""
    return df

def encontrar_usuario(email, filial):
    df = get_usuarios_df()
    if df.empty:
        return None
    mask = (df["USUARIO_EMAIL"].str.strip().str.lower() == normalizar(email)) & \
           (df["FILIAL"].str.strip().str.lower() == normalizar(filial))
    if not mask.any():
        return None
    return df[mask].iloc[0].to_dict()

def autenticar_usuario(filial, email, senha):
    u = encontrar_usuario(email, filial)
    if not u:
        return False, "Usuário não encontrado para esta filial."
    if str(u.get("ATIVO","")).strip().upper() not in ["SIM","S","1","TRUE","ATIVO"]:
        return False, "Usuário inativo."
    senha_atual = str(u.get("SENHA_HASH","")).strip()
    if not senha_atual:
        return None, "SEM_SENHA"
    if senha_hash(senha) != senha_atual:
        return False, "Senha inválida."
    return True, u

def criar_usuario(filial, email, nome, senha):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    u = encontrar_usuario(email, filial)
    if u:
        # Atualiza senha
        df = get_usuarios_df()
        mask = (df["USUARIO_EMAIL"].str.strip().str.lower() == normalizar(email)) & \
               (df["FILIAL"].str.strip().str.lower() == normalizar(filial))
        idx = df[mask].index[0] + 2
        row = [filial, email, nome, senha_hash(senha), "SIM", u.get("CRIADO_EM", agora), agora]
        sheet_usuarios.update(f"A{idx}:G{idx}", [row])
    else:
        sheet_usuarios.append_row([filial, email, nome, senha_hash(senha), "SIM", agora, agora])

def registrar_login(filial, email):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    df = get_usuarios_df()
    mask = (df["USUARIO_EMAIL"].str.strip().str.lower() == normalizar(email)) & \
           (df["FILIAL"].str.strip().str.lower() == normalizar(filial))
    if mask.any():
        idx = df[mask].index[0] + 2
        sheet_usuarios.update(f"G{idx}", [[agora]])


# =====================================================================
# --- SESSION STATE ---
# =====================================================================
if "logado" not in st.session_state:
    st.session_state.logado       = False
    st.session_state.usuario      = {}
    st.session_state.filial       = ""
    st.session_state.criar_conta  = False


# =====================================================================
# --- TELA DE LOGIN ---
# =====================================================================
def tela_login():
    st.markdown("<h1>🚛 CONTROLE - CARGA E DESCARGA</h1>", unsafe_allow_html=True)

    col_esp1, col_form, col_esp2 = st.columns([1, 1.2, 1])
    with col_form:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("### 🔐 Acesso ao Sistema")

        filial = st.selectbox("Filial", [""] + listas.get("FILIAL", []), key="login_filial")
        email  = st.text_input("E-mail / Usuário", key="login_email")
        senha  = st.text_input("Senha", type="password", key="login_senha")

        col1, col2 = st.columns(2)
        with col1:
            entrar = st.button("✅ ENTRAR", use_container_width=True)
        with col2:
            novo   = st.button("➕ CRIAR CONTA", use_container_width=True)

        if entrar:
            if not filial or not email:
                st.warning("Selecione a filial e informe o e-mail.")
            else:
                resultado, dados = autenticar_usuario(filial, email, senha)
                if resultado is True:
                    st.session_state.logado  = True
                    st.session_state.usuario = dados
                    st.session_state.filial  = filial
                    registrar_login(filial, email)
                    st.rerun()
                elif resultado is None:
                    st.session_state.criar_conta = True
                    st.session_state.filial = filial
                    st.session_state.email_novo = email
                    st.rerun()
                else:
                    st.error(dados)

        if novo:
            st.session_state.criar_conta = True
            st.session_state.email_novo  = email
            st.session_state.filial      = filial
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


def tela_criar_conta():
    st.markdown("<h1>🚛 CRIAR CONTA</h1>", unsafe_allow_html=True)

    col_esp1, col_form, col_esp2 = st.columns([1, 1.2, 1])
    with col_form:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("### 👤 Novo Usuário")

        filial  = st.selectbox("Filial", [""] + listas.get("FILIAL", []),
                               index=(listas.get("FILIAL",[]) + [""]).index(st.session_state.filial)
                               if st.session_state.filial in listas.get("FILIAL",[]) else 0,
                               key="cc_filial")
        email   = st.text_input("E-mail", value=st.session_state.get("email_novo",""), key="cc_email")
        nome    = st.text_input("Nome completo", key="cc_nome")
        senha1  = st.text_input("Senha", type="password", key="cc_senha1")
        senha2  = st.text_input("Confirmar senha", type="password", key="cc_senha2")

        col1, col2 = st.columns(2)
        with col1:
            salvar = st.button("💾 SALVAR", use_container_width=True)
        with col2:
            voltar = st.button("← VOLTAR", use_container_width=True)

        if salvar:
            if not filial or not email or not nome or not senha1:
                st.warning("Preencha todos os campos.")
            elif senha1 != senha2:
                st.error("As senhas não conferem.")
            else:
                criar_usuario(filial, email, nome, senha1)
                st.success("Conta criada! Faça login.")
                st.session_state.criar_conta = False
                st.rerun()

        if voltar:
            st.session_state.criar_conta = False
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


# =====================================================================
# --- TELA PRINCIPAL ---
# =====================================================================
def calcular_tarifa(operacao, cliente, peso_str):
    operacao = operacao.strip().upper()
    cliente  = cliente.strip().upper()

    if operacao == "SIMBOLOGIA":
        return 30.0, 30.0
    elif cliente == "AMAGGI (JANELA <6810KG)":
        return 150.0, 150.0
    else:
        tarifa = parse_moeda(banco_tarifas.get(cliente, "0"))
        try:
            peso  = float(str(peso_str).replace(",", ".")) if peso_str else 0.0
        except:
            peso  = 0.0
        total = (peso / 1000) * tarifa
        return tarifa, total


def tela_principal():
    usuario = st.session_state.usuario
    filial  = st.session_state.filial

    # Cabeçalho
    col_t, col_sair = st.columns([5, 1])
    with col_t:
        st.markdown("<h1>🚛 CONTROLE - CARGA E DESCARGA</h1>", unsafe_allow_html=True)
    with col_sair:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Sair", use_container_width=True):
            for k in ["logado","usuario","filial","criar_conta"]:
                st.session_state[k] = False if k == "logado" else "" if k in ["filial"] else {}
            st.rerun()

    nome_usuario = usuario.get("NOME", usuario.get("USUARIO_EMAIL", ""))
    st.markdown(
        f'<p style="color:#a0aec0; text-align:right; margin-top:-1rem;">👤 {nome_usuario} &nbsp;|&nbsp; 🏢 {filial}</p>',
        unsafe_allow_html=True
    )

    # ----------------------------------------------------------------
    # FORMULÁRIO
    # ----------------------------------------------------------------
    st.markdown('<div class="form-container">', unsafe_allow_html=True)

    # Linha 1
    c1, c2, c3, c4, c5 = st.columns([1, 1, 2, 1.5, 1])
    with c1:
        cobranca     = st.selectbox("Cobrança",      [""] + listas.get("COBRANÇA", []),      key="f_cobranca")
    with c2:
        data_sel     = st.date_input("Data",          value=date.today(),                      key="f_data",
                                     format="DD/MM/YYYY")
    with c3:
        cliente      = st.selectbox("Cliente",        [""] + clientes,                         key="f_cliente")
    with c4:
        transportadora = st.selectbox("Transportadora", [""] + listas.get("TRANSPORTADORA",[]), key="f_transp")
    with c5:
        placa        = st.text_input("Placa",                                                   key="f_placa")

    # Linha 2
    c1, c2, c3, c4, c5 = st.columns([1, 1, 2, 1.5, 1])
    with c1:
        peso         = st.text_input("Peso (kg)",                                               key="f_peso")
    with c2:
        notas        = st.text_input("Notas Fiscais",                                           key="f_notas")
    with c3:
        tipo_carga   = st.selectbox("Tipo Carga",    [""] + listas.get("TIPO CARGA", []),      key="f_tcarga")
    with c4:
        operacao     = st.selectbox("Operação",      [""] + listas.get("OPERAÇÃO", []),        key="f_op")
    with c5:
        tipo_carro   = st.selectbox("Tipo de Carro", [""] + listas.get("TIPO CARRO", []),      key="f_tcarro")

    # Linha 3 — Tarifa, Total, Obs, Filial
    tarifa_val, total_val = calcular_tarifa(operacao, cliente, peso)

    c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
    with c1:
        st.markdown('<p class="readonly-label">Tarifa</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="readonly-field">{formatar_moeda(tarifa_val)}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<p class="readonly-label">Total a Cobrar</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="readonly-field">{formatar_moeda(total_val)}</div>', unsafe_allow_html=True)
    with c3:
        obs          = st.text_input("Observação",                                              key="f_obs")
    with c4:
        st.markdown(f'<p class="readonly-label">Filial</p><div class="readonly-field">{filial}</div>',
                    unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------------------------------------------
    # BOTÕES
    # ----------------------------------------------------------------
    bc1, bc2, bc3, bc4 = st.columns([1.5, 1.5, 1.5, 3])
    with bc1:
        salvar_btn = st.button("💾 SALVAR AGENDAMENTO", use_container_width=True)
    with bc2:
        relatorio_btn = st.button("📊 GERAR RELATÓRIO", use_container_width=True)
    with bc3:
        refresh_btn = st.button("🔄 ATUALIZAR TABELA", use_container_width=True)

    # ----------------------------------------------------------------
    # SALVAR
    # ----------------------------------------------------------------
    if salvar_btn:
        campos_obrigatorios = {
            "Cobrança": cobranca, "Cliente": cliente,
            "Transportadora": transportadora, "Placa": placa,
            "Peso": peso, "Notas Fiscais": notas,
            "Tipo Carga": tipo_carga, "Operação": operacao,
            "Tipo de Carro": tipo_carro
        }
        faltando = [k for k, v in campos_obrigatorios.items() if not str(v).strip()]
        if faltando:
            st.warning(f"Campo(s) obrigatório(s): {', '.join(faltando)}")
        else:
            data_fmt = data_sel.strftime("%d/%m/%Y")
            # Verifica duplicidade
            try:
                vals = sheet_dados.get_all_values()
                if len(vals) > 1:
                    df_c = pd.DataFrame(vals[1:], columns=vals[0])
                    df_c.columns = [c.strip().upper() for c in df_c.columns]
                    dup = df_c[
                        (df_c.get("DATA","") == data_fmt) &
                        (df_c.get("CLIENTE","").str.upper() == cliente.upper()) &
                        (df_c.get("PLACA","").str.upper() == placa.upper())
                    ]
                    if not dup.empty:
                        st.warning("⚠️ Registro duplicado encontrado. Verifique antes de salvar novamente.")
            except:
                pass

            linha = [
                cobranca, data_fmt, cliente, transportadora, placa,
                peso, notas, tipo_carga, operacao, tipo_carro,
                tarifa_val, total_val, obs, filial,
                usuario.get("USUARIO_EMAIL",""),
                datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            ]
            try:
                sheet_dados.append_row(linha)
                st.success("✅ Agendamento salvo com sucesso!")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    # ----------------------------------------------------------------
    # RELATÓRIO
    # ----------------------------------------------------------------
    if relatorio_btn:
        st.session_state.mostrar_relatorio = True

    if st.session_state.get("mostrar_relatorio"):
        with st.expander("📅 Período do Relatório", expanded=True):
            rc1, rc2, rc3 = st.columns([1, 1, 1])
            with rc1:
                d_ini = st.date_input("De", value=date.today(), key="r_ini", format="DD/MM/YYYY")
            with rc2:
                d_fim = st.date_input("Até", value=date.today(), key="r_fim", format="DD/MM/YYYY")
            with rc3:
                st.markdown("<br>", unsafe_allow_html=True)
                gerar = st.button("⬇️ BAIXAR EXCEL", use_container_width=True)

            if gerar:
                try:
                    vals = sheet_dados.get_all_values()
                    df = pd.DataFrame(vals[1:], columns=vals[0])
                    df.columns = [c.strip().upper() for c in df.columns]
                    df["DATA"] = pd.to_datetime(df["DATA"], format="%d/%m/%Y", errors="coerce")
                    df = df.dropna(subset=["DATA"])
                    df_f = df[
                        (df["DATA"].dt.date >= d_ini) &
                        (df["DATA"].dt.date <= d_fim) &
                        (df["FILIAL"].str.upper() == filial.upper())
                    ].copy()

                    if df_f.empty:
                        st.warning("Nenhum dado encontrado no período.")
                    else:
                        df_f["DATA"] = df_f["DATA"].dt.strftime("%d/%m/%Y")
                        if "USUARIO_EMAIL" in df_f.columns:
                            df_f.rename(columns={"USUARIO_EMAIL":"USUARIO"}, inplace=True)

                        buffer = io.BytesIO()
                        df_f.to_excel(buffer, index=False)
                        buffer.seek(0)
                        nome_arq = f"Relatorio_{filial}_{datetime.now().strftime('%d%m%Y')}.xlsx"
                        st.download_button("📥 Clique para baixar", buffer, nome_arq,
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                except Exception as e:
                    st.error(f"Erro ao gerar relatório: {e}")

    # ----------------------------------------------------------------
    # TABELA
    # ----------------------------------------------------------------
    st.markdown("---")
    st.markdown('<p style="color:#a0aec0; font-size:0.85rem; margin-bottom:0.3rem;">📋 Agendamentos da filial (mais recentes primeiro)</p>',
                unsafe_allow_html=True)
    try:
        vals = sheet_dados.get_all_values()
        if len(vals) > 1:
            df = pd.DataFrame(vals[1:], columns=vals[0])
            df.columns = [c.strip().upper() for c in df.columns]
            df_f = df[df["FILIAL"].str.upper() == filial.upper()].iloc[::-1].reset_index(drop=True)
            df_f.index += 1
            df_f.index.name = "#"

            # Colunas para exibir
            colunas_exibir = ["COBRANÇA","DATA","CLIENTE","TRANSPORTADORA","PLACA",
                               "PESO","NOTAS FISCAIS","TIPO CARGA","OPERAÇÃO",
                               "TIPO DE CARRO","TARIFA","TOTAL A COBRAR","OBSERVAÇÃO"]
            colunas_exibir = [c for c in colunas_exibir if c in df_f.columns]

            st.dataframe(
                df_f[colunas_exibir],
                use_container_width=True,
                height=380
            )
        else:
            st.info("Nenhum agendamento encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar tabela: {e}")


# =====================================================================
# --- ROTEAMENTO ---
# =====================================================================
if st.session_state.criar_conta:
    tela_criar_conta()
elif not st.session_state.logado:
    tela_login()
else:
    tela_principal()
