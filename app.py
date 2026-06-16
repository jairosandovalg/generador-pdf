from flask import Flask, render_template, request, send_file
from weasyprint import HTML
import tempfile

# 1. Creamos la instancia de la aplicación Flask (Esencial para que Gunicorn la encuentre)
app = Flask(__name__)

# 2. Ahora sí podemos usar el decorador @app.route porque 'app' ya existe
@app.route('/generar', methods=['POST'])
def generar():

    datos = request.form.to_dict()

    html = render_template(
        'pdf_template.html',
        **datos
    )

    pdf_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    HTML(
        string=html,
        base_url=request.url_root
    ).write_pdf(pdf_file.name)

    return send_file(
        pdf_file.name,
        as_attachment=True,
        download_name="Prueba_Ruta_VW.pdf"
    )

# Opcional: Esto te permite correr el archivo localmente con 'python app.py' para hacer pruebas
if __name__ == '__main__':
    app.run(debug=True)
