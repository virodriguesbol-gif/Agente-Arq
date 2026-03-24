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

# Recupera a API Key das "Secrets" do Streamlit
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# Configuração do E-mail
EMAIL_DESTINO = "virodriguesbol@gmail.com"
EMAIL_REMETENTE = st.secrets["EMAIL_USER"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASS"]

def pdf_to_images(pdf_file):
    """Converte as páginas do PDF em imagens para a IA 'enxergar'"""
    pdf = pdfium.PdfDocument(pdf_file)
    images = []
    for i in range(len(pdf)):
        page = pdf[i]
        # Renderizamos com scale=3 para garantir que a IA leia as cotas pequenas
        bitmap = page.render(scale=3) 
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
        # Usamos o servidor do Gmail
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
        with st.spinner("Analisando projeto... Isso pode levar de 30 a 60 segundos."):
            try:
                # 1. Preparar imagens
                images = pdf_to_images(uploaded_file)
                
                # 2. Configurar o Modelo (Usando o nome oficial estável)
                # Se o 2.0-flash der erro, mude para 'gemini-1.5-flash'
                 model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                
                # 3. Prompt Especialista (Refinado)
                prompt = """
                Você é um arquiteto auditor sênior experiente em normas técnicas. 
                Analise cuidadosamente as imagens desta planta e realize uma auditoria detalhada:
                
                1. COTAS: Verifique se as cotas estão completas e se os valores são coerentes com a escala (ex: portas e paredes com medidas padrão).
                2. ELÉTRICA BANHEIRO: Procure especificamente por pontos de tomada destinados a TOALHEIRO ELÉTRICO.
                3. ELÉTRICA COZINHA: Se houver uma ilha, verifique se existem tomadas previstas nela.
                4. GRAMÁTICA E TEXTO: Liste qualquer erro ortográfico em legendas, notas ou no selo.
                5. ACESSIBILIDADE: Verifique se as portas de acesso possuem a largura mínima de 80cm.

                Retorne um relatório organizado com: 
                - ✅ Itens em conformidade
                - ❌ Problemas detectados
                - 💡 Sugestões de melhoria
                """
                
                # 4. Gerar resposta (Passando as imagens como lista)
                response = model.generate_content([prompt, *images])
                relatorio = response.text
                
                # 5. Mostrar na tela e enviar e-mail
                st.subheader("📋 Resultado da Auditoria")
                st.markdown(relatorio)
                
                if enviar_email(relatorio):
                    st.success(f"Relatório enviado com sucesso para {EMAIL_DESTINO}!")
                else:
                    st.warning("O relatório foi gerado, mas houve um problema ao enviar o e-mail.")
            
            except Exception as e:
                st.error(f"Ocorreu um erro durante a análise: {e}")
                st.info("Dica: Se for um erro de 'NotFound', tente mudar o modelo no código para 'gemini-1.5-flash'.")
