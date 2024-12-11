import streamlit as st
from groq import Groq
from gtts import gTTS
import os

# Configuración de la página
st.set_page_config(page_title="Bagash AI", page_icon="🐼")
st.title("Bagash AI")

# Entrada para capturar el nombre del usuario
nombre = st.text_input("¿Cuál es tu nombre?")

if st.button("Saludar"):
    st.write(f"¡Hola, {nombre}! Bienvenido/a a Bagash AI")

# Modelos disponibles
MODELOS = ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768']

# Crear un directorio para almacenar audios
if not os.path.exists("temp"):
    os.makedirs("temp")

# Función para configurar la página
def configurar_pagina():
    # Agregamos un título principal a nuestra página
    st.title("Mi chat de IA")
    st.sidebar.title("Configuración de la IA") # Creamos un sidebar con un título.
    elegirModelo =  st.sidebar.selectbox('Elegí un Modelo', options=MODELOS, index=0)
    return elegirModelo

# Ciente
def crear_usuario_groq():
    claveSecreta = st.secrets["CLAVE_API"]
    return Groq(api_key=claveSecreta)

# Conexión a Groq y generación de respuesta
def configurar_modelo(cliente, modelo, mensajeDeEntrada):
    return cliente.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": mensajeDeEntrada}],
        stream=True
    )

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


#area_chat
def area_chat():
    contenedorDelChat = st.container(height=300, border=True)
    with contenedorDelChat:
        mostrar_historial()

# Generar respuesta del modelo
def generar_respuesta(chat_completo):
    respuesta_completa = ""
    for frase in chat_completo:
        if frase.choices[0].delta.content:
            respuesta_completa += frase.choices[0].delta.content
            yield frase.choices[0].delta.content
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
    clienteUsuario = crear_usuario_groq()
    inicializar_estado()
    area_chat()


    # Capturar mensaje del usuario
    mensaje = st.chat_input("Escribí tu mensaje:")
    if mensaje:
        # Actualizar el historial con el mensaje del usuario
        actualizar_historial("user", mensaje, "👦")
        
        # Configurar el modelo para generar una respuesta
        chat_completo = configurar_modelo(clienteUsuario, modelo, mensaje)

        if chat_completo:
            with st.chat_message("assistant"):
                # Usar el generador para mostrar las respuestas incrementales
                respuesta_completa = st.write_stream(generar_respuesta(chat_completo))
                actualizar_historial("assistant", respuesta_completa, "🤖")

                # Generar el audio si es necesario
                st.session_state.audio_path = generar_audio(respuesta_completa)
                st.session_state.mostrar_audio = True

                # Volver a renderizar la página
                st.rerun()

    # Mostrar botón para reproducir el audio
    if st.session_state.mostrar_audio and st.session_state.audio_path:
        if st.button("🔊 Escuchar respuesta"):
            st.audio(st.session_state.audio_path, format="audio/mp3")
            st.session_state.mostrar_audio = False

if __name__ == "__main__":
    main()






