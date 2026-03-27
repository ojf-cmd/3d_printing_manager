import os
import json
import uuid
import pandas as pd
from fpdf import FPDF
from datetime import datetime

DATA_DIR = "data"

SCHEMAS = {
    "clientes.csv": ["id", "nome", "telefone", "email"],
    "equipamentos.csv": ["id", "nome", "tipo", "preco_compra", "vida_util_horas", "custo_hora_depreciacao"],
    "estoque.csv": ["id", "categoria", "nome_item", "quantidade", "custo_unitario", "cor"],
    "pedidos.csv": ["id", "id_cliente", "nome_arquivo", "id_orcamento", "prazo_entrega", "status", "link_agenda"],
    "orcamentos.csv": ["id", "nome_projeto", "id_pedido", "peso_g", "tempo_impressao_h", 
                       "tempo_trabalho_h", "custo_total", "preco_final", "margem_lucro"],
    "projetos.csv": ["id", "nome", "id_cliente", "descricao", "status"]
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
    
    # Init config
    load_config()

def load_data(table_name):
    filepath = os.path.join(DATA_DIR, f"{table_name}.csv")
    expected_cols = SCHEMAS[f"{table_name}.csv"]
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, dtype=str)
        df.fillna('', inplace=True)
        
        # Correção automática de versão: Se o app atualizou e tem colunas novas, adicione-as!
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
    """
    Gera um PDF na memória usando FPDF e retorna os bytes para download.
    dados_orcamento é um dict contendo detalhes como nome, total, etc.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16, style='B')
    
    # Title
    pdf.cell(200, 10, txt="Orcamento de Servico 3D", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    dia_hoje = datetime.now().strftime("%d/%m/%Y")
    
    # Header Info
    pdf.cell(200, 10, txt=f"Data: {dia_hoje}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Referencia: {dados_orcamento.get('nome_projeto', 'Impressao')}", ln=True, align="L")
    if dados_orcamento.get('cliente_nome'):
        pdf.cell(200, 10, txt=f"Cliente: {dados_orcamento.get('cliente_nome')}", ln=True, align="L")
        
    pdf.line(10, 50, 200, 50)
    pdf.ln(15)
    
    # Specs Table / List
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Especificacoes da Peca:", ln=True, align="L")
    pdf.set_font("Arial", size=11)
    
    peso = str(dados_orcamento.get('peso_g', '0.0'))
    tempo = str(dados_orcamento.get('tempo_impressao_h', '0.0'))
    pdf.cell(200, 8, txt=f"- Peso estimado: {peso} g", ln=True, align="L")
    pdf.cell(200, 8, txt=f"- Tempo de maquina: {tempo} horas", ln=True, align="L")
    pdf.ln(5)
    
    # Extras
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
        
    # Total Box
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
    pdf.cell(200, 10, txt="* Este orcamento eh valido por 15 dias. Os valores podem sofrer alteracoes sem aviso previo.", ln=True, align="C")
    
    # Return directly as byte array string that streamlit download understands
    return pdf.output(dest='S').encode('latin-1')

def sugerir_margem_lucro():
    """Lógica super simples que olha os orçamentos e pega a média das margens já aplicadas."""
    orcamentos = load_data('orcamentos')
    if orcamentos.empty:
        df_cfg = load_config()
        return df_cfg.get('margem_padrao', 80)
        
    try:
        # Tenta pegar apenas orcamentos que fecharam, se não hover status filtra todos.
        # Por enquanto faz a média geral dos que estão lá.
        margens = pd.to_numeric(orcamentos['margem_lucro'], errors='coerce').dropna()
        if len(margens) > 0:
            media = margens.mean()
            return int(media)
    except:
        pass
    return 80

import streamlit as st
import hmac

def check_password():
    """Valida se o usuário tem a senha mestre. Retorna True se logged in."""
    def password_entered():
        if hmac.compare_digest(st.session_state["user_password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["user_password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("<h2 style='text-align: center;'>🔒 Acesso Restrito ao Administrador</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.text_input("Digite sua Senha Mestra", type="password", key="user_password", on_change=password_entered)
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 Senha incorreta. Tente novamente.")
    
    return False
