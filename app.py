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
st.set_page_config(page_title="Auditor Arq Sênior", layout="wide")
st.title("📐 Agente Arquiteto Revisor Sênior")

# Recupera a API Key das "Secrets" do Streamlit
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# Configurações do Remetente (Vêm do Secrets)
EMAIL_REMETENTE = st.secrets["EMAIL_USER"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASS"]

def pdf_to_images(pdf_file):
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
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg['Subject'] = "Relatório Técnico de Revisão Executiva - Auditoria de Projeto"
    
    # CSS básico para deixar a tabela e o e-mail bonitos no Gmail
    estilo_html = """
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f4f4f4; color: #333; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
    </style>
    """
    
    corpo_html = markdown.markdown(relatorio_md, extensions=['tables'])
    html_final = f"<html><head>{estilo_html}</head><body><div class='header'><h2>Relatório de Revisão Técnica</h2></div>{corpo_html}</body></html>"
    
    msg.attach(MIMEText(html_final, 'html'))
    
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
uploaded_file = st.file_uploader("1. Faça o upload do arquivo técnico (PDF)", type="pdf")
email_destino = st.text_input("2. E-mail para envio do relatório técnico:", value="virodriguesbol@gmail.com")

if uploaded_file is not None:
    if st.button("🚀 Iniciar Revisão Técnica Sênior"):
        st.info(f"O Arquiteto Revisor está analisando as pranchas. O e-mail será enviado para: {email_destino}")
        
        with st.spinner("Realizando conferência de normas (NBR 6492 / NBR 5410)..."):
            try:
                images = pdf_to_images(uploaded_file)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # A sua Persona e Checklist integrados:
                prompt = f"""
                Persona: Você é um Arquiteto Revisor Sênior com 20 anos de experiência em detalhamento técnico e compatibilização. 
                Sua visão é analítica, focada nas normas NBR 6492 e NBR 5410.

                Instruções de Análise:
                Analise o arquivo PDF (imagens das pranchas) seguindo estas 4 camadas:
                1. Conformidade de Cotas e Escala: Verifique cotas ausentes, erros de soma e proporcionalidade.
                2. Erros Ortográficos e Textuais: Revise legendas, selos e nomenclatura de ambientes.
                3. Infraestrutura Elétrica e Tomadas: Avalie funcionalidade, alturas e pontos críticos (interruptores e tomadas de bancada/ilha/cabeceira).
                4. Inconsistências de Layout: Identifique conflitos entre móveis e pontos elétricos e confira bonecas de portas/janelas.

                Formato da Resposta (Obrigatório para o E-mail):
                - Inicie com um breve parágrafo profissional de introdução.
                - Apresente os achados OBRIGATORIAMENTE em uma TABELA Markdown com as colunas: | Tipo de Erro | Localização (Ambiente) | Descrição do Problema | Sugestão de Correção |
                - Finalize com uma breve conclusão sobre a viabilidade executiva do projeto.
                - Use um tom sério, técnico e direto.
                """
                
                response = model.generate_content([prompt, *images])
                relatorio = response.text
                
                st.subheader("📋 Relatório Gerado")
                st.markdown(relatorio)
                
                if enviar_email(relatorio, email_destino):
                    st.success(f"Relatório enviado com sucesso! Verifique o e-mail {email_destino}")
                
                del images
                gc.collect()

            except Exception as e:
                st.error(f"Ocorreu um erro na análise: {e}")
