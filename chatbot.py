import streamlit as st
from groq import Groq
from gtts import gTTS
from gtts.lang import tts_langs
from deep_translator import GoogleTranslator
import os
from PIL import Image
import pytesseract
import cv2
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

def configurar_modelo(cliente, modelo, mensajeDeEntrada):
    return cliente.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": mensajeDeEntrada}],
        stream=True
    )

def inicializar_estado():
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []
    if "audio_path" not in st.session_state:
        st.session_state.audio_path = None
    if "mostrar_audio" not in st.session_state:
        st.session_state.mostrar_audio = False
    if "archivo_subido" not in st.session_state:
        st.session_state.archivo_subido = None
    if "accion_archivo" not in st.session_state:
        st.session_state.accion_archivo = ""

def actualizar_historial(rol, contenido, avatar):
    st.session_state.mensajes.append({"role": rol, "content": contenido, "avatar": avatar})

def mostrar_historial():
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["role"], avatar=mensaje["avatar"]):
            st.markdown(mensaje["content"])

def generar_respuesta(chat_completo):
    respuesta_completa = ""
    for frase in chat_completo:
        if hasattr(frase, "choices") and frase.choices[0].delta.content:  # Validación adicional
            respuesta_completa += frase.choices[0].delta.content
            yield frase.choices[0].delta.content  # Respuestas incrementales
    return respuesta_completa

def obtener_respuesta_completa(chat_completo):
    generador = generar_respuesta(chat_completo)
    respuesta_completa = "".join(list(generador))
    return respuesta_completa

# Generar audio
def generar_audio(texto, idioma_codigo):
    try:
        # Validar que el texto sea una cadena
        if not isinstance(texto, str):
            raise TypeError("El texto debe ser una cadena de caracteres.")
        if not texto.strip():
            raise ValueError("El texto está vacío.")
        if idioma_codigo not in tts_langs():
            raise ValueError(f"El idioma '{idioma_codigo}' no es compatible con gTTS.")
       
        archivo_audio = f"./temp/audio_{len(st.session_state.mensajes)}.mp3"
        tts = gTTS(text=texto, lang=idioma_codigo)
        tts.save(archivo_audio)
        return archivo_audio
    except Exception as e:
        st.error(f"Error al generar el audio: {e}")
        return None


def procesar_imagen(imagen_subida):
    try:
        imagen = Image.open(imagen_subida)
        texto = pytesseract.image_to_string(imagen, lang="eng")
        return texto.strip()
    except Exception as e:
        return f"Error al procesar la imagen: {e}"

def procesar_pdf(pdf_subido):
    try:
        reader = PdfReader(pdf_subido)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text()
        return texto.strip()
    except Exception as e:
        return f"Error al procesar el PDF: {e}"

def procesar_video(video_subido):
    try:
        video = cv2.VideoCapture(video_subido.name)
        if not video.isOpened():
            return "Error al abrir el archivo de video."
        
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
        duracion = total_frames / fps
        return f"Duración del video: {duracion:.2f} segundos"
    except Exception as e:
        return f"Error al procesar el video: {e}"

def procesar_archivo(archivo):
    if archivo.type in ["image/png", "image/jpeg", "image/jpg"]:
        return procesar_imagen(archivo)
    elif archivo.type == "pdf":
        return procesar_pdf(archivo)
    elif archivo.type == "mp4":
        return procesar_video(archivo)
    else:
        return "Tipo de archivo no soportado."

def preguntar_accion_archivo():
    return st.radio("Selecciona qué deseas hacer con el archivo:", (
        "Extraer texto",
        "Analizar contenido",
        "Generar resumen"
    ))

def main():
    modelo, idioma_codigo = configurar_pagina()
    clienteUsuario = crear_usuario_groq()
    inicializar_estado()

    col1, col2 = st.columns([3, 2])

    with col1:
        mensaje = st.text_area("Escribí tu mensaje:")

    with col2:
        archivo = st.file_uploader("Sube tu archivo (imagen, PDF, video):", 
                                   type=["png", "jpg", "jpeg", "pdf", "mp4"],
                                   label_visibility="collapsed")

    if archivo:
        st.session_state.archivo_subido = procesar_archivo(archivo)
        st.session_state.accion_archivo = preguntar_accion_archivo()

    if st.button("Enviar"):
        if mensaje.strip():
            actualizar_historial("user", mensaje, "👦")
            chat_completo = configurar_modelo(clienteUsuario, modelo, mensaje)
            if chat_completo:
                with st.chat_message("assistant"):
                    respuesta_completa = st.write_stream(generar_respuesta(chat_completo))
                    actualizar_historial("assistant", respuesta_completa, "🤖")

        if st.session_state.archivo_subido:
            accion = st.session_state.accion_archivo
            texto_archivo = st.session_state.archivo_subido
            if accion == "Extraer texto":
                actualizar_historial("assistant", texto_archivo, "🤖")
            elif accion == "Analizar contenido":
                analizar = f"Contenido analizado: {texto_archivo[:100]}..."
                actualizar_historial("assistant", analizar, "🤖")
            elif accion == "Generar resumen":
                resumen = f"Resumen generado: {texto_archivo[:100]}..."
                actualizar_historial("assistant", resumen, "🤖")

            st.rerun()

   

   # Generar audio de la respuesta
    if "assistant" in [m["role"] for m in st.session_state.mensajes]:
        respuesta_final = st.session_state.mensajes[-1]["content"]
        audio_path = generar_audio(respuesta_final, idioma_codigo)
        if audio_path:
            st.session_state.audio_path = audio_path
            st.session_state.mostrar_audio = True


    if st.session_state.mostrar_audio and st.session_state.audio_path:
        if st.button("🔊 Escuchar respuesta"):
            st.audio(st.session_state.audio_path, format="audio/mp3")
            st.session_state.mostrar_audio = False
            st.rerun()
    mostrar_historial()
    
if __name__ == "__main__":
    main()
