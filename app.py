import streamlit as st
from google import genai
from google.genai import types
import json
import time

###CARGA DE LA CLAVE DE API DIRECTAMENTE
APY_KEY_DIRECTA = "AQ.Ab8RN6Ixy2pZnoAtjOZ0_eT6WH2tB0lZ0CaEs-XSrqZVjZi4Ig"

####CONSTRUCCIÓN DE LA GUI
st.set_page_config(page_title="Analista IA para Llamadas",page_icon="🖥️",layout="wide")

st.title("Analista IA - JQ Corp")
st.markdown("Analiza automáticamente el contenido de una llamada")

###CONFIGURAR LA BARRA LATERAL
with st.sidebar:
    st.header("Modelos IA disponibles")
    modelo = st.selectbox("Modelo",["gemini-3.8-flash","gemini-3.6-flash","gemini-3.5-flash-lite","gemini-2.5-flash","gemini-2.5-flash-lite"])
    st.info("Seleccione el modelo de IA para el análisis")

###CARGA DEL ARCHIVO DE AUDIO
archivo_audio = st.file_uploader("Cargue el audio para el análisis:",type=["mp3","wav","aac","ogg"])

###NOS ASEGURAMOS QUE EL ARCHIVO QUEDÓ CARGADO
if archivo_audio:
    st.audio(archivo_audio)
    if st.button("Iniciar análisis 🔊"):
        gemini_archivo = None
        
        ###INICIALIZAR EL MODELO IA Y TRAER LA CLAVE DE API
        client = genai.Client(api_key=APY_KEY_DIRECTA)

        try:
            with st.status("Analizando el contenido del audio...", expanded=True) as status:
                st.write("Guardando el archivo temporal...")
                archivo_temporal = f"temp_{archivo_audio.name}"
                with open(archivo_temporal,"wb") as f:
                    f.write(archivo_audio.getbuffer())
                st.write("Cargando el audio a Google AI...")
                ###ENVIANDO EL AUDIO A GOOGLE
                gemini_archivo = client.files.upload(file=archivo_temporal)

                while gemini_archivo.state.name ==  "PROCESSING":
                    st.write("Google está procesando el audio...")
                    time.sleep(3)
                    gemini_archivo = client.files.get(name=gemini_archivo.name)
                if gemini_archivo.state.name == "FAILED":
                    raise Exception("El procesamiento del audio falló")

                st.write("Generando el análisis con IA")

                ####INSTRUCCIONES PARA EL GPT
                config_analisis = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction =(
                        "Eres un experto en ventas. Analiza el audio y entrega obligatoriamente en formato JSON estructurado"
                        "el resultado del análisis exactamente con estas llaves:"
                        "califiacion_vendedor (un número de 1 al 10), actitud_cliente(texo: Positivo/Negativo,Neutro),"
                        "resumen (string largo), objeciones (lista de string), tareas (lista de string)."
                    )
                )
                prompt = "Analiza el audio de la llamada adjunto y entrega el reporte en el formato JSON estucturado solicitado"

                response = client.models._generate_content(
                    model = modelo,
                    contents = [gemini_archivo, prompt],
                    config = config_analisis
                )

                ###PROCESAR LA RESUPUESTA DE LA IA
                res = json.loads(response.text)
                status.update(label="Análisis terminado", state="complete",expanded=False)

            col1,col2 = st.columns(2)
            with col1:
                st.metric("Calificación del Vendedor",f"{res.get('califiacion_vendedor','N/A')}/10")
            with col2:
                st.metric("Actitud del Cliente",f"{res.get('actitud_cliente','N/A')}")
            st.subheader("Resumen de la llamda")
            st.info(res.get("resumen","N/A"))

            col1,col2 = st.columns(2)
            with col1:
                st.subheader("Objeciones del cliente")
                objeciones = res.get("objeciones",[])
                if objeciones:
                    for obje in objeciones:
                        st.write(f"* {obje}")
                else:
                    st.write("No se detectaron objeciones del cliente")
            with col2:
                st.subheader("Tareas Pendiente")
                tareas = res.get("tareas",[])
                if objeciones:
                    for tarea in tareas:
                        st.write(f"* {tarea}")
                else:
                    st.write("No se asignaron tareas durante la llamada")

        except Exception as e:
            st.error(f"Error detectado durante el proceso: {e}")
        
        finally:
            ###BORRAR TODOS LOS ARCHIVOS TEMPORALES DE GOOGLE IA STUDIO
            if gemini_archivo:
                try:
                    client.files.delete(name=gemini_archivo.name)
                except Exception:
                    pass
