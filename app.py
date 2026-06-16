from flask import Flask, render_template, request, send_file
from weasyprint import HTML
import tempfile

app = Flask(__name__)

@app.route('/')
def home():
    # Carga el formulario web interactivo desactivando el modo PDF
    return render_template('pdf_template.html', es_pdf=False)

@app.route('/generar', methods=['POST'])
def generar():
    # Captura todos los datos enviados desde el formulario web
    datos = request.form.to_dict()

    # Renderiza la misma plantilla activa en modo PDF pasando los datos correspondientes
    html = render_template(
        'pdf_template.html',
        es_pdf=True,
        datos_post=datos,
        **datos  # Envía variables sueltas como orden, placa, modelo, etc.
    )

    # Crea un archivo temporal seguro para depositar el binario del PDF
    pdf_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    # Convierte el HTML generado en PDF interpretando los estilos CSS internos
    HTML(
        string=html,
        base_url=request.url_root
    ).write_pdf(pdf_file.name)

    # Devuelve el PDF listo para su descarga nombrando el archivo con la placa del vehículo
    return send_file(
        pdf_file.name,
        as_attachment=True,
        download_name=f"Prueba_Ruta_{datos.get('placa', 'VW')}.pdf"
    )

if __name__ == '__main__':
    app.run(debug=True)
