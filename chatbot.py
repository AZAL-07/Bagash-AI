import streamlit as st
from groq import Groq
from gtts import gTTS
import os
import pkg_resources

# Verificar si gTTS está instalado
installed_packages = [pkg.key for pkg in pkg_resources.working_set]
if 'gtts' in installed_packages:
    print("gTTS está instalado")
else:
    print("gTTS no está instalado")

# Configuración de la página
st.set_page_config(page_title="Bagash AI", page_icon="🐼")
st.title("Bagash AI")
# Configuración de la página

nombre = st.text_input("¿Cuál es tu nombre?")

if st.button("Saludar"):
    st.write(f"¡Hola, {nombre}! Bienvenido/a a Bagash")
    
# Crear un directorio para almacenar audios
if not os.path.exists("temp"):
    os.makedirs("temp")

# Modelos disponibles
modelos = ['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768']

# Función para configurar la página
def configurar_pagina():
    st.sidebar.title("Configuración")
    elegirModelo = st.sidebar.selectbox("Elegir un modelo", options=modelos, index=0)
    return elegirModelo

# Crear cliente en Groq
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
    mensaje = st.chat_input("Escribe tu mensaje:")
    if mensaje:
        actualizar_historial("user", mensaje, avatar="🙂")
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("Procesando...")
            respuesta_stream = configurar_modelo(clienteUsuario, modelo, mensaje)
            respuesta = generar_respuesta(respuesta_stream)
            st.markdown(respuesta)
            actualizar_historial("assistant", respuesta, avatar="🤖")
            
            # Generar audio (opcional)
            archivo_audio = generar_audio(respuesta)
            if archivo_audio:
                st.session_state.audio_path = archivo_audio
                st.session_state.mostrar_audio = True

    # Mostrar audio generado
    if st.session_state.mostrar_audio and st.session_state.audio_path:
        st.audio(st.session_state.audio_path, format="audio/mp3")

# Ejecutar aplicación
if __name__ == "__main__":
    main()
