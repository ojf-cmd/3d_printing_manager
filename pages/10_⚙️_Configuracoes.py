import streamlit as st
from utils import load_config, save_config

st.set_page_config(page_title="Configurações e Precisão", layout="wide", page_icon="⚙️")

from utils import check_password
if not check_password():
    st.stop()


st.title("⚙️ Configurador de Variáveis")
st.markdown("Altere os valores padrão do laboratório abaixo. Todas as abas de Orçamento e Simulação puxarão esses 'impostos' globais invisíveis e garantirão máxima precisão.")

config_obj = load_config()

with st.form("settings_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Custos Base")
        vh = st.number_input("Sua Hora Fixa de Trabalho (Fatiamento/Limpeza) (R$/h)", value=float(config_obj.get('valor_hora_operador', 40)), step=5.0)
        cmat = st.number_input("Custo Padrão do Carretel (1KG) (R$)", value=float(config_obj.get('custo_padrao_material_kg', 120)), step=10.0)
        margem = st.number_input("Margem de Lucro Estática Padrão (%)", value=float(config_obj.get('margem_padrao', 80)), step=10.0)
        
    with col2:
        st.subheader("Taxas de Extras (Checkbox)")
        c_emb = st.number_input("Lucro por Adicionar Embalagem Especial (R$)", value=float(config_obj.get('custo_embalagem', 10)), step=5.0)
        c_proj = st.number_input("Lucro ou Terceirização de Engenharia (R$)", value=float(config_obj.get('custo_projeto_engenharia', 100)), step=50.0)
        c_ent = st.number_input("Valor Cobrado Pela Entrega Motoboy (R$)", value=float(config_obj.get('custo_entrega', 20)), step=5.0)
        
    if st.form_submit_button("Salvar Regras da Impressão"):
        novo = {
            "valor_hora_operador": vh,
            "custo_padrao_material_kg": cmat,
            "margem_padrao": margem,
            "custo_embalagem": c_emb,
            "custo_projeto_engenharia": c_proj,
            "custo_entrega": c_ent
        }
        save_config(novo)
        st.success("Tudo salvo! Seu Hub de Pedidos passará a usar estes novos parâmetros na ponta do lápis!")
