from flask import render_template
from weasyprint import HTML
import tempfile

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
