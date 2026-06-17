from flask import Flask, render_template, request, send_file
from datetime import datetime
from weasyprint import HTML
import os
import tempfile
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

@app.route('/generar', methods=['POST'])
def generar():
    # 1. Captura todos los datos enviados desde los inputs del formulario web como un diccionario
    datos = request.form.to_dict()

    # Convertimos explícitamente el kilometraje a número entero si existe para evitar conflictos en SQL
    if 'km' in datos and datos['km']:
        try:
            datos['km'] = int(datos['km'])
        except ValueError:
            datos['km'] = 0

    # 2. Renderiza la plantilla en modo PDF pasando el diccionario de datos mapeados
    html = render_template(
        'pdf_template.html',
        es_pdf=True,
        datos_post=datos,
        **datos  # Mantiene tu desempaquetado original para alimentar orden, placa, modelo, etc.
    )

    # 3. Crea un archivo temporal seguro para depositar el binario del PDF
    pdf_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    # Convierte el HTML estructurado en PDF con WeasyPrint
    HTML(
        string=html,
        base_url=request.url_root
    ).write_pdf(pdf_file.name)
    
    print("-> PDF generado localmente en el servidor de Render.")

    # --- EXTRACCIÓN DE IDENTIFICADORES CLAVE ---
    # Rescatamos los valores del formulario para nombrar el archivo físico
    n_orden = datos.get('orden', 'SIN_ORDEN').strip()
    placa = datos.get('placa', 'SIN_PLACA').strip()

    # 4. AUTOMÁTICO: Subir el archivo PDF generado al Storage de Supabase
    # Volvemos al formato limpio: Orden_Placa.pdf
    nombre_archivo_pdf = f"{n_orden}_{placa}.pdf"
    
    url_publica = None
    try:
        with open(pdf_file.name, 'rb') as archivo_pdf:
            supabase.storage.from_('pdfs_formularios').upload(
                file=archivo_pdf,
                path=nombre_archivo_pdf,
                file_options={"content-type": "application/pdf"}
            )
        
        # Obtener el enlace de descarga permanente de Supabase Storage
        url_publica = supabase.storage.from_('pdfs_formularios').get_public_url(nombre_archivo_pdf)
        print(f"-> PDF subido al Storage de forma automática. URL: {url_publica}")
        
    except Exception as e:
        print(f"Alerta: No se pudo subir el archivo PDF al Storage: {e}")

    # 5. AUTOMÁTICO: Si obtuvimos la URL, la agregamos al diccionario antes de guardar en la tabla
    if url_publica:
        datos['url_pdf'] = url_publica

    # 6. Intentamos guardar el diccionario completo en Supabase 
    # (Aquí ya viaja el campo 'tecnico' con el valor que capturó del formulario)
    try:
        supabase.table("inspecciones").insert(datos).execute()
        print("¡Inspección y enlace de PDF guardados exitosamente en la base de datos de Supabase!")
    except Exception as e:
        print(f"Alerta: No se pudo registrar en la tabla de Supabase: {e}")

    # 7. Devuelve el archivo para su descarga inmediata con el nombre limpio solicitado
    return send_file(
        pdf_file.name,
        as_attachment=True,
        download_name=f"{n_orden}_{placa}.pdf"
    )

if __name__ == '__main__':
    append.run(debug=True)
