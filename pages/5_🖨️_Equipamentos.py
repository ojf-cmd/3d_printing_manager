import streamlit as st
import pandas as pd
from utils import load_data, save_data, generate_id

st.set_page_config(page_title="Equipamentos", layout="wide", page_icon="🖨️")

from utils import check_password
if not check_password():
    st.stop()


st.title("🖨️ Máquinas e Depreciação")
st.markdown("Cadastre suas impressoras 3D, Gravadoras a Laser e Scanners. O sistema calculará o **Custo de Desgaste por Hora** para você nunca levar prejuízo pela depreciação do equipamento.")

equipamentos = load_data("equipamentos")

with st.expander("➕ Adicionar Máquina"):
    with st.form("form_equip"):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome/Modelo da Máquina (Ex: Ender 3 S1 Pro)")
        tipo = col1.selectbox("Tipo", ["Impressora FDM", "Impressora Resina SLA", "Gravadora Laser", "Scanner 3D", "Outro"])
        
        preco_compra = col2.number_input("Preço de Compra (R$)", value=2500.0, step=100.0)
        vida_util_horas = col2.number_input("Vida Útil Estimada (Horas de Uso)", value=10000.0, step=1000.0, help="Quanto tempo você acha que a máquina imprime bem antes de ter que trocar/jogar fora. (Padrão: 8000 a 10000 hrs)")
        
        if st.form_submit_button("Salvar Equipamento"):
            if nome and preco_compra > 0 and vida_util_horas > 0:
                custo_hora_deprec = round(preco_compra / vida_util_horas, 4)
                
                novo = pd.DataFrame([{
                    "id": generate_id(),
                    "nome": nome,
                    "tipo": tipo,
                    "preco_compra": preco_compra,
                    "vida_util_horas": vida_util_horas,
                    "custo_hora_depreciacao": custo_hora_deprec
                }])
                
                equipamentos = pd.concat([equipamentos, novo], ignore_index=True)
                save_data("equipamentos", equipamentos)
                st.success(f"Equipamento salvo! Custo de Depreciação: R$ {custo_hora_deprec:.2f} por hora.")
                st.rerun()

st.markdown("---")
st.subheader("📋 Suas Máquinas Cadastradas")

if not equipamentos.empty:
    st.dataframe(
        equipamentos.rename(columns={
            "nome": "Modelo", "tipo": "Categoria", "preco_compra": "Preço Pago (R$)", 
            "vida_util_horas":"Vida Útil (h)", "custo_hora_depreciacao": "Depreciação/Hora (R$)"
        }).drop(columns=['id']),
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("Você ainda não tem máquinas cadastradas.")
