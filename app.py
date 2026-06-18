from flask import Flask, render_template, request, send_file
from datetime import datetime
from weasyprint import HTML
import os
import tempfile
import traceback
# Importamos el cliente oficial de Supabase
from supabase import create_client, Client

app = Flask(__name__)

# Configuración de Supabase utilizando variables de entorno para mayor seguridad en Render
SUPABASE_URL = os.environ.get("SUPABASE_URL", "TU_SUPABASE_URL_AQUI")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "TU_SUPABASE_ANON_KEY_AQUI")

# Inicializamos el enlace con la base de datos de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def home():
    # Calcula la fecha actual en formato AAAA-MM-DD para inicializar el formulario web
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    return render_template('pdf_template.html', es_pdf=False, fecha=fecha_hoy)


# =====================================================================
# --- FUNCIÓN INTERNA PROCESADORA (EVITA DUPLICAR CÓDIGO) ---
# =====================================================================
def procesar_inspeccion(sufijo_marca):
    """
    Función genérica que centraliza la lógica de captura, renderizado, 
    guardado en base de datos y subida a Storage tanto para VW como para Audi.
    """
    # 1. Captura todos los datos originales enviados por el HTML
    datos_html = request.form.to_dict()

    # Convertimos el kilometraje a entero de forma segura
    if 'km' in datos_html and datos_html['km']:
        try:
            datos_html['km'] = int(datos_html['km'])
        except ValueError:
            datos_html['km'] = 0

    # 2. Renderiza la plantilla compartida
    html = render_template(
        'pdf_template.html',
        es_pdf=True,
        datos_post=datos_html,
        url_root=request.url_root,
        **datos_html
    )

    # 3. Generación física del PDF temporal
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    HTML(
        string=html, 
        base_url=os.path.dirname(os.path.abspath(__file__))
    ).write_pdf(pdf_file.name)
    
    print(f"-> PDF de {sufijo_marca.upper()} generado localmente en el servidor.")

    # --- EXTRACCIÓN DE IDENTIFICADORES CLAVE ---
    n_orden = datos_html.get('orden', 'SIN_ORDEN').strip()
    placa = datos_html.get('placa', 'SIN_PLACA').strip()
    
    # Añadimos un timestamp único al nombre del archivo para evitar colisiones/sobreescrituras en Storage
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo_pdf = f"{n_orden}_{placa}_{timestamp}.pdf"
    
    # 4. Almacenamiento automático en Supabase Storage
    url_publica = None
    try:
        with open(pdf_file.name, 'rb') as archivo_pdf:
            supabase.storage.from_('pdfs_formularios').upload(
                file=archivo_pdf,
                path=nombre_archivo_pdf,
                file_options={"content-type": "application/pdf"}
            )
        url_publica = supabase.storage.from_('pdfs_formularios').get_public_url(nombre_archivo_pdf)
        print(f"-> PDF de {sufijo_marca.upper()} subido al Storage automáticamente. URL: {url_publica}")
    except Exception as e:
        print(f"Alerta Storage ({sufijo_marca.upper()}): No se pudo subir al Storage: {e}")

    # =====================================================================
    # --- TRADUCCIÓN DE DATOS PARA LA TABLA DE SUPABASE ---
    # =====================================================================
    datos_para_supabase = {}
    for clave, valor in datos_html.items():
        # Si la variable termina con el sufijo asignado ('_vw' o '_audi'), se lo removemos para la BD
        if clave.endswith(f'_{sufijo_marca}'):
            nueva_clave = clave.replace(f'_{sufijo_marca}', '')
            datos_para_supabase[nueva_clave] = valor
        else:
            # Conserva intactos los campos comunes globales ('orden', 'placa', 'km', etc.)
            datos_para_supabase[clave] = valor

    # Inyectamos la URL pública si la subida fue exitosa
    if url_publica:
        datos_para_supabase['url_pdf'] = url_publica

    # Explicitamos qué marca procesó este registro (útil si manejas una sola tabla "inspecciones")
    datos_para_supabase['marca'] = sufijo_marca.upper()

    # 5. Insertamos en la tabla de Supabase
    try:
        supabase.table("inspecciones").insert(datos_para_supabase).execute()
        print(f"¡Inspección de {sufijo_marca.upper()} guardada correctamente en la BD sin conflictos!")
    except Exception as database_error:
        return f"<h1>Error al guardar {sufijo_marca.upper()} en Supabase (Base de Datos):</h1><p>{str(database_error)}</p>", 500

    # 6. Devuelve el archivo para su descarga inmediata
    return send_file(
        pdf_file.name,
        as_attachment=True,
        download_name=f"{n_orden}_{placa}.pdf"
    )


# =====================================================================
# --- RUTA PARA VOLKSWAGEN ---
# =====================================================================
@app.route('/generar-vw', methods=['POST'])
def generar_vw():
    try:
        return procesar_inspeccion(sufijo_marca='vw')
    except Exception as e:
        error_detallado = traceback.format_exc()
        return f"<h1>Error Interno del Servidor (Ruta VW):</h1><pre>{error_detallado}</pre>", 500


# =====================================================================
# --- RUTA PARA AUDI ---
# =====================================================================
@app.route('/generar-audi', methods=['POST'])
def generar_audi():
    try:
        return procesar_inspeccion(sufijo_marca='audi')
    except Exception as e:
        error_detallado = traceback.format_exc()
        return f"<h1>Error Interno del Servidor (Ruta Audi):</h1><pre>{error_detallado}</pre>", 500


if __name__ == '__main__':
    app.run(debug=True)
