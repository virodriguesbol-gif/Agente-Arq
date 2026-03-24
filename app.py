import streamlit as st
import google.generativeai as genai
import pypdfium2 as pdfium
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import gc

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="Auditor de Projetos Arq", layout="centered")
st.title("🏗️ Agente Auditor de Arquitetura")

# Recupera a API Key das "Secrets" do Streamlit
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# Configuração do E-mail
EMAIL_DESTINO = "virodriguesbol@gmail.com"
EMAIL_REMETENTE = st.secrets["EMAIL_USER"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASS"]

def pdf_to_images(pdf_file):
    """Converte as páginas do PDF em imagens de forma otimizada"""
    pdf = pdfium.PdfDocument(pdf_file)
    images = []
    # Limitamos a 5 páginas para não estourar o limite de RAM do Streamlit
    num_paginas = min(len(pdf), 5) 
    
    for i in range(num_paginas):
        page = pdf[i]
        # scale=1.5 é o equilíbrio perfeito entre leitura de cota e economia de memória
        bitmap = page.render(scale=1.5) 
        pil_image = bitmap.to_pil()
        images.append(pil_image)
        # Limpeza rápida de memória
        page.close()
    
    pdf.close()
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
uploaded_file = st.file_uploader("Arraste o PDF do projeto aqui (Máx. 5 páginas serão analisadas)", type="pdf")

if uploaded_file is not None:
    if st.button("🚀 Iniciar Auditoria Técnica"):
        with st.spinner("Analisando projeto... O Gemini 2.5 está processando."):
            try:
                # 1. Preparar imagens
                images = pdf_to_images(uploaded_file)
                
                # 2. Configurar o Modelo (Versão 2.5 Flash conforme seu painel)
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
                
                if enviar_email(relatorio):
                    st.success(f"Relatório enviado com sucesso para {EMAIL_DESTINO}!")
                
                # Limpeza final de memória
                del images
                gc.collect()

            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")
                st.info("Dica: Se aparecer 'Quota Exceeded', espere 2 minutos e tente de novo.")
