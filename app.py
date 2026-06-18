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
# --- RUTA PARA VOLKSWAGEN ---
# =====================================================================
@app.route('/generar-vw', methods=['POST'])
def generar_vw():
    try:
        # 1. Captura todos los datos enviados desde los inputs del formulario web de VW (vienen con '_vw')
        datos_html = request.form.to_dict()

        # Convertimos el kilometraje a número entero si existe
        if 'km' in datos_html and datos_html['km']:
            try:
                datos_html['km'] = int(datos_html['km'])
            except ValueError:
                datos_html['km'] = 0

        # 2. Renderiza la plantilla compartida pasando los datos tal cual los espera el HTML
        html = render_template(
            'pdf_template.html',  # Plantilla única compartida
            es_pdf=True,
            datos_post=datos_html,
            url_root=request.url_root,  
            **datos_html  # Mantiene tu desempaquetado original (fecha, tecnico, etc.)
        )

        # 3. Crea el archivo PDF físico temporal
        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        HTML(
            string=html,
            base_url=os.path.dirname(os.path.abspath(__file__))
        ).write_pdf(pdf_file.name)
        
        print("-> PDF de VW generado localmente en el servidor.")

        # --- EXTRACCIÓN DE IDENTIFICADORES CLAVE ---
        n_orden = datos_html.get('orden', 'SIN_ORDEN').strip()
        placa = datos_html.get('placa', 'SIN_PLACA').strip()
        nombre_archivo_pdf = f"{n_orden}_{placa}.pdf"
        
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
            print(f"-> PDF de VW subido al Storage de forma automática. URL: {url_publica}")
        except Exception as e:
            print(f"Alerta Storage (VW): No se pudo subir al Storage: {e}")

        # =====================================================================
        # --- TRADUCCIÓN DE DATOS VW PARA LA TABLA DE SUPABASE ---
        # =====================================================================
        datos_para_supabase = {}
        for clave, valor in datos_html.items():
            # Si la variable termina en '_vw', le removemos el sufijo para calzar con la BD
            if clave.endswith('_vw'):
                nueva_clave = clave.replace('_vw', '')
                datos_para_supabase[nueva_clave] = valor
            else:
                # Conserva intactos 'orden', 'placa', 'km', 'tecnico', 'fecha', etc.
                datos_para_supabase[clave] = valor

        if url_publica:
            datos_para_supabase['url_pdf'] = url_publica

        # 5. Intentamos guardar el diccionario ya limpio en la tabla de Supabase 
        try:
            supabase.table("inspecciones").insert(datos_para_supabase).execute()
            print("¡Inspección de VW guardada exitosamente en Supabase sin conflictos!")
        except Exception as database_error:
            return f"<h1>Error al guardar VW en Supabase (Base de datos):</h1><p>{str(database_error)}</p>", 500

        # 6. Devuelve el archivo para su descarga inmediata
        return send_file(
            pdf_file.name,
            as_attachment=True,
            download_name=f"{n_orden}_{placa}.pdf"
        )
    except Exception as e:
        error_detallado = traceback.format_exc()
        return f"<h1>Error Interno del Servidor (Ruta VW):</h1><pre>{error_detallado}</pre>", 500


# =====================================================================
# --- RUTA PARA AUDI ---
# =====================================================================
@app.route('/generar-audi', methods=['POST'])
def generar_audi():
    try:
        # 1. Captura todos los datos originales enviados por el HTML de Audi (vienen con '_audi')
        datos_html = request.form.to_dict()

        # Convertimos el kilometraje a entero si existe
        if 'km' in datos_html and datos_html['km']:
            try:
                datos_html['km'] = int(datos_html['km'])
            except ValueError:
                datos_html['km'] = 0

        # 2. Renderiza LA MISMA plantilla compartida pasando las variables tal y como las espera el HTML
        html = render_template(
            'pdf_template.html',  # Plantilla única compartida
            es_pdf=True,
            datos_post=datos_html,
            url_root=request.url_root,
            **datos_html  # Mantiene tu desempaquetado original (fecha, tecnico, etc.)
        )

        # 3. Generación física del PDF temporal
        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        HTML(
            string=html, 
            base_url=os.path.dirname(os.path.abspath(__file__))
        ).write_pdf(pdf_file.name)
        
        print("-> PDF de Audi generado localmente en el servidor.")

        # --- EXTRACCIÓN DE IDENTIFICADORES CLAVE ---
        n_orden = datos_html.get('orden', 'SIN_ORDEN').strip()
        placa = datos_html.get('placa', 'SIN_PLACA').strip()
        nombre_archivo_pdf = f"{n_orden}_{placa}.pdf"
        
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
            print(f"-> PDF de Audi subido al Storage de forma automática. URL: {url_publica}")
        except Exception as e:
            print(f"Alerta Storage (Audi): No se pudo subir al Storage: {e}")

        # =====================================================================
        # --- TRADUCCIÓN DE DATOS AUDI PARA LA TABLA DE SUPABASE ---
        # =====================================================================
        datos_para_supabase = {}
        for clave, valor in datos_html.items():
            # Si la variable del formulario de Audi termina en '_audi', le removemos el sufijo para la BD
            if clave.endswith('_audi'):
                nueva_clave = clave.replace('_audi', '')
                datos_para_supabase[nueva_clave] = valor
            else:
                # Conserva intactos los campos globales comunes: 'orden', 'placa', 'km', 'tecnico', 'fecha', etc.
                datos_para_supabase[clave] = valor

        if url_publica:
            datos_para_supabase['url_pdf'] = url_publica

        # 5. Insertamos en la tabla usando el diccionario ya corregido y traducido
        try:
            supabase.table("inspecciones").insert(datos_para_supabase).execute()
            print("¡Inspección de Audi guardada correctamente sin conflictos!")
        except Exception as database_error:
            return f"<h1>Error al guardar Audi en Supabase (Base de datos):</h1><p>{str(database_error)}</p>", 500

        # 6. Devuelve el archivo para su descarga inmediata
        return send_file(
            pdf_file.name,
            as_attachment=True,
            download_name=f"{n_orden}_{placa}.pdf"
        )
    except Exception as e:
        error_detallado = traceback.format_exc()
        return f"<h1>Error Interno del Servidor (Ruta Audi):</h1><pre>{error_detallado}</pre>", 500


if __name__ == '__main__':
    app.run(debug=True)
