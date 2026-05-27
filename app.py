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
# --- CARREGAR IMAGENS LOCAIS COMO BASE64 ---
# =====================================================================
def img_to_b64(path, mime="image/png"):
    try:
        with open(path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        return f"data:{mime};base64,{b64}"
    except:
        return ""


caminhao_src    = img_to_b64("caminhão.png",     "image/png")
empilhadeira_src= img_to_b64("empilhadeira.png", "image/png")
gif_src         = img_to_b64("rodape.gif",       "image/gif")


# =====================================================================
# --- CSS GLOBAL ---
# =====================================================================
st.markdown(f"""
<style>
    .stApp {{
        background-color: #111921;
    }}

    .block-container {{
        position: relative;
        z-index: 1;
        padding-top: 0.5rem !important;
    }}

    h1 {{
        color: #ffffff !important;
        text-align: center;
        font-size: 2.4rem !important;
        letter-spacing: 3px;
        padding: 0.3rem 0 0.8rem 0;
        border-bottom: 1px solid #1f3a60;
        margin-bottom: 1rem;
    }}

    h2, h3 {{
        color: #a0aec0 !important;
    }}

    label, .stSelectbox label, .stTextInput label,
    .stDateInput label, .stNumberInput label {{
        color: #a0aec0 !important;
        font-weight: bold !important;
        font-size: 0.82rem !important;
    }}

    .stTextInput input, .stNumberInput input {{
        background-color: #1a222d !important;
        color: #dce3ea !important;
        border: 1px solid #2d3e50 !important;
        border-radius: 4px !important;
    }}

    .stSelectbox div[data-baseweb="select"] > div {{
        background-color: #1a222d !important;
        color: #dce3ea !important;
        border: 1px solid #2d3e50 !important;
    }}

    .stDateInput input {{
        background-color: #1a222d !important;
        color: #dce3ea !important;
        border: 1px solid #2d3e50 !important;
    }}

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

    .form-container {{
        background-color: rgba(10, 15, 20, 0.88);
        border: 1px solid #34495e;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        position: relative;
        overflow: hidden;
    }}

    .form-container::before {{
        content: "";
        position: absolute;
        left: -10px;
        top: 50%;
        transform: translateY(-50%);
        width: 160px;
        height: 160px;
        background-image: url("{caminhao_src}");
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        opacity: 0.10;
        mix-blend-mode: screen;
        pointer-events: none;
        z-index: 0;
    }}

    .form-container::after {{
        content: "";
        position: absolute;
        right: -10px;
        top: 50%;
        transform: translateY(-50%);
        width: 160px;
        height: 160px;
        background-image: url("{empilhadeira_src}");
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        opacity: 0.10;
        mix-blend-mode: screen;
        pointer-events: none;
        z-index: 0;
    }}

    .form-container > * {{
        position: relative;
        z-index: 1;
    }}

    .stButton > button {{
        width: 100% !important;
        height: 3rem !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: linear-gradient(135deg, #1f3a60 0%, #2c5282 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.05);
        transition: all 0.25s ease !important;
        cursor: pointer !important;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.45), 0 0 10px rgba(66,153,225,0.35);
        border: 1px solid rgba(255,255,255,0.15) !important;
    }}

    .stButton > button:active {{
        transform: scale(0.98);
    }}

    button[key="btn_salvar"] {{
        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%) !important;
        border: 1px solid rgba(46, 204, 113, 0.3) !important;
    }}

    button[key="btn_relatorio"] {{
        background: linear-gradient(135deg, #2980b9 0%, #3498db 100%) !important;
        border: 1px solid rgba(52, 152, 219, 0.3) !important;
    }}

    button[key="btn_atualizar"] {{
        background: linear-gradient(135deg, #e67e22 0%, #f39c12 100%) !important;
        border: 1px solid rgba(243, 156, 18, 0.3) !important;
    }}

    button[label*="Sair"] {{
        background: linear-gradient(135deg, #c0392b 0%, #e74c3c 100%) !important;
        border: 1px solid rgba(231, 76, 60, 0.3) !important;
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

    .login-box {{
        background-color: rgba(10, 15, 20, 0.90);
        border: 1px solid #34495e;
        border-radius: 10px;
        padding: 2rem;
        max-width: 420px;
        margin: 2rem auto;
    }}

    .header-row {{
        display: flex;
        align-items: center;
        gap: 18px;
        margin-bottom: 0.5rem;
    }}

    .header-gif {{
        height: 64px;
        width: auto;
        flex-shrink: 0;
    }}

    .header-title {{
        color: #ffffff;
        font-size: 2.4rem;
        font-weight: bold;
        letter-spacing: 3px;
        flex: 1;
        text-align: center;
        border-bottom: 1px solid #1f3a60;
        padding-bottom: 0.4rem;
    }}

    #MainMenu, footer, header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)


# =====================================================================
# --- CONEXÃO GOOGLE SHEETS ---
# =====================================================================
@st.cache_resource
def conectar_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except Exception:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1jq0YByg8407tE1dM_-__r588W6yqgkfjSt824nYURsE")


try:
    planilha       = conectar_sheets()
    sheet_dados    = planilha.worksheet("CADASTRO")
    sheet_usuarios = planilha.worksheet("USUARIOS")
except Exception as e:
    st.error(f"❌ Falha ao conectar na nuvem: {e}")
    st.stop()


# =====================================================================
# --- CONFIGURAÇÕES ---
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
        aba_val  = planilha.worksheet("VALORES").get_all_values()
        tarifas  = {r[0].strip().upper(): r[1] for r in aba_val[1:] if len(r) >= 2}
        clientes = sorted([r[0] for r in aba_val[1:] if len(r) >= 1])
        return listas, clientes, tarifas
    except Exception as e:
        st.error(f"Erro ao carregar configurações: {e}")
        return {}, [], {}


listas, clientes, banco_tarifas = carregar_configuracoes()


# =====================================================================
# --- HELPERS ---
# =====================================================================
def senha_hash(s):   return sha256(s.encode()).hexdigest()
def normalizar(t):   return str(t).strip().lower()


def formatar_moeda(v):
    try:   return f"R$ {float(v):,.2f}".replace(",","X").replace(".","," ).replace("X",".")
    except: return "R$ 0,00"


def parse_moeda(v):
    try:   return float(str(v).replace("R$","").replace(" ","").replace(".","").replace(",","."))
    except: return 0.0


# =====================================================================
# --- USUÁRIOS ---
# =====================================================================
def get_usuarios_df():
    vals = sheet_usuarios.get_all_values()
    if len(vals) < 2:
        return pd.DataFrame(columns=["FILIAL","USUARIO_EMAIL","NOME","SENHA_HASH","ATIVO","CRIADO_EM","ULTIMO_LOGIN"])
    df = pd.DataFrame(vals[1:], columns=vals[0])
    df.columns = [c.strip().upper() for c in df.columns]
    for col in ["FILIAL","USUARIO_EMAIL","NOME","SENHA_HASH","ATIVO","CRIADO_EM","ULTIMO_LOGIN"]:
        if col not in df.columns: df[col] = ""
    return df


def encontrar_usuario(email, filial):
    df = get_usuarios_df()
    if df.empty: return None
    mask = (df["USUARIO_EMAIL"].str.strip().str.lower() == normalizar(email)) & \
           (df["FILIAL"].str.strip().str.lower() == normalizar(filial))
    return df[mask].iloc[0].to_dict() if mask.any() else None


def autenticar_usuario(filial, email, senha):
    u = encontrar_usuario(email, filial)
    if not u: return False, "Usuário não encontrado para esta filial."
    if str(u.get("ATIVO","")).strip().upper() not in ["SIM","S","1","TRUE","ATIVO"]:
        return False, "Usuário inativo."
    sh = str(u.get("SENHA_HASH","")).strip()
    if not sh: return None, "SEM_SENHA"
    if senha_hash(senha) != sh: return False, "Senha inválida."
    return True, u


def criar_usuario(filial, email, nome, senha):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    u = encontrar_usuario(email, filial)
    if u:
        df   = get_usuarios_df()
        mask = (df["USUARIO_EMAIL"].str.strip().str.lower() == normalizar(email)) & \
               (df["FILIAL"].str.strip().str.lower() == normalizar(filial))
        idx  = df[mask].index[0] + 2
        sheet_usuarios.update(f"A{idx}:G{idx}", [[filial, email, nome, senha_hash(senha), "SIM", u.get("CRIADO_EM", agora), agora]])
    else:
        sheet_usuarios.append_row([filial, email, nome, senha_hash(senha), "SIM", agora, agora])


def registrar_login(filial, email):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    df    = get_usuarios_df()
    mask  = (df["USUARIO_EMAIL"].str.strip().str.lower() == normalizar(email)) & \
            (df["FILIAL"].str.strip().str.lower() == normalizar(filial))
    if mask.any():
        sheet_usuarios.update(f"G{df[mask].index[0]+2}", [[agora]])


# =====================================================================
# --- SESSION STATE ---
# =====================================================================
for k, v in [("logado",False),("usuario",{}),("filial",""),("criar_conta",False),("mostrar_relatorio",False)]:
    if k not in st.session_state:
        st.session_state[k] = v


# =====================================================================
# --- CABEÇALHO COM GIF ---
# =====================================================================
def render_header():
    gif_html = f'<img src="{gif_src}" class="header-gif">' if gif_src else ""
    st.markdown(f"""
    <div class="header-row">
        {gif_html}
        <div class="header-title">🚛 CONTROLE - CARGA E DESCARGA</div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================================
# --- TELA DE LOGIN ---
# =====================================================================
def tela_login():
    render_header()
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("### 🔐 Acesso ao Sistema")
        filial = st.selectbox("Filial", [""] + listas.get("FILIAL", []), key="login_filial")
        email  = st.text_input("E-mail / Usuário", key="login_email")
        senha  = st.text_input("Senha", type="password", key="login_senha")
        c1, c2 = st.columns(2)
        with c1: entrar = st.button("✅ ENTRAR",       use_container_width=True)
        with c2: novo   = st.button("➕ CRIAR CONTA",  use_container_width=True)

        if entrar:
            if not filial or not email:
                st.warning("Selecione a filial e informe o e-mail.")
            else:
                res, dados = autenticar_usuario(filial, email, senha)
                if res is True:
                    st.session_state.update(logado=True, usuario=dados, filial=filial)
                    registrar_login(filial, email)
                    st.rerun()
                elif res is None:
                    st.session_state.update(criar_conta=True, filial=filial, email_novo=email)
                    st.rerun()
                else:
                    st.error(dados)

        if novo:
            st.session_state.update(criar_conta=True, email_novo=email, filial=filial)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# =====================================================================
# --- TELA CRIAR CONTA ---
# =====================================================================
def tela_criar_conta():
    render_header()
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("### 👤 Novo Usuário")
        filial_list = listas.get("FILIAL", [])
        idx_f = filial_list.index(st.session_state.filial) + 1 if st.session_state.filial in filial_list else 0
        filial = st.selectbox("Filial", [""] + filial_list, index=idx_f, key="cc_filial")
        email  = st.text_input("E-mail",          value=st.session_state.get("email_novo",""), key="cc_email")
        nome   = st.text_input("Nome completo",    key="cc_nome")
        senha1 = st.text_input("Senha",            type="password", key="cc_senha1")
        senha2 = st.text_input("Confirmar senha",  type="password", key="cc_senha2")
        c1, c2 = st.columns(2)
        with c1: salvar = st.button("💾 SALVAR",  use_container_width=True)
        with c2: voltar = st.button("← VOLTAR",   use_container_width=True)

        if salvar:
            if not all([filial, email, nome, senha1]):
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
    op = operacao.strip().upper()
    cl = cliente.strip().upper()
    if op == "SIMBOLOGIA":         return 30.0, 30.0
    if cl == "AMAGGI (JANELA <6810KG)": return 150.0, 150.0
    tarifa = parse_moeda(banco_tarifas.get(cl, "0"))
    try:   peso = float(str(peso_str).replace(",",".")) if peso_str else 0.0
    except: peso = 0.0
    return tarifa, (peso / 1000) * tarifa


def tela_principal():
    usuario = st.session_state.usuario
    filial  = st.session_state.filial

    col_h, col_sair = st.columns([6, 1])
    with col_h:
        gif_html = f'<img src="{gif_src}" class="header-gif">' if gif_src else ""
        st.markdown(f"""
        <div class="header-row">
            {gif_html}
            <div class="header-title">🚛 CONTROLE - CARGA E DESCARGA</div>
        </div>
        """, unsafe_allow_html=True)
    with col_sair:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.update(logado=False, usuario={}, filial="", criar_conta=False)
            st.rerun()

    nome_u = usuario.get("NOME", usuario.get("USUARIO_EMAIL",""))
    st.markdown(f'<p style="color:#a0aec0;text-align:right;margin-top:-0.5rem;">👤 {nome_u} &nbsp;|&nbsp; 🏢 {filial}</p>',
                unsafe_allow_html=True)

    st.markdown('<div class="form-container">', unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns([1,1,2,1.5,1])
    with c1: cobranca       = st.selectbox("Cobrança",        [""] + listas.get("COBRANÇA",[]),       key="f_cob")
    with c2: data_sel       = st.date_input("Data",           value=date.today(), key="f_data", format="DD/MM/YYYY")
    with c3: cliente        = st.selectbox("Cliente",         [""] + clientes,                        key="f_cli")
    with c4: transportadora = st.selectbox("Transportadora",  [""] + listas.get("TRANSPORTADORA",[]), key="f_tra")
    with c5: placa          = st.text_input("Placa",                                                  key="f_pla")

    c1,c2,c3,c4,c5 = st.columns([1,1,2,1.5,1])
    with c1: peso       = st.text_input("Peso (kg)",                                                  key="f_pes")
    with c2: notas      = st.text_input("Notas Fiscais",                                              key="f_not")
    with c3: tipo_carga = st.selectbox("Tipo Carga",   [""] + listas.get("TIPO CARGA",[]),  key="f_tca")
    with c4: operacao   = st.selectbox("Operação",     [""] + listas.get("OPERAÇÃO",[]),    key="f_ope")
    with c5: tipo_carro = st.selectbox("Tipo de Carro", [""] + listas.get("TIPO CARRO",[]), key="f_tco")

    tarifa_val, total_val = calcular_tarifa(operacao, cliente, peso)

    c1,c2,c3,c4 = st.columns([1,1,2,1])
    with c1:
        st.markdown('<p class="readonly-label">Tarifa</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="readonly-field">{formatar_moeda(tarifa_val)}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<p class="readonly-label">Total a Cobrar</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="readonly-field">{formatar_moeda(total_val)}</div>', unsafe_allow_html=True)
    with c3: obs = st.text_input("Observação", key="f_obs")
    with c4:
        st.markdown(f'<p class="readonly-label">Filial</p><div class="readonly-field">{filial}</div>',
                    unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    esp1, bc1, bc2, bc3, esp2 = st.columns([1,1.5,1.5,1.5,1])
    
    with bc1:
        salvar_btn = st.button(
            "💾 SALVAR AGENDAMENTO",
            use_container_width=True,
            key="btn_salvar"    # ← ESSA KEY APLICA A COR VERDE
        )

    with bc2:
        relatorio_btn = st.button(
             "📊 GERAR RELATÓRIO",
            use_container_width=True,
            key="btn_relatorio"    # ← ESSA KEY APLICA A COR AZUL
        )

    with bc3:
        refresh_btn = st.button(
            "🔄 ATUALIZAR TABELA",
            use_container_width=True,
            key="btn_atualizar"    # ← ESSA KEY APLICA A COR LARANJA
        )

    faltando = []

    if salvar_btn:
        obrig = {"Cobrança":cobranca,"Cliente":cliente,"Transportadora":transportadora,
                 "Placa":placa,"Peso":peso,"Notas Fiscais":notas,
                 "Tipo Carga":tipo_carga,"Operação":operacao,"Tipo de Carro":tipo_carro}
        faltando = [k for k,v in obrig.items() if not str(v).strip()]

    if faltando:
        st.warning(f"Campo(s) obrigatório(s): {', '.join(faltando)}")
    else:
        data_fmt = data_sel.strftime("%d/%m/%Y")
        linha = [cobranca, data_fmt, cliente, transportadora, placa,
                 peso, notas, tipo_carga, operacao, tipo_carro,
                 tarifa_val, total_val, obs, filial,
                 usuario.get("USUARIO_EMAIL",""),
                 datetime.now().strftime("%d/%m/%Y %H:%M:%S")]
        try:
            vals_exist = sheet_dados.get_all_values()

            if len(vals_exist) > 1:
                df_exist = pd.DataFrame(vals_exist[1:], columns=vals_exist[0])
                df_exist.columns = [c.strip().upper() for c in df_exist.columns]

                colunas_linha = [
                    "COBRANÇA", "DATA", "CLIENTE", "TRANSPORTADORA", "PLACA",
                    "PESO", "NOTAS FISCAIS", "TIPO CARGA", "OPERAÇÃO",
                    "TIPO DE CARRO", "TARIFA", "TOTAL A COBRAR", "OBSERVAÇÃO",
                    "FILIAL", "USUARIO_EMAIL", "ULTIMO_LOGIN"
                ]

                for col in colunas_linha:
                    if col not in df_exist.columns:
                        df_exist[col] = ""

                chave_nova = "|".join([str(v).strip() for v in linha])
                chaves_existentes = df_exist[colunas_linha].fillna("").astype(str).apply(
                    lambda r: "|".join([x.strip() for x in r.tolist()]), axis=1
                )

                if chave_nova in set(chaves_existentes):
                    st.warning("⚠️ Registro duplicado detectado. Nada foi salvo.")
                else:
                    sheet_dados.append_row(linha)
                    st.success("✅ Agendamento salvo com sucesso!")
                    st.cache_data.clear()
            else:
                sheet_dados.append_row(linha)
                st.success("✅ Agendamento salvo com sucesso!")
                st.cache_data.clear()

        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    if relatorio_btn:
        st.session_state.mostrar_relatorio = True

    if st.session_state.mostrar_relatorio:
        with st.expander("📅 Período do Relatório", expanded=True):
            rc1,rc2,rc3 = st.columns([1,1,1])
            with rc1: d_ini = st.date_input("De",   value=date.today(), key="r_ini", format="DD/MM/YYYY")
            with rc2: d_fim = st.date_input("Até",  value=date.today(), key="r_fim", format="DD/MM/YYYY")
            with rc3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⬇️ BAIXAR EXCEL", use_container_width=True):
                    try:
                        vals = sheet_dados.get_all_values()
                        df   = pd.DataFrame(vals[1:], columns=vals[0])
                        df.columns = [c.strip().upper() for c in df.columns]
                        df["DATA"] = pd.to_datetime(df["DATA"], format="%d/%m/%Y", errors="coerce")
                        df = df.dropna(subset=["DATA"])
                        df_f = df[(df["DATA"].dt.date >= d_ini) &
                                  (df["DATA"].dt.date <= d_fim) &
                                  (df["FILIAL"].str.upper() == filial.upper())].copy()
                        if df_f.empty:
                            st.warning("Nenhum dado encontrado no período.")
                        else:
                            df_f["DATA"] = df_f["DATA"].dt.strftime("%d/%m/%Y")
                            if "USUARIO_EMAIL" in df_f.columns:
                                df_f.rename(columns={"USUARIO_EMAIL":"USUARIO"}, inplace=True)
                            buf = io.BytesIO()
                            df_f.to_excel(buf, index=False)
                            buf.seek(0)
                            st.download_button("📥 Clique para baixar", buf,
                                f"Relatorio_{filial}_{datetime.now().strftime('%d%m%Y')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    st.markdown("---")
    st.markdown('<p style="color:#a0aec0;font-size:0.85rem;margin-bottom:0.3rem;">📋 Agendamentos da filial (mais recentes primeiro)</p>',
                unsafe_allow_html=True)
    try:
        vals = sheet_dados.get_all_values()
        if len(vals) > 1:
            df   = pd.DataFrame(vals[1:], columns=vals[0])
            df.columns = [c.strip().upper() for c in df.columns]
            df_f = df[df["FILIAL"].str.upper() == filial.upper()].iloc[::-1].reset_index(drop=True)
            df_f.index += 1
            df_f.index.name = "#"
            cols = ["COBRANÇA","DATA","CLIENTE","TRANSPORTADORA","PLACA","PESO",
                    "NOTAS FISCAIS","TIPO CARGA","OPERAÇÃO","TIPO DE CARRO",
                    "TARIFA","TOTAL A COBRAR","OBSERVAÇÃO"]
            cols = [c for c in cols if c in df_f.columns]
            st.dataframe(df_f[cols], use_container_width=True, height=380)
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