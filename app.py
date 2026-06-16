from flask import Flask, render_template, request, send_file
from weasyprint import HTML
import tempfile

# 1. Inicialización de la aplicación Flask
app = Flask(__name__)

# 2. Ruta de inicio (GET /) - Evita el error "Not Found" en el navegador
@app.route('/')
def home():
    return "El servidor de PDFs está activo. Envía un POST a /generar para crear un PDF."

# 3. Ruta para generar el PDF (POST /generar)
@app.route('/generar', methods=['POST'])
def generar():
    # Obtiene los datos enviados desde el formulario o cliente HTTP
    datos = request.form.to_dict()

    # Renderiza la plantilla HTML pasándole los datos recibidos
    html = render_template(
        'pdf_template.html',
        **datos
    )

    # Crea un archivo temporal seguro para almacenar el PDF antes de enviarlo
    pdf_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    # Usa WeasyPrint para transformar el HTML renderizado en un documento PDF
    HTML(
        string=html,
        base_url=request.url_root
    ).write_pdf(pdf_file.name)

    # Retorna el archivo PDF generado como una descarga para el usuario
    return send_file(
        pdf_file.name,
        as_attachment=True,
        download_name="Prueba_Ruta_VW.pdf"
    )

# 4. Bloque de ejecución local (opcional para pruebas en tu PC con 'python app.py')
if __name__ == '__main__':
    app.run(debug=True)
