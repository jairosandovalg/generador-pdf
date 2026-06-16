from flask import Flask, render_template, request, send_file
from weasyprint import HTML
import tempfile

app = Flask(__name__)

@app.route('/')
def home():
    # En la raíz del sitio web cargamos la plantilla indicando que NO es un PDF.
    # Esto mostrará los inputs limpios y listos para escribir.
    return render_template('pdf_template.html', es_pdf=False)

@app.route('/generar', methods=['POST'])
def generar():
    datos = request.form.to_dict()

    # Volvemos a renderizar la misma plantilla, pero pasándole los datos y activando es_pdf=True
    html = render_template(
        'pdf_template.html',
        es_pdf=True,
        datos_post=datos,
        **datos # Desempaqueta variables directas como orden, placa, etc.
    )

    pdf_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    # Convertimos a PDF conservando las fuentes y los estilos agregados en la sección <style>
    HTML(
        string=html,
        base_url=request.url_root
    ).write_pdf(pdf_file.name)

    return send_file(
        pdf_file.name,
        as_attachment=True,
        download_name=f"Prueba_Ruta_{datos.get('placa', 'VW')}.pdf"
    )

if __name__ == '__main__':
    app.run(debug=True)
