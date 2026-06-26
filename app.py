"""
PROYECTO: Prueba de ruta
ÁREA ORIGEN: Postventa
DESCRIPCIÓN: Este script inicializa el servidor backend que gestiona los formularios técnicos de inspección para Audi y Volkswagen, procesa los datos en tiempo real, los persiste en Supabase y renderiza los reportes físicos en PDF mediante WeasyPrint.
INSTRUCCIONES: Las rutas y configuraciones deben añadirse debajo de la instancia de 'app'.
LINK: https://generador-pdf-formulario.onrender.com/
"""

# Flask es un microframework que permite el balance entre velocidad del desarrollo y control arquitectónico
from flask import Flask, render_template, request, send_file
from datetime import datetime
from weasyprint import HTML
import os
import tempfile
import traceback
from supabase import create_client, Client

# '__name__' le indica a Flask dónde buscar recursos como plantillas (templates) y archivos estáticos.
app = Flask(__name__)

# -------------------------------------------------------------------------
# CONEXIÓN CON LA BASE DE DATOS (SUPABASE)
# Se cargan las credenciales de seguridad del entorno y se inicializa el 
# cliente para poder leer y escribir datos en el servidor de Supabase.
# -------------------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL", "TU_SUPABASE_URL_AQUI")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "TU_SUPABASE_ANON_KEY_AQUI")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------------------------------------------------
# @app.route conecta la web con el código python (Routing)
# -------------------------------------------------------------------------
@app.route('/') # Define que esta función responderá cuando se acceda a la raíz del sitio web.                    
def home():     # Define la función "vista" (view function) que procesa la lógica de la página principal.      
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    # Renderiza la plantilla HTML y le inyecta variables dinámicas.
    return render_template('pdf_template.html', es_pdf=False, fecha=fecha_hoy, marca='audi')


# --- FUNCIÓN INTERNA PROCESADORA (MÓDULO CENTRAL CORE) ---
def procesar_inspeccion(sufijo_marca):
    # Obtiene todos los campos del formulario HTML como un diccionario de Python
    datos_html = request.form.to_dict()

    # =========================================================================
    # ⚙️ CONTROL DE CAMBIOS: ACTUALIZACIÓN DE MÉTRICAS DE KILOMETRAJE
    # =========================================================================
    for campo in ['km_inicial', 'km_final']:
        if campo in datos_html and datos_html[campo]:
            try:
                datos_html[campo] = int(datos_html[campo])
            except ValueError:
                datos_html[campo] = 0
        else:
            datos_html[campo] = 0

    # Forzamos la inyección limpia de variables estructurales hacia Jinja2
    html = render_template(
        'pdf_template.html',
        es_pdf=True,
        marca=sufijo_marca, 
        datos_post=datos_html,
        url_root=request.url_root,
        orden=datos_html.get('orden', ''),
        placa=datos_html.get('placa', ''),
        modelo=datos_html.get('modelo', ''),
        motor=datos_html.get('motor', ''),
        # Enviamos las dos nuevas variables dinámicas al HTML para el dibujo del PDF
        km_inicial=datos_html.get('km_inicial', 0), # <--- NUEVO
        km_final=datos_html.get('km_final', 0),     # <--- NUEVO
        tecnico=datos_html.get('tecnico', ''),
        fecha=datos_html.get('fecha', '')
    )

    # Generación física del archivo binario PDF en el directorio temporal del servidor
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    HTML(string=html, base_url=os.path.dirname(os.path.abspath(__file__))).write_pdf(pdf_file.name)
    print(f"-> PDF de {sufijo_marca.upper()} generado localmente.")

    n_orden = datos_html.get('orden', 'SIN_ORDEN').strip()
    placa = datos_html.get('placa', 'SIN_PLACA').strip()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo_pdf = f"{n_orden}_{placa}_{timestamp}.pdf"
    
    # Subida automatizada del reporte PDF al Storage Bucket de Supabase
    url_publica = None
    try:
        with open(pdf_file.name, 'rb') as archivo_pdf:
            supabase.storage.from_('pdfs_formularios').upload(
                file=archivo_pdf,
                path=nombre_archivo_pdf,
                file_options={"content-type": "application/pdf"}
            )
        url_publica = supabase.storage.from_('pdfs_formularios').get_public_url(nombre_archivo_pdf)
        print(f"-> PDF subido al Storage. URL: {url_publica}")
    except Exception as e:
        print(f"Alerta Storage: No se pudo subir: {e}")

    # TRADUCCIÓN DE DATOS QUITANDO SUFIJOS PARA EL INSERT DE LA BASE DE DATOS
    # Transforma 'ilum_exterior_audi' o 'ilum_exterior_vw' en 'ilum_exterior' dinámicamente para la tabla común.
    datos_para_supabase = {}
    for clave, valor in datos_html.items():
        if clave.endswith(f'_{sufijo_marca}'):
            datos_para_supabase[clave.replace(f'_{sufijo_marca}', '')] = valor
        else:
            datos_para_supabase[clave] = valor

    # Adjuntamos la URL de descarga del PDF al registro que se guardará en la tabla
    if url_publica:
        datos_para_supabase['url_pdf'] = url_publica

    # Persistencia de datos final en la tabla 'inspecciones' de Supabase
    try:
        supabase.table("inspecciones").insert(datos_para_supabase).execute()
        print(f"¡Inspección de {sufijo_marca.upper()} guardada en base de datos!")
    except Exception as database_error:
        return f"<h1>Error al guardar en Supabase:</h1><p>{str(database_error)}</p>", 500

    # Envía el archivo PDF binario al navegador del cliente forzando la descarga nativa
    return send_file(pdf_file.name, as_attachment=True, download_name=f"{n_orden}_{placa}.pdf")

# --- RUTA ENDPOINT PARA AUDI ---
@app.route('/generar-audi', methods=['POST'])
def generar_audi():
    try:
        return procesar_inspeccion(sufijo_marca='audi')
    except Exception as e:
        return f"<h1>Error Interno (Ruta Audi):</h1><pre>{traceback.format_exc()}</pre>", 500

# --- RUTA ENDPOINT PARA VOLKSWAGEN ---
@app.route('/generar-vw', methods=['POST'])
def generar_vw():
    try:
        return procesar_inspeccion(sufijo_marca='vw')
    except Exception as e:
        return f"<h1>Error Interno (Ruta VW):</h1><pre>{traceback.format_exc()}</pre>", 500

if __name__ == '__main__':
    app.run(debug=True)
