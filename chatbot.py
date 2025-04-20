import streamlit as st
from groq import Groq
from gtts import gTTS
from gtts.lang import tts_langs
from deep_translator import GoogleTranslator
import os
from PIL import Image
import pytesseract
from PyPDF2 import PdfReader

# Configuración de Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configuración de la página
st.set_page_config(page_title="Bagash AI", page_icon="🐼")
st.title("Bagash AI")

# Idiomas disponibles para gTTS
IDIOMAS = {
    "Español": "es",
    "Árabe": "ar",
    "Inglés": "en",
    "Francés": "fr",
    "Alemán": "de",
    "Italiano": "it",
    "Portugués": "pt",
    "Chino": "zh-cn",
    "Japonés": "ja",
    "Coreano": "ko",
}

# Modelos simulados
MODELOS = ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768']

# Crear directorio temporal para audio
if not os.path.exists("temp"):
    os.makedirs("temp")

# Funciones principales

def configurar_pagina():
    st.sidebar.title("Configuración de la IA")
    modelo = st.sidebar.selectbox('Elegí un Modelo', options=MODELOS, index=0)
    idioma_seleccionado = st.sidebar.selectbox("Selecciona el idioma:", options=IDIOMAS.keys())
    idioma_codigo = IDIOMAS[idioma_seleccionado]
    return modelo, idioma_codigo

def crear_usuario_groq():
    claveSecreta = st.secrets["CLAVE_API"]
    return Groq(api_key=claveSecreta)

def generar_audio(texto, idioma_codigo):
    try:
        if not texto.strip():
            raise ValueError("El texto está vacío.")
        archivo_audio = f"./temp/audio_{len(st.session_state.mensajes)}.mp3"
        tts = gTTS(text=texto, lang=idioma_codigo)
        tts.save(archivo_audio)
        return archivo_audio
    except Exception as e:
        st.error(f"Error al generar el audio: {e}")
        return None

def procesar_archivo(archivo):
    # Verificamos si el archivo es None (no se subió ningún archivo)
    if archivo is None:
        st.error("No se ha subido ningún archivo.")
        return "No se ha subido ningún archivo."

    try:
        # Accedemos al nombre del archivo
        nombre_archivo = archivo.name.lower()

        # Verificamos el tipo de archivo y procesamos según corresponda
        if nombre_archivo.endswith((".png", ".jpg", ".jpeg")):
            imagen = Image.open(archivo)
            texto = pytesseract.image_to_string(imagen)
            return texto

        elif nombre_archivo.endswith(".pdf"):
            pdf = PdfReader(archivo)
            texto = ""
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ""
            return texto.strip() or "No se pudo extraer texto del PDF."

        elif nombre_archivo.endswith(".mp4"):
            return "Análisis de video aún no implementado."

        else:
            return "Tipo de archivo no compatible."

    except Exception as e:
        st.error(f"Error al procesar archivo: {e}")
        return "Error procesando archivo."

def main():
    modelo, idioma_codigo = configurar_pagina()
    clienteUsuario = crear_usuario_groq()

    # Inicializar el estado de la sesión
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []
    if "audio_path" not in st.session_state:
        st.session_state.audio_path = None
    if "archivo_subido" not in st.session_state:
        st.session_state.archivo_subido = None

    col1, col2 = st.columns([2, 2])

    with col1:
        mensaje = st.text_area("Escribí tu mensaje:")

    with col2:
        archivo = st.file_uploader("Sube tu archivo (imagen, PDF, video):",
                                   type=["png", "jpg", "jpeg", "pdf", "mp4"],
                                   label_visibility="collapsed")

    if archivo:
        texto_archivo = procesar_archivo(archivo)

        # Solo mostramos la opción "Extraer texto"
        accion = st.radio("Selecciona qué deseas hacer con el archivo:", ["Extraer texto"], key="accion_unica_1")

        if st.button("Confirmar acción"):
            if accion == "Extraer texto":
                # Mostrar el texto extraído
                st.session_state.mensajes.append({"role": "assistant", "content": f"Texto extraído: {texto_archivo}", "avatar": "🤖"})
                
                # Generar el audio con el texto extraído
                audio_path = generar_audio(texto_archivo, idioma_codigo)
                
                # Reproducir el audio si se genera correctamente
                if audio_path:
                    st.session_state.audio_path = audio_path
                    st.audio(audio_path, format="audio/mp3")  # Reproduce el audio

                # Limpiar el estado de la sesión para los próximos archivos
                st.session_state.archivo_subido = None
                st.session_state.accion_archivo = None
                st.rerun()  # Recargar la página para refrescar los estados

    # Enviar mensaje (esto es para mensajes de texto)
    if st.button("Enviar") and mensaje.strip():
        # Actualizar el historial con el mensaje
        st.session_state.mensajes.append({"role": "user", "content": mensaje, "avatar": "👦"})

        # Llamar al modelo Groq
        chat_completo = clienteUsuario.chat.completions.create(
            model=modelo,
            messages=[{"role": "user", "content": mensaje}],
            stream=True
        )
        
        respuesta_completa = ""
        for frase in chat_completo:
            if hasattr(frase, "choices") and frase.choices[0].delta.content:
                respuesta_completa += frase.choices[0].delta.content

        # Mostrar la respuesta del modelo
        st.session_state.mensajes.append({"role": "assistant", "content": respuesta_completa, "avatar": "🤖"})

        # Generar y reproducir el audio para la respuesta del modelo
        audio_path = generar_audio(respuesta_completa, idioma_codigo)
        if audio_path:
            st.audio(audio_path, format="audio/mp3")

    # Mostrar historial de conversación
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["role"], avatar=mensaje["avatar"]):
            st.markdown(mensaje["content"])

       # Reproducir el audio si existe en la sesión
    if st.session_state.audio_path:
        st.audio(st.session_state.audio_path, format="audio/mp3")  # Reproduce el audio

if __name__ == "__main__":
    main()
