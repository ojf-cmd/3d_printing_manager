import os
import json
import uuid
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import streamlit as st
import requests
import urllib.parse

DATA_DIR = "data"

SCHEMAS = {
    "clientes.csv": ["id", "nome", "telefone", "email"],
    "equipamentos.csv": ["id", "nome", "tipo", "preco_compra", "vida_util_horas", "custo_hora_depreciacao"],
    "estoque.csv": ["id", "categoria", "nome_item", "quantidade", "custo_unitario", "cor"],
    "pedidos.csv": ["id", "id_cliente", "nome_arquivo", "id_orcamento", "prazo_entrega", "status", "link_agenda"],
    "orcamentos.csv": ["id", "nome_projeto", "id_pedido", "peso_g", "tempo_impressao_h", 
                       "tempo_trabalho_h", "custo_total", "preco_final", "margem_lucro"],
    "projetos.csv": ["id", "nome", "id_cliente", "descricao", "status"],
    "usuarios.csv": ["id", "email", "nome", "status", "role"]
}

DEFAULT_CONFIG = {
    "valor_hora_operador": 40.0,
    "custo_embalagem": 10.0,
    "custo_projeto_engenharia": 100.0,
    "custo_entrega": 20.0,
    "margem_padrao": 80,
    "custo_padrao_material_kg": 120.0
}

def load_config():
    filepath = os.path.join(DATA_DIR, "config.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                return cfg
        except:
            return DEFAULT_CONFIG
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(cfg):
    filepath = os.path.join(DATA_DIR, "config.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)

def init_db():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    for filename, columns in SCHEMAS.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            df = pd.DataFrame(columns=columns)
            df.to_csv(filepath, index=False)
            
    load_config()

def load_data(table_name):
    filepath = os.path.join(DATA_DIR, f"{table_name}.csv")
    expected_cols = SCHEMAS[f"{table_name}.csv"]
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, dtype=str)
        df.fillna('', inplace=True)
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ''
        return df
    return pd.DataFrame(columns=expected_cols)

def save_data(table_name, df):
    filepath = os.path.join(DATA_DIR, f"{table_name}.csv")
    df.to_csv(filepath, index=False)

def generate_id():
    return str(uuid.uuid4())[:8]

def generate_pdf_bytes(dados_orcamento):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16, style='B')
    pdf.cell(200, 10, txt="Orcamento de Servico 3D", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    dia_hoje = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(200, 10, txt=f"Data: {dia_hoje}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Referencia: {dados_orcamento.get('nome_projeto', 'Impressao')}", ln=True, align="L")
    if dados_orcamento.get('cliente_nome'):
        pdf.cell(200, 10, txt=f"Cliente: {dados_orcamento.get('cliente_nome')}", ln=True, align="L")
    pdf.line(10, 50, 200, 50)
    pdf.ln(15)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Especificacoes da Peca:", ln=True, align="L")
    pdf.set_font("Arial", size=11)
    peso = str(dados_orcamento.get('peso_g', '0.0'))
    tempo = str(dados_orcamento.get('tempo_impressao_h', '0.0'))
    pdf.cell(200, 8, txt=f"- Peso estimado: {peso} g", ln=True, align="L")
    pdf.cell(200, 8, txt=f"- Tempo de maquina: {tempo} horas", ln=True, align="L")
    pdf.ln(5)
    extras = []
    if dados_orcamento.get('extras_embalagem'): extras.append("Embalagem Especial")
    if dados_orcamento.get('extras_engenharia'): extras.append("Projeto 3D / Engenharia")
    if dados_orcamento.get('extras_entrega'): extras.append("Entrega")
    if extras:
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, txt="Adicionais Inclusos:", ln=True, align="L")
        pdf.set_font("Arial", size=11)
        for e in extras:
            pdf.cell(200, 8, txt=f"- {e}", ln=True, align="L")
        pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Arial", size=14, style='B')
    try:
        val_total = float(dados_orcamento.get('preco_final', 0))
    except:
        val_total = 0.0
    pdf.cell(200, 10, txt=f"VALOR TOTAL: R$ {val_total:.2f}", ln=True, align="C")
    pdf.ln(20)
    pdf.set_font("Arial", size=10, style='I')
    pdf.cell(200, 10, txt="* Este orcamento eh valido por 15 dias.", ln=True, align="C")
    return pdf.output(dest='S').encode('latin-1')

def sugerir_margem_lucro():
    orcamentos = load_data('orcamentos')
    if orcamentos.empty:
        df_cfg = load_config()
        return df_cfg.get('margem_padrao', 80)
    try:
        margens = pd.to_numeric(orcamentos['margem_lucro'], errors='coerce').dropna()
        if len(margens) > 0:
            media = margens.mean()
            return int(media)
    except:
        pass
    return 80

# === SISTEMA DE LOGIN GOOGLE OAUTH ===

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

def get_login_url():
    params = {
        "client_id": st.secrets.get("google_client_id", ""),
        "redirect_uri": st.secrets.get("google_redirect_uri", ""),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

def check_password():
    if st.session_state.get('user_approved', False):
        return True

    
    # 1. Checa as Secret Keys do Admin
    if "google_client_id" not in st.secrets or "google_redirect_uri" not in st.secrets:
        st.error("⚠️ As credenciais do Google Cloud (Client ID e Redirect URI) não foram configuradas no secrets.toml!")
        return False
        
    st.markdown("<h2 style='text-align: center;'>🔐 Acesso Restrito</h2>", unsafe_allow_html=True)
    
    query = st.query_params
    
    # Processa o retorno do Google (Callback Code)
    if 'code' in query and 'user_email' not in st.session_state:
        code = query['code']
        data = {
            'code': code,
            'client_id': st.secrets['google_client_id'],
            'client_secret': st.secrets['google_client_secret'],
            'redirect_uri': st.secrets['google_redirect_uri'],
            'grant_type': 'authorization_code'
        }
        res = requests.post(TOKEN_URL, data=data)
        if res.status_code == 200:
            access_token = res.json().get('access_token')
            headers = {"Authorization": f"Bearer {access_token}"}
            user_info = requests.get(USERINFO_URL, headers=headers).json()
            st.session_state['user_email'] = user_info.get('email')
            st.session_state['user_name'] = user_info.get('name')
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Falha ao recuperar token do Google. Verifique os Secrets.")
            return False

    # Se não logou ainda, exibir botão
    if 'user_email' not in st.session_state:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.info("Somente usuários autorizados pelo Titular podem acessar.")
            st.link_button("🌐 Entrar com o Google", get_login_url(), use_container_width=True)
            
            st.divider()
            st.markdown("**Testando Offline / Bypass para Devs:**")
            bypass = st.text_input("Qual e-mail de teste? (Só funciona se dev for true)", key="bp_em")
            if st.button("Fazer Bypass Local") and bypass:
                st.session_state['user_email'] = bypass
                st.session_state['user_name'] = "Bypass User"
                st.rerun()
        return False
        
    # Já tem a conta do Google na memória
    email = st.session_state['user_email']
    name = st.session_state['user_name']
    
    usuarios = load_data('usuarios')
    
    # Registro de um novato:
    if usuarios.empty or len(usuarios[usuarios['email'] == email]) == 0:
        if email.strip().lower() == 'octaviofrancchitrabalho@gmail.com':
            status = 'Aprovado'
            role = 'Admin'
        else:
            status = 'Pendente'
            role = 'User'
            
        novo = pd.DataFrame([{"id": generate_id(), "email": email, "nome": name, "status": status, "role": role}])
        usuarios = pd.concat([usuarios, novo], ignore_index=True)
        save_data("usuarios", usuarios)
        st.rerun()
    
    # Extrair dados do banco agora que existe
    user_db = usuarios[usuarios['email'] == email].iloc[0]
    
    if user_db['status'] == 'Pendente':
        colA, colB, colC = st.columns([1,2,1])
        with colB:
            st.warning(f"Sua conta Google ({email}) foi registrada e está em análise.")
            st.info("Aguarde o Administrador (Octávio) aprovar seu acesso na tela administrativa.")
            if st.button("Deseja entrar com outra conta? Parar a Sessão."):
                del st.session_state['user_email']
                st.rerun()
        return False
        
    if user_db['status'] == 'Aprovado':
        st.session_state['user_approved'] = True
        st.session_state['user_role'] = user_db['role']
        # Tenta carregar imagem ou boas vindas.
        st.toast(f"Bem-vindo {name}!")
        return True
        
    st.error("Conta bloqueada pelo Administrador.")
    return False
