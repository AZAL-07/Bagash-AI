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
        st.session_state.accion_archivo = None


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


# Generar audio
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


# Función para traducir texto con GoogleTranslator
def traducir_texto(texto, idioma_origen, idioma_destino):
    try:
        traducido = GoogleTranslator(source=idioma_origen, target=idioma_destino).translate(texto)
        return traducido
    except Exception as e:
        st.error(f"Error al traducir: {e}")
        return None



# Procesar el archivo cargado
def procesar_archivo(archivo):
    try:
        if archivo.type in ["image/png", "image/jpeg", "image/jpg"]:
            imagen = Image.open(archivo)
            texto = pytesseract.image_to_string(imagen, lang="eng").strip()
            return texto
        elif archivo.type == "pdf":
            reader = PdfReader(archivo)
            texto = "".join([page.extract_text() for page in reader.pages])
            return texto.strip()
        elif archivo.type == "mp4":
            video = cv2.VideoCapture(archivo.name)
            if not video.isOpened():
                return "Error al abrir el archivo de video."
            fps = video.get(cv2.CAP_PROP_FPS)
            total_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
            duracion = total_frames / fps
            return f"Duración del video: {duracion:.2f} segundos"
        else:
            return "Tipo de archivo no soportado."
    except Exception as e:
        return f"Error al procesar el archivo: {e}"


def main():
    modelo, idioma_codigo = configurar_pagina()
    clienteUsuario = crear_usuario_groq()
    inicializar_estado()
    


    col1, col2 = st.columns([2, 2])


    with col1:
        mensaje = st.text_area("Escribí tu mensaje:")


    if st.button("Enviar"):
        if mensaje.strip():
            if idioma_codigo != "en":
                mensaje = traducir_texto(mensaje, "auto", idioma_codigo)
            actualizar_historial("user", mensaje, "👦")
            chat_completo = configurar_modelo(clienteUsuario, modelo, mensaje)
            respuesta_completa = "".join(generar_respuesta(chat_completo))
            actualizar_historial("assistant", respuesta_completa, "🤖")
            audio_path = generar_audio(respuesta_completa, idioma_codigo)
            if audio_path:
                st.audio(audio_path, format="audio/mp3")


    mostrar_historial()


if __name__ == "__main__":
    main()
