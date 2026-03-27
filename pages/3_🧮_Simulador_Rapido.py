import streamlit as st
import pandas as pd
from utils import load_config, generate_pdf_bytes, load_data, sugerir_margem_lucro

st.set_page_config(page_title="Simulador Rápido", layout="wide", page_icon="🧮")

from utils import check_password
if not check_password():
    st.stop()


st.title("🧮 Simulador Rápido de Preço")
st.markdown("Use esta ferramenta para simular preços instantaneamente para curiosos no balcão/WhatsApp sem compromisso, e gere o PDF!")

config_obj = load_config()
equipamentos = load_data("equipamentos")

col1, col2 = st.columns(2)

with col1:
    peso = st.number_input("Peso estimado (g)", value=50.0, step=10.0)
    tempo_imp = st.number_input("Tempo estimado na máquina (h)", value=2.0, step=0.5)
    
    if not equipamentos.empty:
        eq_nome = st.selectbox("Qual máquina?", equipamentos['nome'].tolist())
        eq_hora_deprec = float(equipamentos[equipamentos['nome'] == eq_nome]['custo_hora_depreciacao'].values[0])
    else:
        st.warning("Adicione uma máquina nas configurações para rodar a depreciação!")
        eq_hora_deprec = 0
    
with col2:
    tempo_seu = st.number_input("Tempo Operador Limpando (h)", value=0.5, step=0.5)
    
    # A IA sugere!
    sugestao = sugerir_margem_lucro()
    st.info(f"💡 Dica de Sucesso: Historicamente você fatura com ~{sugestao}% de margem!")
    margem = st.slider("Margem Aplicada (%)", 10.0, 300.0, float(sugestao))

# CALCULAR NA HORA
st.markdown("---")
custo_material = (peso / 1000) * float(config_obj.get('custo_padrao_material_kg', 120))
custo_maq = tempo_imp * eq_hora_deprec
custo_hum = tempo_seu * float(config_obj.get('valor_hora_operador', 40))

base = custo_material + custo_maq + custo_hum
final = base * (1 + (margem / 100))

c_a, c_b, c_c = st.columns(3)
c_a.metric("Custo Fixo Liso", f"R$ {base:.2f}")
c_b.metric("Seu Lucro", f"R$ {final - base:.2f}")
c_c.metric("Preço ao Cliente", f"R$ {final:.2f}")

st.divider()

# GERAR PDF EM BRANCO (SEM COMPROMISSO)
dados_fake = {
    "nome_projeto": "Orcamento Simulacao",
    "cliente_nome": "Cliente Balcao / Avulso",
    "peso_g": peso,
    "tempo_impressao_h": tempo_imp,
    "preco_final": final,
    "extras_embalagem": False,
    "extras_engenharia": False,
    "extras_entrega": False
}

pdf_simulacao = generate_pdf_bytes(dados_fake)

st.download_button(
    "⬇️ Baixar PDF do Orçamento Avalista", 
    pdf_simulacao, 
    "Orcamento_Simulado.pdf", 
    "application/pdf",
    use_container_width=True
)

st.success("Se o cliente gostou, não esqueça de criar um 'Novo Pedido' na Central e fechar a compra com esses números!")
