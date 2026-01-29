import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
import pytz
from oauth2client.service_account import ServiceAccountCredentials

# --- OCULTAR ELEMENTOS PADRÃO ---
st.markdown("""
    <style>
        /* Esconde o menu de 3 pontinhos e o Deploy */
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* Esconde o rodapé "Made with Streamlit" */
        footer {visibility: hidden;}
        
        /* A linha abaixo foi removida para você poder ver a setinha (>) novamente */
        /* header {visibility: hidden;} */
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM GOOGLE SHEETS ---
@st.cache_resource
def conectar_google_sheets():
    # 1. Pega os segredos brutos
    raw_creds = st.secrets["gcp_service_account"]
    
    # 2. Cria uma CÓPIA editável
    creds_dict = dict(raw_creds)
    
    # 3. Corrige a chave
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Abre a planilha (Confira o nome!)
    sheet = client.open("smartbiblio.db").sheet1 
    return sheet

# --- A LINHA QUE FALTAVA ---
# Ela chama a função acima e cria a variável 'sheet' que o resto do código usa
sheet = conectar_google_sheets()

# --- INTERFACE ---
st.title("📚 Sistema de Biblioteca (Na Nuvem)")

menu = ["Retirar Livro", "Devolver Livro", "Histórico Geral"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Retirar Livro":
    st.subheader("Novo Empréstimo")
    nome = st.text_input("Nome da Pessoa:").strip().title()
    livro = st.text_input("Nome do Livro:")
    
    if st.button("Confirmar Retirada"):
        if nome and livro:
            # Baixa todos os dados para verificar
            dados = sheet.get_all_records()
            df = pd.DataFrame(dados)
            
            # Conta quantos livros pendentes a pessoa tem
            if not df.empty:
                # Verifica se as colunas existem antes de filtrar para evitar erro de Index
                if 'Nome' in df.columns and 'Status' in df.columns:
                    pendentes = df[(df['Nome'] == nome) & (df['Status'] == 'Pendente')]
                    qtd_pendentes = len(pendentes)
                else:
                    st.error("Erro: As colunas 'Nome' e 'Status' não foram encontradas na planilha. Verifique o cabeçalho no Google Sheets.")
                    st.stop()
            else:
                qtd_pendentes = 0
            
            if qtd_pendentes >= 2:
                st.error(f"❌ {nome} já tem {qtd_pendentes} livros pendentes!")
            else:
                # Define o fuso horário de Brasília/Belém
                fuso_br = pytz.timezone('America/Sao_Paulo')
                # Pega a hora certa nesse fuso
                data_agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
                
                # Adiciona nova linha na planilha
                sheet.append_row([nome, livro, data_agora, "Pendente"])
                st.success(f"✅ Empréstimo de '{livro}' registrado!")
        else:
            st.warning("Preencha todos os campos.")

elif choice == "Devolver Livro":
    st.subheader("Registrar Devolução")
    nome_busca = st.text_input("Nome da pessoa:").strip().title()
    
    if nome_busca:
        # Pega todos os valores (incluindo cabeçalho) para achar o número da linha
        todas_linhas = sheet.get_all_values()
        
        # Filtra visualmente para o usuário
        encontrou_algum = False
        
        # Começa do índice 1 (pula o cabeçalho)
        for i, row in enumerate(todas_linhas[1:], start=2):
            # row[0] é Nome, row[1] é Livro, row[3] é Status
            # Verifique a ordem das colunas na sua planilha!
            if len(row) >= 4:
                nome_planilha = row[0]
                livro_planilha = row[1]
                status_planilha = row[3]
                
                if nome_planilha == nome_busca and status_planilha == "Pendente":
                    encontrou_algum = True
                    # Botão único usando o índice da linha como chave
                    if st.button(f"Devolver: {livro_planilha}", key=f"btn_{i}"):
                        # Atualiza a célula da coluna 4 (Status) na linha 'i'
                        sheet.update_cell(i, 4, "Devolvido")
                        st.success("Livro devolvido com sucesso!")
                        st.rerun()
        
        if not encontrou_algum:
            st.info("Nenhum empréstimo pendente encontrado para essa pessoa.")

elif choice == "Histórico Geral":
    st.subheader("Todos os Registros")
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)
    st.dataframe(df, use_container_width=True)