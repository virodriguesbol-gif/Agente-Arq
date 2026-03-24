import streamlit as st
import google.generativeai as genai
import pypdfium2 as pdfium
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import gc
import markdown

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="Auditor de Projetos Arq", layout="centered")
st.title("🏗️ Agente Auditor de Arquitetura")

# Recupera a API Key das "Secrets" do Streamlit
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# Configurações do Remetente (Vêm do Secrets)
EMAIL_REMETENTE = st.secrets["EMAIL_USER"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASS"]

def pdf_to_images(pdf_file):
    """Converte TODAS as páginas do PDF em imagens"""
    pdf = pdfium.PdfDocument(pdf_file)
    images = []
    for i in range(len(pdf)):
        page = pdf[i]
        bitmap = page.render(scale=1.5) 
        pil_image = bitmap.to_pil()
        images.append(pil_image)
        page.close()
    pdf.close()
    return images

def enviar_email(relatorio_md, destinatario):
    """Converte o relatório para HTML e envia para o destinatário escolhido"""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg['Subject'] = "Relatório de Auditoria de Projeto - Novo Upload"
    
    html_content = markdown.markdown(relatorio_md)
    msg.attach(MIMEText(html_content, 'html'))
    
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
uploaded_file = st.file_uploader("1. Arraste o PDF completo do projeto aqui", type="pdf")

# NOVO: Campo para definir o e-mail de destino na hora
email_destino = st.text_input("2. Para qual e-mail devo enviar o relatório?", value="virodriguesbol@gmail.com")

if uploaded_file is not None:
    if st.button("🚀 3. Iniciar Auditoria Técnica Completa"):
        st.warning(f"Processando projeto completo. O relatório será enviado para: {email_destino}")
        
        with st.spinner("Lendo pranchas e acionando IA..."):
            try:
                # 1. Preparar imagens
                images = pdf_to_images(uploaded_file)
                
                # 2. Configurar o Modelo
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # 3. Prompt Especialista
                prompt = """
                Você é um arquiteto auditor sênior. Analise as imagens desta planta:
                1. COTAS: Verifique se as cotas estão completas e coerentes.
                2. ELÉTRICA BANHEIRO: Procure por pontos de tomada para TOALHEIRO ELÉTRICO.
                3. ELÉTRICA COZINHA: Se houver ilha, verifique se há tomadas nela.
                4. GRAMÁTICA: Liste erros de escrita em legendas ou selos.
                5. ACESSIBILIDADE: Portas principais devem ter no mínimo 80cm.

                Retorne um relatório organizado com conformidades, erros e sugestões.
                """
                
                # 4. Gerar resposta
                response = model.generate_content([prompt, *images])
                relatorio = response.text
                
                # 5. Mostrar na tela e enviar e-mail
                st.subheader("📋 Resultado da Auditoria")
                st.markdown(relatorio)
                
                if enviar_email(relatorio, email_destino):
                    st.success(f"Sucesso! Relatório enviado para {email_destino}")
                
                del images
                gc.collect()

            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")
