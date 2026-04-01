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

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="Auditor Arq Sênior v4.0", layout="wide")
st.title("📐 Auditor Arquiteto Sênior (Lógica de Conferência Real)")

API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

EMAIL_REMETENTE = st.secrets["EMAIL_USER"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASS"]

def pdf_to_images(pdf_file):
    pdf = pdfium.PdfDocument(pdf_file)
    images = []
    for i in range(len(pdf)):
        page = pdf[i]
        # Scale 3.0 para máxima nitidez possível
        bitmap = page.render(scale=3.0) 
        pil_image = bitmap.to_pil()
        images.append(pil_image)
        page.close()
    pdf.close()
    return images

def enviar_email(relatorio_md, destinatario):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg['Subject'] = "Relatório de Auditoria Técnica - Revisão Validada"
    
    corpo_html = markdown.markdown(relatorio_md, extensions=['tables'])
    msg.attach(MIMEText(corpo_html, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- INTERFACE ---
uploaded_file = st.file_uploader("Suba o PDF Técnico", type="pdf")
email_destino = st.text_input("E-mail de destino:", value="virodriguesbol@gmail.com")

if uploaded_file is not None:
    if st.button("🚀 Iniciar Auditoria"):
        with st.spinner("Realizando conferência matemática rigorosa..."):
            try:
                images = pdf_to_images(uploaded_file)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # NOVO PROMPT COM LÓGICA DE PENSAMENTO (CHAIN OF THOUGHT)
                prompt = """
                Você é um Arquiteto Revisor Sênior. Sua prioridade ZERO é NÃO reportar erros inexistentes. 
                Erros de leitura de imagem (OCR) são comuns, por isso você deve ser extremamente conservador.

                Siga este processo para cada cota:
                1. IDENTIFICAÇÃO: Localize os números das cotas parciais e a cota total.
                2. DESCARTE DE RUÍDO: Se um número estiver cortado por uma linha ou estiver ilegível, NÃO reporte erro sobre ele.
                3. CÁLCULO REAL: Some as parciais. 
                4. VALIDAÇÃO: Se a soma das parciais for DIFERENTE da cota total em mais de 0.02 (2cm), verifique se você leu os números corretamente. 
                5. SÓ REPORTE SE: Se após conferir 3 vezes, a diferença matemática for óbvia e clara.

                PROIBIÇÕES:
                - NÃO reporte erros de termos técnicos (Cooktop, cm, m, etc).
                - NÃO reporte erros de maiúsculas/minúsculas.
                - NÃO reporte erros se não tiver certeza absoluta do número que está lendo.

                FORMATO DA RESPOSTA:
                | Categoria | Prancha | Texto/Cota Lida | Problema Real | Sugestão |
                | :--- | :--- | :--- | :--- | :--- |
                (Se tudo estiver correto em uma categoria, apenas escreva: 'Categoria X: Conforme')
                """
                
                response = model.generate_content([prompt, *images])
                relatorio = response.text
                
                st.markdown(relatorio)
                if enviar_email(relatorio, email_destino):
                    st.success("Relatório enviado!")
                
                del images
                gc.collect()

            except Exception as e:
                st.error(f"Erro: {e}")
