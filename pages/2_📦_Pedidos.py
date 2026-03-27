import streamlit as st
import pandas as pd
from utils import load_data, save_data, generate_id, generate_pdf_bytes, load_config
from datetime import datetime
import urllib.parse

st.set_page_config(page_title="Central de Pedidos", layout="wide", page_icon="📦")

from utils import check_password
if not check_password():
    st.stop()


st.title("📦 Central de Pedidos")
st.markdown("Selecione um pedido existente para gerenciar todos os seus aspectos (cliente, orçamento, máquina, estoque e agenda).")

# Carregar dados
pedidos = load_data("pedidos")
clientes = load_data("clientes")
orcamentos = load_data("orcamentos")
equipamentos = load_data("equipamentos")
config_obj = load_config()

# ---- CRIAR NOVO PEDIDO ----
with st.expander("➕ Clicou aqui para Abrir um Novo Pedido (Do Zero)"):
    if clientes.empty:
        st.warning("Cadastre um cliente antes!")
    else:
        with st.form("form_novo_pedido"):
            cliente_sel = st.selectbox("Cliente do Pedido", clientes['nome'].tolist())
            nome_p = st.text_input("Qual a Peça / Serviço?")
            prazo = st.date_input("Prazo final")
            
            if st.form_submit_button("Gerar Pedido em Branco"):
                id_cliente = clientes[clientes['nome'] == cliente_sel]['id'].values[0]
                n_id = generate_id()
                prazo_str = prazo.strftime("%Y-%m-%d")
                link_agenda = f"https://calendar.google.com/calendar/r/eventedit?text={urllib.parse.quote(nome_p)}&dates={prazo.strftime('%Y%m%d')}/{prazo.strftime('%Y%m%d')}"
                
                novo = pd.DataFrame([{"id": n_id, "id_cliente": id_cliente, "nome_arquivo": nome_p, "id_orcamento": "", "prazo_entrega": prazo_str, "status": "Em Espera", "link_agenda": link_agenda}])
                pedidos = pd.concat([pedidos, novo], ignore_index=True)
                save_data("pedidos", pedidos)
                st.success("Pedido inicializado! Selecione-o abaixo para continuar de onde parou.")
                st.rerun()

st.markdown("---")

if pedidos.empty:
    st.info("Nenhum pedido ativo no momento.")
else:
    # Seleção de Pedido Ativo
    pedidos_view = pedidos.copy()
    # Merge com clientes para mostrar nome legalzinho no selectbox
    pedidos_view = pedidos_view.merge(clientes[['id', 'nome']], left_on='id_cliente', right_on='id', how='left')
    lista_opcoes = [f"[{row['status']}] {row['nome_arquivo']} ({row['nome']})" for _, row in pedidos_view.iterrows()]
    
    pedido_select = st.selectbox("🔍 Selecionar Pedido para Trabalhar:", lista_opcoes)
    idx_selecionado = lista_opcoes.index(pedido_select)
    pedido_ativo = pedidos.iloc[idx_selecionado]
    id_pedido = pedido_ativo['id']
    
    st.markdown(f"## Painel do Pedido: {pedido_ativo['nome_arquivo']}")
    
    # HUB DE ABAS
    tab_resumo, tab_cliente, tab_orcamento, tab_producao, tab_cronograma = st.tabs([
        "📊 Resumo", "👥 Cliente", "💵 Orçamento / PDF", "🖨️ Produção (Stock)", "📅 Cronograma"
    ])
    
    # 1. RESUMO
    with tab_resumo:
        colA, colB = st.columns(2)
        novo_st = colA.selectbox("Mudar Status do Pedido:", ["Em Espera", "Aprovado", "Imprimindo", "Concluído", "Cancelado"], 
                                 index=["Em Espera", "Aprovado", "Imprimindo", "Concluído", "Cancelado"].index(pedido_ativo['status']))
        
        if novo_st != pedido_ativo['status']:
            pedidos.loc[pedidos['id'] == id_pedido, 'status'] = novo_st
            save_data("pedidos", pedidos)
            st.rerun()
            
        colB.markdown(f"**Prazo Oficial:** `{pedido_ativo['prazo_entrega']}`")
        colB.markdown(f"**Link Agenda:** [Salvar no Google Calendar]({pedido_ativo['link_agenda']})")
        
    # 2. CLIENTE
    with tab_cliente:
        cli_ped = clientes[clientes['id'] == pedido_ativo['id_cliente']].iloc[0]
        st.write(f"**Nome:** {cli_ped['nome']}")
        st.write(f"**Telefone/WhatsApp:** {cli_ped['telefone']}")
        st.write(f"**Email:** {cli_ped['email']}")
        link_zap = f"https://wa.me/?text=Ola+{urllib.parse.quote(cli_ped['nome'])}"
        st.link_button("Conversar no WhatsApp", link_zap)

    # 3. ORÇAMENTO & PDF
    with tab_orcamento:
        st.info("Aqui você calcula e crava o preço desta peça.")
        # Se ja tiver um orcamento para esse pedido, puxar. Senão formulário branco.
        orc_existente = orcamentos[orcamentos['id_pedido'] == id_pedido]
        
        if not orc_existente.empty:
            st.success("Orçamento já salvo para este pedido!")
            dados_o = orc_existente.iloc[-1].to_dict() # pega o ultimo salvamento
            
            st.metric("Preço Final", f"R$ {float(dados_o.get('preco_final', 0)):.2f}")
            st.write(f"Margem de lucro aplicada: {dados_o.get('margem_lucro', '0')}%")
            
            # Gerar PDF Real Button
            # Pass data for PDF inside dict
            dados_pdf = {
                "nome_projeto": pedido_ativo['nome_arquivo'],
                "cliente_nome": cli_ped['nome'],
                "peso_g": dados_o.get('peso_g'),
                "tempo_impressao_h": dados_o.get('tempo_impressao_h'),
                "preco_final": dados_o.get('preco_final'),
                "extras_embalagem": dados_o.get('extras_embalagem'),
                "extras_engenharia": dados_o.get('extras_engenharia'),
                "extras_entrega": dados_o.get('extras_entrega'),
            }
            
            pdf_bytes = generate_pdf_bytes(dados_pdf)
            st.download_button(
                label="⬇️ Baixar PDF do Orçamento",
                data=pdf_bytes,
                file_name=f"Orcamento_{pedido_ativo['nome_arquivo'].replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            
        else:
            # Form para gerar o primeiro orçamento vinculado
            with st.form("form_orc_hub"):
                col1, col2 = st.columns(2)
                peso_g = col1.number_input("Peso estimado da peça (g)", min_value=0.0, step=10.0)
                tempo_h = col1.number_input("Tempo na Máquina (Horas)", min_value=0.0, step=0.5)
                tempo_trab = col1.number_input("Seu Tempo gasto limpando (Hrs)", value=1.0, step=0.5)
                
                if not equipamentos.empty:
                    eq_nome = col2.selectbox("Qual máquina vai usar?", equipamentos['nome'].tolist())
                    eq_hora_deprec = float(equipamentos[equipamentos['nome'] == eq_nome]['custo_hora_depreciacao'].values[0])
                else:
                    st.warning("Sem máq. no banco!")
                    eq_hora_deprec = 0
                    
                st.write("Adicionais:")
                ex_emb = st.checkbox("Embalagem Premium")
                ex_eng = st.checkbox("Projeto/Modelagem 3D")
                ex_ent = st.checkbox("Entrega via Motoboy")
                
                # O valor padrao sugerido vem das configuracoes!
                margem_sugerida = float(config_obj.get("margem_padrao", 80.0))
                margem = st.slider("Margem (%)", 10.0, 300.0, margem_sugerida)
                
                if st.form_submit_button("Aprovar Orçamento e Salvar no Pedido"):
                    # Calc
                    custo_material = (peso_g / 1000) * float(config_obj.get('custo_padrao_material_kg', 120))
                    custo_maq = tempo_h * eq_hora_deprec
                    custo_hum = tempo_trab * float(config_obj.get('valor_hora_operador', 40))
                    
                    extra_val = 0
                    if ex_emb: extra_val += float(config_obj.get('custo_embalagem', 10))
                    if ex_eng: extra_val += float(config_obj.get('custo_projeto_engenharia', 100))
                    if ex_ent: extra_val += float(config_obj.get('custo_entrega', 20))
                    
                    base_price = custo_material + custo_maq + custo_hum + extra_val
                    total = base_price * (1 + (margem / 100))
                    
                    n_orc = pd.DataFrame([{
                        "id": generate_id(),
                        "nome_projeto": pedido_ativo['nome_arquivo'],
                        "id_pedido": id_pedido,
                        "peso_g": peso_g,
                        "tempo_impressao_h": tempo_h,
                        "tempo_trabalho_h": tempo_trab,
                        "extras_embalagem": ex_emb,
                        "extras_engenharia": ex_eng,
                        "extras_entrega": ex_ent,
                        "margem_lucro": margem,
                        "custo_total": base_price,
                        "preco_final": total
                    }])
                    orcamentos = pd.concat([orcamentos, n_orc], ignore_index=True)
                    save_data("orcamentos", orcamentos)
                    
                    # Atualiza pedido
                    pedidos.loc[pedidos['id'] == id_pedido, 'status'] = 'Aprovado'
                    save_data("pedidos", pedidos)
                    
                    st.success("Calculado!")
                    st.rerun()

    # 4. PRODUÇÃO & ESTOQUE
    with tab_producao:
        st.write("Em qual estágio a impressão está?")
        st.info("Puxaremos do 'Estoque' em breve para remover do seu inventário os gramas usados!")
        
    # 5. CRONOGRAMA
    with tab_cronograma:
        st.write(f"Prazo deste item específico: {pedido_ativo['prazo_entrega']}")
        st.write("Abra o App de Cronograma no menu esquerdo para ter a visão geral de sua linha do tempo de todos!")
