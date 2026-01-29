import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- OCULTAR ELEMENTOS PADRÃO DO STREAMLIT ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
conn = sqlite3.connect('biblioteca.db', check_same_thread=False)
c = conn.cursor()

def criar_tabelas():
    # O conteúdo da função precisa ter um recuo (4 espaços)
    c.execute('''CREATE TABLE IF NOT EXISTS emprestimos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nome_pessoa TEXT, 
                  livro TEXT, 
                  data_retirada TEXT, 
                  status TEXT)''')
    conn.commit()

# Chama a função para garantir que a tabela existe
criar_tabelas()

# --- INTERFACE ---
st.title("📚 Sistema de Biblioteca Inteligente")

menu = ["Retirar Livro", "Devolver Livro", "Histórico Geral"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Retirar Livro":
    st.subheader("Novo Empréstimo")
    
    # Inputs devem estar dentro do bloco 'if choice...'
    nome = st.text_input("Nome da Pessoa:").strip().title()
    livro = st.text_input("Nome do Livro:")
    
    if st.button("Confirmar Retirada"):
        if nome and livro:
            # Verifica quantos livros a pessoa tem no momento
            c.execute("SELECT COUNT(*) FROM emprestimos WHERE nome_pessoa = ? AND status = 'Pendente'", (nome,))
            livros_atuais = c.fetchone()[0]
            
            if livros_atuais >= 2:
                st.error(f"❌ {nome} já possui {livros_atuais} livros. Devolva um antes de retirar outro!")
            else:
                data_agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                c.execute("INSERT INTO emprestimos (nome_pessoa, livro, data_retirada, status) VALUES (?, ?, ?, ?)",
                          (nome, livro, data_agora, 'Pendente'))
                conn.commit()
                st.success(f"✅ Empréstimo de '{livro}' registrado para {nome} às {data_agora}!")
        else:
            st.warning("Por favor, preencha todos os campos.")

elif choice == "Devolver Livro":
    st.subheader("Registrar Devolução")
    nome_busca = st.text_input("Digite o nome da pessoa para devolver:").strip().title()
    
    if nome_busca:
        c.execute("SELECT id, livro, data_retirada FROM emprestimos WHERE nome_pessoa = ? AND status = 'Pendente'", (nome_busca,))
        livros_pendentes = c.fetchall()
        
        if livros_pendentes:
            for item in livros_pendentes:
                # O botão deve ser único para cada livro (usando key=item[0])
                if st.button(f"Devolver: {item[1]} (Retirado em: {item[2]})", key=item[0]):
                    c.execute("UPDATE emprestimos SET status = 'Devolvido' WHERE id = ?", (item[0],))
                    conn.commit()
                    st.rerun()
        else:
            st.info("Esta pessoa não possui livros pendentes.")

elif choice == "Histórico Geral":
    st.subheader("Todos os Registros")
    # A leitura do DataFrame deve estar dentro deste bloco
    df = pd.read_sql_query("SELECT nome_pessoa as Nome, livro as Livro, data_retirada as 'Data/Hora', status as Status FROM emprestimos", conn)
    st.dataframe(df, use_container_width=True)