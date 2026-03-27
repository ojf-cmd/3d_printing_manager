import streamlit as st
import pandas as pd
from utils import load_data
import plotly.express as px

st.set_page_config(page_title="Dashboard", layout="wide", page_icon="📊")

from utils import check_password
if not check_password():
    st.stop()


st.title("📊 Dashboard")
st.markdown("Visão geral do sistema de Impressão 3D.")

# Carregar dados
pedidos = load_data("pedidos")
orcamentos = load_data("orcamentos")
clientes = load_data("clientes")

if not pedidos.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    total_pedidos = len(pedidos)
    pendentes = len(pedidos[pedidos['status'] == 'Em Espera'])
    aprovados = len(pedidos[pedidos['status'] == 'Aprovado'])
    total_clientes = len(clientes)
    
    col1.metric("📦 Total de Pedidos", total_pedidos)
    col2.metric("⏳ Em Espera", pendentes)
    col3.metric("✅ Aprovados", aprovados)
    col4.metric("👥 Clientes", total_clientes)

    st.markdown("---")
    
    # Gráficos simples se houver orçamentos vinculados
    if not orcamentos.empty:
        # Conversão para números
        orcamentos['preco_final'] = pd.to_numeric(orcamentos['preco_final'], errors='coerce').fillna(0)
        faturamento_potencial = orcamentos['preco_final'].sum()
        
        st.subheader("💰 Resumo Financeiro")
        st.metric("Faturamento Potencial Baseado em Orçamentos", f"R$ {faturamento_potencial:,.2f}")
        
    st.subheader("Situação dos Pedidos")
    fig = px.pie(pedidos, names='status', title='Divisão de Pedidos por Status', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Ainda não há pedidos cadastrados. Comece cadastrando clientes e criando orçamentos/pedidos!")
