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
st.set_page_config(page_title="Auditor Arq Sênior v3.0", layout="wide")
st.title("📐 Agente Arquiteto Revisor Sênior (Filtro Anti-Erro)")

# Recupera a API Key das "Secrets" do Streamlit
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

EMAIL_REMETENTE = st.secrets["EMAIL_USER"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASS"]

def pdf_to_images(pdf_file):
    pdf = pdfium.PdfDocument(pdf_file)
    images = []
    for i in range(len(pdf)):
        page = pdf[i]
        # Aumentamos para 2.5 para dar "visão de águia" à IA
        bitmap = page.render(scale=2.5) 
        pil_image = bitmap.to_pil()
        images.append(pil_image)
        page.close()
    pdf.close()
    return images

def enviar_email(relatorio_md, destinatario):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg['Subject'] = "Relatório de Revisão Técnica - Auditoria Validada"
    
    estilo_html = """
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 13px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #2c3e50; color: white; }
        tr:nth-child(even) { background-color: #f8f9fa; }
        .critical { color: #e74c3c; font-weight: bold; }
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
    except Exception as e:
        st.error(f"Erro ao enviar: {e}")
        return False

# --- INTERFACE ---
uploaded_file = st.file_uploader("Suba o PDF (Será analisado com rigor matemático)", type="pdf")
email_destino = st.text_input("E-mail para envio:", value="virodriguesbol@gmail.com")

if uploaded_file is not None:
    if st.button("🚀 Iniciar Auditoria"):
        with st.spinner("O Revisor Sênior está conferindo cada cota e termo técnico..."):
            try:
                images = pdf_to_images(uploaded_file)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # PROMPT DE ALTA PRECISÃO
                prompt = f"""
                Você é um Arquiteto Revisor Sênior obcecado por precisão. 
                Sua missão é encontrar APENAS erros reais. Falsos positivos prejudicam sua reputação.

                --- PROTOCOLO DE VERIFICAÇÃO ---
                1. COTAS: Ao somar cotas parciais, faça o cálculo duas vezes. Se a diferença for menor que 1cm, ignore (pode ser arredondamento). Só reporte se houver erro matemático claro.
                2. TERMOS TÉCNICOS: NÃO reporte como erro termos como: Cooktop, Cocktop (variante aceitável), cm, CM, m, M, H:, PA, sapatas, layout, etc.
                3. ORTOGRAFIA: Ignore variações de Maiúsculas/Minúsculas. Só reporte se a palavra for ilegível ou mudar o sentido técnico.
                4. ELÉTRICA/HIDRÁULICA: Só aponte ausência de cota se for impossível executar a instalação com as informações dadas.

                --- FORMATO DA RESPOSTA ---
                - Use uma tabela Markdown: | Categoria | Local (Prancha/Página) | Descrição do Erro | Sugestão de Ajuste |
                - Se uma categoria estiver 100% correta, escreva "CONFORME" e não liste erros nela.
                - Seja direto. Menos é mais. Só escreva se tiver certeza absoluta.
                """
                
                response = model.generate_content([prompt, *images])
                relatorio = response.text
                
                st.markdown(relatorio)
                if enviar_email(relatorio, email_destino):
                    st.success("Relatório validado enviado!")
                
                del images
                gc.collect()

            except Exception as e:
                st.error(f"Erro: {e}")
