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
st.set_page_config(page_title="Auditor Arq Sênior v5.0", layout="wide")
st.title("📐 Auditor Arquiteto Sênior (Ultra Precisão 4.0)")

API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

EMAIL_REMETENTE = st.secrets["EMAIL_USER"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASS"]

def pdf_to_images(pdf_file):
    """Converte PDF para imagens com escala 4.0 para máxima nitidez"""
    pdf = pdfium.PdfDocument(pdf_file)
    images = []
    for i in range(len(pdf)):
        page = pdf[i]
        # Opção B: Scale 4.0 (Aumenta o detalhamento visual para evitar erros de leitura)
        bitmap = page.render(scale=4.0) 
        pil_image = bitmap.to_pil()
        images.append(pil_image)
        page.close()
    pdf.close()
    return images

def enviar_email(relatorio_md, destinatario):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg['Subject'] = "Relatório de Auditoria Técnica - Revisão de Alta Precisão"
    
    estilo_html = """
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 13px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #2c3e50; color: white; }
        tr:nth-child(even) { background-color: #f8f9fa; }
    </style>
    """
    corpo_html = markdown.markdown(relatorio_md, extensions=['tables'])
    html_final = f"<html><head>{estilo_html}</head><body>{corpo_html}</body></html>"
    msg.attach(MIMEText(html_final, 'html'))
    
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
uploaded_file = st.file_uploader("Suba o PDF (Análise em escala 4.0)", type="pdf")
email_destino = st.text_input("E-mail de destino:", value="virodriguesbol@gmail.com")

if uploaded_file is not None:
    if st.button("🚀 Iniciar Auditoria de Alta Precisão"):
        # Aviso sobre o processamento pesado
        st.warning("A escala 4.0 exige mais processamento. O relatório pode levar até 2 minutos para ser gerado. Não feche a aba.")
        
        with st.spinner("Analisando detalhes milimétricos e compatibilizando..."):
            try:
                images = pdf_to_images(uploaded_file)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Opção A: Prompt com restrição de espessuras e "Dúvida = Descarte"
                prompt = """
                Você é um Arquiteto Revisor Sênior. 
                Sua missão é realizar uma auditoria executiva impecável. 

                --- REGRAS DE OURO PARA EVITAR ERROS ---
                1. CUIDADO COM ESPESSURAS: Cotas totais de ambientes somam apenas os vãos livres. NÃO some espessuras de paredes, pilares ou hachuras ao total, a menos que a linha de cota atravesse o elemento. 
                2. DÚVIDA É DESCARTE: Se a imagem estiver com qualquer ruído visual ou se você não tiver 100% de certeza do número lido, NÃO reporte o erro.
                3. TOLERÂNCIA: Diferenças de até 2cm devem ser tratadas como arredondamento do software e ignoradas.
                4. TERMOS TÉCNICOS: Ignore variações gráficas em 'Cooktop', 'cm', 'm', ou uso de maiúsculas. Foco apenas em erros ortográficos reais.

                --- CATEGORIAS DE ANÁLISE ---
                - Compatibilização Elétrica x Layout (ex: tomada atrás de móvel fixo).
                - Infraestrutura (alturas de pontos conforme NBR 5410).
                - Conferência de Cotas (Apenas erros matemáticos claros e confirmados).

                --- FORMATO DA RESPOSTA ---
                Inicie com uma introdução técnica. 
                TABELA Markdown: | Categoria | Prancha/Página | Texto Lido | Problema Identificado | Sugestão Técnica |
                Finalize com o selo: "Revisão Realizada com Critério de Alta Precisão".
                """
                
                response = model.generate_content([prompt, *images])
                relatorio = response.text
                
                st.markdown(relatorio)
                if enviar_email(relatorio, email_destino):
                    st.success(f"Relatório de alta fidelidade enviado para {email_destino}!")
                
                del images
                gc.collect()

            except Exception as e:
                st.error(f"Erro no processamento: {e}")
                st.info("Dica: Se houver erro de memória, reduza o 'scale' para 3.0 no código.")
