import streamlit as st
from groq import Groq
from gtts import gTTS
import os






# Configuración de la página
st.set_page_config(page_title="Bagash AI", page_icon="🐼")
st.title("Bagash AI")

nombre = st.text_input("¿Cuál es tu nombre?")

if st.button("Saludar"):
    st.write(f"¡Hola, {nombre}! Bienvenido/a a Bagash")

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


# Crear usuario en Groq
def crear_usuario_groq():
    claveSecreta = st.secrets["CLAVE_API"]
    return Groq(api_key=claveSecreta)


# Configurar el modelo seleccionado
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
        st.write(f"Audio guardado en: {archivo_audio}")
        return archivo_audio
    except Exception as e:
        st.error(f"Error al generar el audio: {e}")
        return None


# Función principal
def main():
    modelo = configurar_pagina()
    clienteUsuario = crear_usuario_groq()
    inicializar_estado()
    mostrar_historial()
    
    # Entrada de mensaje
    mensaje = st.chat_input("Escribí tu mensaje:")
    if mensaje:
        actualizar_historial("user", mensaje, "👦")
        chat_completo = configurar_modelo(clienteUsuario, modelo, mensaje)
        
        if chat_completo:
            respuesta_generada = ""
            for parte in generar_respuesta(chat_completo):
                respuesta_generada += parte
                st.chat_message("assistant").markdown(parte)

            actualizar_historial("assistant", respuesta_generada, "🤖")
            
            # Generar el audio de la respuesta
            audio_path = generar_audio(respuesta_generada)
            if audio_path:
                st.session_state.audio_path = audio_path
                st.session_state.mostrar_audio = True

    # Mostrar botón para reproducir el audio
    if st.session_state.mostrar_audio and st.session_state.audio_path:
        if st.button("🔊 Escuchar respuesta"):
            st.audio(st.session_state.audio_path, format="audio/mp3")
            st.session_state.mostrar_audio = False  # Ocultar el botón después de reproducir


if __name__ == "__main__":
    main()
