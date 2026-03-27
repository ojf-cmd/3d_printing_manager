import streamlit as st
import pandas as pd
from utils import load_data, save_data, generate_id

st.set_page_config(page_title="Clientes", layout="wide", page_icon="👥")

from utils import check_password
if not check_password():
    st.stop()


st.title("👥 Agenda de Clientes")

clientes = load_data("clientes")

with st.expander("👤 Novo Cadastro de Cliente"):
    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome do Cliente / Empresa")
        telefone = col2.text_input("WhatsApp / Telefone (+55...)")
        email = st.text_input("E-mail (Para evios de Nota/PDF)")
        
        sub = st.form_submit_button("Salvar")
        if sub and nome:
            novo_id = generate_id()
            novo_cli = pd.DataFrame([{"id": novo_id, "nome": nome, "telefone": telefone, "email": email}])
            clientes = pd.concat([clientes, novo_cli], ignore_index=True)
            save_data("clientes", clientes)
            st.success("Cliente salvo!")
            st.rerun()

st.subheader("Lista de Clientes Cadastrados")
st.dataframe(clientes, use_container_width=True, hide_index=True)
