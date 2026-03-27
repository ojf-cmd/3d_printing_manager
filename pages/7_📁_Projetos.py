import streamlit as st
import pandas as pd
from utils import load_data, save_data, generate_id

st.set_page_config(page_title="Projetos Especiais", layout="wide", page_icon="📁")

from utils import check_password
if not check_password():
    st.stop()


st.title("📁 Projetos")
st.markdown("Agrupe vários pedidos de peças complexas em um único 'Projeto'. Exemplo: 'Robô Seguidor de Linha'")

projetos = load_data("projetos")
clientes = load_data("clientes")

with st.expander("✨ Criar Novo Projeto"):
    with st.form("form_projetos"):
        nome_proj = st.text_input("Nome do Projeto")
        cliente = st.selectbox("Qual Cliente?", ["Nenhum (Projeto Pessoal)"] + clientes['nome'].tolist() if not clientes.empty else ["Nenhum (Projeto Pessoal)"])
        descricao = st.text_area("Descritivo", help="Coloque links de STL do Thingiverse/Printables, ideias gerais e peças necessárias.")
        
        if st.form_submit_button("Abrir Projeto"):
            if cliente != "Nenhum (Projeto Pessoal)":
                id_cliente = clientes[clientes['nome'] == cliente]['id'].values[0]
            else:
                id_cliente = "None"
                
            novo_proj = pd.DataFrame([{
                "id": generate_id(),
                "nome": nome_proj,
                "id_cliente": id_cliente,
                "descricao": descricao,
                "status": "Aberto"
            }])
            projetos = pd.concat([projetos, novo_proj], ignore_index=True)
            save_data("projetos", projetos)
            st.success("Projeto Inicializado!")
            st.rerun()

st.subheader("Lista de Projetos")
st.dataframe(projetos, use_container_width=True, hide_index=True)
