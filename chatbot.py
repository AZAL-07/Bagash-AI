import streamlit as st
from groq import Groq
from gtts import gTTS
import os
import sys


# Imprime las rutas de búsqueda
print("Rutas de búsqueda de módulos:")
for ruta in sys.path:
    print(ruta)


# Configuración de la página
st.set_page_config(page_title="Bagash AI", page_icon="🐼")
st.title("Bagash AI")

# Entrada para capturar el nombre del usuario
nombre = st.text_input("¿Cuál es tu nombre?")

if st.button("Saludar"):
    st.write(f"¡Hola, {nombre}! Bienvenido/a a Bagash AI")

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
    claveSecreta = st.secrets.get("CLAVE_API")
    if not claveSecreta:
        st.error("CLAVE_API no está configurada en secrets.toml")
        return None
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
def generar_respuesta(chat_completo):
    respuesta_completa = ""
    for frase in chat_completo:
        # Validar si 'choices' existe y tiene el contenido esperado
        if "choices" in frase and isinstance(frase["choices"], list):
            delta = frase["choices"][0].get("delta", {})
            if "content" in delta:
                respuesta_completa += delta["content"]
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


# Simular configuración de modelo
def configurar_modelo(clienteUsuario, modelo, mensaje):
    # Simula una respuesta del modelo con la estructura esperada
    return [{"choices": [{"delta": {"content": f"Respuesta generada con {modelo} para: {mensaje}"}}]}]


# Área de chat
def area_chat():
    contenedorDelChat = st.container()
    with contenedorDelChat:
        mostrar_historial()


# Función principal
def main():
    modelo = configurar_pagina()
    clienteUsuario = crear_usuario_groq()
    if not clienteUsuario:
        return  # Detener ejecución si no se puede crear el cliente

    inicializar_estado()
    area_chat()

    # Input del usuario
    mensaje = st.chat_input("Escribí tu mensaje:")

    # Procesar el mensaje del usuario
    if mensaje:
        actualizar_historial("user", mensaje, "👦")

        # Configura el modelo con el mensaje
        chat_completo = configurar_modelo(clienteUsuario, modelo, mensaje)

        if chat_completo:  # Verificar que 'chat_completo' no esté vacío
            respuesta_generada = ""
            for parte in generar_respuesta(chat_completo):
                respuesta_generada += parte

            # Mostrar la respuesta en el área de chat
            st.chat_message("assistant").markdown(respuesta_generada)

            # Actualizar el historial del chat con la respuesta completa
            actualizar_historial("assistant", respuesta_generada, "🤖")

            # Generar el audio
            audio_path = generar_audio(respuesta_generada)
            if audio_path:
                st.session_state.audio_path = audio_path
                st.session_state.mostrar_audio = True


    # Mostrar botón para reproducir el audio
    if st.session_state.mostrar_audio and st.session_state.audio_path:
        if st.button("🔊 Escuchar respuesta"):
            st.audio(st.session_state.audio_path, format="audio/mp3")
            st.session_state.mostrar_audio = False


if __name__ == "__main__":
    main()






