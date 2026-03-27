import streamlit as st
from utils import init_db

st.set_page_config(
    page_title="3D Printing Manager",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa o banco de dados (Cria os CSVs caso não existam)
init_db()

st.title("🖨️ 3D Printing Manager")
st.markdown("---")
st.markdown("### Bem-vindo ao sistema de gerenciamento da sua empresa!")
st.info("👈 Utilize o menu lateral esquerdo para navegar pelas ferramentas.")

col1, col2, col3 = st.columns(3)
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/3067/3067425.png", width=120)
    st.markdown("**Organize Pedidos**")
with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=120)
    st.markdown("**Gerencie Orçamentos**")
with col3:
    st.image("https://cdn-icons-png.flaticon.com/512/610/610128.png", width=120)
    st.markdown("**Controle Insumos**")
