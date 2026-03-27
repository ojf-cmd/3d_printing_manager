import streamlit as st
import pandas as pd
from utils import load_data, save_data, generate_id

st.set_page_config(page_title="Estoque", layout="wide", page_icon="🏭")

st.title("🏭 Controle de Estoque de Insumos")

estoque = load_data("estoque")

with st.expander("📦 Entrada de Insumo / Fornecedor"):
    with st.form("form_estoque"):
        c1, c2, c3 = st.columns(3)
        categoria = c1.selectbox("Categoria", ["Filamento (Rolo)", "Resina (Garrafa)", "Peça de Reposição (Nozzle, etc)", "Insumo Geral"])
        nome = c1.text_input("Qual material? (Ex: PLA Preto 1kg)")
        cor = c2.text_input("Cor Predominante")
        
        qtde = c2.number_input("Quantidade", min_value=1, step=1, value=1)
        custo = c3.number_input("Custo Unitário Pago (R$)", step=10.0, value=100.0)
        
        if st.form_submit_button("Confirmar Entrada"):
            novo_est = pd.DataFrame([{
                "id": generate_id(),
                "categoria": categoria,
                "nome_item": nome,
                "cor": cor,
                "quantidade": qtde,
                "custo_unitario": custo
            }])
            estoque = pd.concat([estoque, novo_est], ignore_index=True)
            save_data("estoque", estoque)
            st.success("Estoque Adicionado!")
            st.rerun()

st.subheader("Lista de Insumos Atuais")
st.dataframe(estoque, hide_index=True, use_container_width=True)
