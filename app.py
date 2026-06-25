"""
PROYECTO: Prueba de ruta
ÁREA ORIGEN: Postventa
DESCRIPCIÓN: Este script inicializa el servidor backend que gestiona [mencionar brevemente qué hace, ej: los endpoints de datos / el modelo predictivo].
INSTRUCCIONES: Las rutas y configuraciones deben añadirse debajo de la instancia de 'app'.
LINK: https://generador-pdf-formulario.onrender.com/
"""

#Flask es un microframework que permite el balance entre velocidad del desarrollo y control arquitectónico
from flask import Flask, render_template, request, send_file
from datetime import datetime
from weasyprint import HTML
import os
import tempfile
import traceback
from supabase import create_client, Client

# '__name__' le indica a Flask dónde buscar recursos como plantillas (templates) y archivos estáticos.
app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "TU_SUPABASE_URL_AQUI")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "TU_SUPABASE_ANON_KEY_AQUI")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

#@app.route conecta la web con el código python (Routing)

@app.route('/')
def home():
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    # Enviamos marca='audi' por defecto para la primera carga web
    return render_template('pdf_template.html', es_pdf=False, fecha=fecha_hoy, marca='audi')

# --- FUNCIÓN INTERNA PROCESADORA (REFACTORIZADA) ---
def procesar_inspeccion(sufijo_marca):
    datos_html = request.form.to_dict()

    if 'km' in datos_html and datos_html['km']:
        try:
            datos_html['km'] = int(datos_html['km'])
        except ValueError:
            datos_html['km'] = 0

    # Forzamos la inyección limpia de variables estructurales
    html = render_template(
        'pdf_template.html',
        es_pdf=True,
        marca=sufijo_marca, # <--- Clave: Le decimos explícitamente la marca al HTML
        datos_post=datos_html,
        url_root=request.url_root,
        orden=datos_html.get('orden', ''),
        placa=datos_html.get('placa', ''),
        modelo=datos_html.get('modelo', ''),
        motor=datos_html.get('motor', ''),
        km=datos_html.get('km', ''),
        tecnico=datos_html.get('tecnico', ''),
        fecha=datos_html.get('fecha', '')
    )

    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    HTML(string=html, base_url=os.path.dirname(os.path.abspath(__file__))).write_pdf(pdf_file.name)
    print(f"-> PDF de {sufijo_marca.upper()} generado localmente.")

    n_orden = datos_html.get('orden', 'SIN_ORDEN').strip()
    placa = datos_html.get('placa', 'SIN_PLACA').strip()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo_pdf = f"{n_orden}_{placa}_{timestamp}.pdf"
    
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

    # TRADUCCIÓN DE DATOS QUITANDO SUFIJOS PARA LA BD
    datos_para_supabase = {}
    for clave, valor in datos_html.items():
        if clave.endswith(f'_{sufijo_marca}'):
            datos_para_supabase[clave.replace(f'_{sufijo_marca}', '')] = valor
        else:
            datos_para_supabase[clave] = valor

    if url_publica:
        datos_para_supabase['url_pdf'] = url_publica

    try:
        supabase.table("inspecciones").insert(datos_para_supabase).execute()
        print(f"¡Inspección de {sufijo_marca.upper()} guardada en base de datos!")
    except Exception as database_error:
        return f"<h1>Error al guardar en Supabase:</h1><p>{str(database_error)}</p>", 500

    return send_file(pdf_file.name, as_attachment=True, download_name=f"{n_orden}_{placa}.pdf")

# --- RUTA PARA AUDI ---
@app.route('/generar-audi', methods=['POST'])
def generar_audi():
    try:
        return procesar_inspeccion(sufijo_marca='audi')
    except Exception as e:
        return f"<h1>Error Interno (Ruta Audi):</h1><pre>{traceback.format_exc()}</pre>", 500

# --- RUTA PARA VOLKSWAGEN ---
@app.route('/generar-vw', methods=['POST'])
def generar_vw():
    try:
        return procesar_inspeccion(sufijo_marca='vw')
    except Exception as e:
        return f"<h1>Error Interno (Ruta VW):</h1><pre>{traceback.format_exc()}</pre>", 500

if __name__ == '__main__':
    app.run(debug=True)
