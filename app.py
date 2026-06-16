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

    # 2. Intentamos guardar el diccionario completo de forma directa en Supabase
    try:
        supabase.table("inspecciones").insert(datos).execute()
        print("¡Inspección guardada exitosamente en la base de datos de Supabase!")
    except Exception as e:
        # Si la red falla o las credenciales no están listas, la consola imprimirá el error
        # pero el backend no se colgará y continuará generando el PDF para el técnico.
        print(f"Alerta: No se pudo registrar en Supabase de forma síncrona: {e}")

    # 3. Renderiza la plantilla en modo PDF pasando el diccionario de datos mapeados
    html = render_template(
        'pdf_template.html',
        es_pdf=True,
        datos_post=datos,
        **datos  # Mantiene tu desempaquetado original para alimentar orden, placa, modelo, etc.
    )

    # 4. Crea un archivo temporal seguro para depositar el binario del PDF
    pdf_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    # Convierte el HTML estructurado en PDF con WeasyPrint
    HTML(
        string=html,
        base_url=request.url_root
    ).write_pdf(pdf_file.name)

    # 5. Devuelve el archivo para su descarga inmediata usando la placa en el nombre
    return send_file(
        pdf_file.name,
        as_attachment=True,
        download_name=f"Prueba_Ruta_{datos.get('placa', 'VW')}.pdf"
    )

if __name__ == '__main__':
    app.run(debug=True)
