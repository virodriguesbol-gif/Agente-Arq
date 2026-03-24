import streamlit as st
import google.generativeai as genai
import pypdfium2 as pdfium
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="Auditor de Projetos Arq", layout="centered")
st.title("🏗️ Agente Auditor de Arquitetura")

# Recupera a API Key das "Secrets" do Streamlit (Configuraremos no painel depois)
API_KEY = st.secrets["AIzaSyDMlBemo9w1HVGpjJymYIbCIOAXHXCRapM"]
genai.configure(api_key=API_KEY)

# Configuração do E-mail (Também via Secrets por segurança)
EMAIL_DESTINO = "virodriguesbol@gmail.com"
EMAIL_REMETENTE = st.secrets["EMAIL_USER"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASS"]

def pdf_to_images(pdf_file):
    """Converte as páginas do PDF em imagens para a IA 'enxergar'"""
    pdf = pdfium.PdfDocument(pdf_file)
    images = []
    for i in range(len(pdf)):
        page = pdf[i]
        bitmap = page.render(scale=2) # Aumenta a resolução para ler cotas
        pil_image = bitmap.to_pil()
        images.append(pil_image)
    return images

def enviar_email(relatorio):
    """Envia o relatório final para o seu e-mail"""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINO
    msg['Subject'] = "Relatório de Auditoria de Projeto - Novo Upload"
    
    msg.attach(MIMEText(relatorio, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False

# --- INTERFACE ---
uploaded_file = st.file_uploader("Arraste o PDF do projeto aqui", type="pdf")

if uploaded_file is not None:
    if st.button("🚀 Iniciar Auditoria Técnica"):
        with st.spinner("Analisando projeto... Isso pode levar alguns segundos."):
            
            # 1. Preparar imagens
            images = pdf_to_images(uploaded_file)
            
            # 2. Configurar o Modelo (Gemini 1.5 Pro é melhor para plantas)
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # 3. Prompt Especialista
            prompt = """
            Você é um arquiteto auditor sênior. Analise as imagens deste projeto e verifique:
            1. COTAS: Verifique se existem cotas desvinculadas ou incoerentes com a escala indicada (ex: portas com tamanhos absurdos).
            2. ELÉTRICA BANHEIRO: Verifique se há previsão de ponto de tomada para TOALHEIRO ELÉTRICO nos banheiros.
            3. ELÉTRICA COZINHA: Identifique se há uma ilha e se ela possui tomadas previstas.
            4. GRAMÁTICA: Revise todos os textos, legendas e selos em busca de erros de escrita.
            5. ACESSIBILIDADE: Cheque se as portas principais parecem ter o mínimo de 80cm.

            Responda em formato de relatório técnico estruturado, apontando o que está faltando ou o que está errado.
            """
            
            # 4. Gerar resposta
            response = model.generate_content([prompt, *images])
            relatorio = response.text
            
            # 5. Mostrar na tela e enviar e-mail
            st.subheader("📋 Resultado da Auditoria")
            st.markdown(relatorio)
            
            if enviar_email(relatorio):
                st.success(f"Relatório enviado com sucesso para {EMAIL_DESTINO}!")
