import streamlit as st
import pandas as pd
from utils import load_data, save_data, check_password

st.set_page_config(page_title="Gestão de Usuários", layout="wide", page_icon="🔑")

if not check_password():
    st.stop()

# Proteção dupla: Apenas Admins enxergam a página real!
if st.session_state.get('user_role') != 'Admin':
    st.error("🚫 Apenas o Administrador Mestre tem acesso à Gestão de Usuários.")
    st.stop()
    
st.title("🔑 Autorização de Funcionários / Sócios")
st.markdown("Nesta aba, você **Octávio (Admin)** tem o poder de liberar acesso total para os e-mails do Google de outras pessoas na sua oficina.")

usuarios = load_data('usuarios')

# Exibe Pendentes
st.subheader("⚠️ Solicitações Pendentes (Novos Logins)")
pendentes = usuarios[usuarios['status'] == 'Pendente']

if pendentes.empty:
    st.info("Ninguém está na fila de aprovação no momento.")
else:
    for index, row in pendentes.iterrows():
        col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
        col1.markdown(f"**E-mail:** `{row['email']}`")
        col2.markdown(f"**Nome Conta:** {row['nome']}")
        
        if col3.button("✅ Aprovar (Acesso Total)", key=f"apr_{row['id']}"):
            usuarios.loc[usuarios['id'] == row['id'], 'status'] = 'Aprovado'
            save_data('usuarios', usuarios)
            st.success("Usuário aprovado!")
            st.rerun()
            
        if col4.button("❌ Recusar", key=f"rec_{row['id']}"):
            usuarios.loc[usuarios['id'] == row['id'], 'status'] = 'Bloqueado'
            save_data('usuarios', usuarios)
            st.success("Bloqueado!")
            st.rerun()

st.divider()

# Exibe Aprovados e Bloqueados
st.subheader("👥 Equipe Aprovada e Status")

todas_as_contas = usuarios.copy()
# Botão remover
if not todas_as_contas.empty:
    for index, row in todas_as_contas.iterrows():
        if row['email'] == 'octaviofrancchitrabalho@gmail.com':
            continue # Ignora sua propria conta pro menu de gerenciamento, pois vc é o boss.
            
        st.write(f"🔹 **{row['nome']}** (`{row['email']}`) - Regra: **{row['role']}** | Status: **{row['status']}**")
        
        colA, colB = st.columns(2)
        n_st = colA.selectbox("Status", ["Aprovado", "Bloqueado", "Pendente"], index=["Aprovado", "Bloqueado", "Pendente"].index(row['status']), key=f"mod_st_{row['id']}")
        n_rl = colB.selectbox("Permissão (Role)", ["User", "Admin"], index=["User", "Admin"].index(row['role']), key=f"mod_rl_{row['id']}")
        
        if n_st != row['status'] or n_rl != row['role']:
            usuarios.loc[usuarios['id'] == row['id'], 'status'] = n_st
            usuarios.loc[usuarios['id'] == row['id'], 'role'] = n_rl
            save_data('usuarios', usuarios)
            st.rerun()
        st.write("---")
