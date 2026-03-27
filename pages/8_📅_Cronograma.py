import streamlit as st
import pandas as pd
from utils import load_data
from datetime import datetime

st.set_page_config(page_title="Cronograma", layout="wide", page_icon="📅")

from utils import check_password
if not check_password():
    st.stop()


st.title("📅 Cronograma de Entregas")
st.markdown("Veja apenas os pedidos que foram aprovados e acompanhe de perto sua fila de impressão!")

pedidos = load_data("pedidos")
clientes = load_data("clientes")

if not pedidos.empty:
    # merge com clientes pra pegar o nome
    df_merged = pedidos.merge(clientes[['id', 'nome']], left_on='id_cliente', right_on='id', how='left')
    aprovados = df_merged[df_merged['status'].isin(['Aprovado', 'Em Andamento', 'Em Impressão'])]
    
    if aprovados.empty:
        st.success("🥳 Sem pedidos aprovados na calha. Tudo tranquilo!")
    else:
        # Converter prazo_entrega string para datetime
        aprovados['prazo_entrega'] = pd.to_datetime(aprovados['prazo_entrega'])
        aprovados = aprovados.sort_values(by='prazo_entrega')
        
        for index, row in aprovados.iterrows():
            st.markdown(f"### 🗓️ {row['prazo_entrega'].strftime('%d de %B de %Y')}")
            col1, col2, col3 = st.columns([1,3,1])
            with col1:
                st.info(f"📁 {row['nome_arquivo']}")
            with col2:
                st.markdown(f"**Cliente:** {row['nome']}")
                st.markdown(f"**Status Atual:** `{row['status']}`")
            with col3:
                st.link_button("Modificar no Google Calendar", row['link_agenda'])
            st.divider()
else:
    st.info("Nenhum pedido cadastrado no momento.")
