import streamlit as st
from groq import Groq
from gtts import gTTS
import os

# Configuración de la página
st.set_page_config(page_title="Bagash AI", page_icon="🐼")
st.title("Bagash AI")

# Modelos disponibles
modelos = ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768']

# Crear un directorio para almacenar audios
if not os.path.exists("temp"):
    os.makedirs("temp")

# Función para configurar la página
def configurar_pagina():
    st.sidebar.title("Configuración")
    elegirModelo = st.sidebar.selectbox("Elegir un modelo", options=modelos, index=0)
    return elegirModelo

# Crear cliente Groq
def crear_usuario_groq():
    claveSecreta = st.secrets["CLAVE_API"]  # Asegúrate de definir esta clave en secrets.toml
    return Groq(api_key=claveSecreta)

# Inicializar el estado de la sesión
def inicializar_estado():
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []
    if "audio_path" not in st.session_state:
        st.session_state.audio_path = None
    if "mostrar_audio" not in st.session_state:
        st.session_state.mostrar_audio = False

# Actualizar historial de mensajes
def actualizar_historial(rol, contenido, avatar):
    st.session_state.mensajes.append({"role": rol, "content": contenido, "avatar": avatar})

# Mostrar historial de mensajes
def mostrar_historial():
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["role"], avatar=mensaje["avatar"]):
            st.markdown(mensaje["content"])

# Generar respuesta del modelo
def generar_respuesta(cliente, modelo, mensaje):
    respuesta_completa = ""
    for frase in cliente.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": mensaje}],
        stream=True
    ):
        if frase.choices[0].delta.get("content"):
            fragmento = frase.choices[0].delta["content"]
            respuesta_completa += fragmento
            yield fragmento  # Entrega la respuesta por partes
    return respuesta_completa

# Generar audio con gTTS
def generar_audio(texto):
    try:
        archivo_audio = f"./temp/audio_{len(st.session_state.mensajes)}.mp3"
        tts = gTTS(text=texto, lang="es")
        tts.save(archivo_audio)
        return archivo_audio
    except Exception as e:
        st.error(f"Error al generar el audio: {e}")
        return None

# Función principal
def main():
    modelo = configurar_pagina()
    inicializar_estado()
    mostrar_historial()
    
    # Entrada de mensaje
    mensaje = st.chat_input("Escribí tu mensaje:")
    if mensaje:
        actualizar_historial("user", mensaje, "👦")
        
        clienteUsuario = crear_usuario_groq()  # Crear cliente aquí
        respuesta_generada = ""
        
        for parte in generar_respuesta(clienteUsuario, modelo, mensaje):
            respuesta_generada += parte
            st.chat_message("assistant").markdown(parte)
        
        actualizar_historial("assistant", respuesta_generada, "🤖")
        
        # Generar audio de la respuesta
        audio_path = generar_audio(respuesta_generada)
        if audio_path:
            st.session_state.audio_path = audio_path
            st.session_state.mostrar_audio = True

    # Mostrar botón para reproducir el audio
    if st.session_state.mostrar_audio and st.session_state.audio_path:
        if st.button("🔊 Escuchar respuesta"):
            st.audio(st.session_state.audio_path, format="audio/mp3")
            st.session_state.mostrar_audio = False  # Ocultar el botón tras reproducir

if __name__ == "__main__":
    main()

