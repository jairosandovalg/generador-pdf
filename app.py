from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import os

app = Flask(__name__)

def crear_pdf_dinamico(buffer, titulo_usuario, opcion_seleccionada):
    # Crear el documento usando el buffer en memoria
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    estilos = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle(
        'TituloPDF',
        parent=estilos['Heading1'],
        fontSize=24, leading=28, textColor=colors.HexColor("#1A365D"), spaceAfter=20
    )
    
    estilo_cuerpo = ParagraphStyle(
        'CuerpoPDF',
        parent=estilos['Normal'],
        fontSize=12, leading=18, textColor=colors.HexColor("#2D3748")
    )

    story = []

    # 🖼️ COLOCO LA IMAGEN AL INICIO DEL DOCUMENTO
    ruta_imagen = "logo.jpg"
    if os.path.exists(ruta_imagen):
        # Ajusta el ancho (width) y alto (height) en puntos (1 pulgada = 72 puntos)
        logo = Image(ruta_imagen, width=120, height=50)
        logo.hAlign = 'LEFT' # Alineación de la imagen
        story.append(logo)
        story.append(Spacer(1, 15)) # Espacio debajo de la imagen
    else:
        print(f"Advertencia: No se encontró la imagen en {ruta_imagen}")

    # Contenido del reporte
    story.append(Paragraph(f"Reporte: {titulo_usuario}", estilo_titulo))
    story.append(Spacer(1, 10))
    
    texto_contenido = f"Este documento confirma que el usuario ha seleccionado la **{opcion_seleccionada}**. " \
                      f"Los datos han sido procesados y almacenados correctamente en el servidor en la sesión actual."
    
    story.append(Paragraph(texto_contenido, estilo_cuerpo))
    
    # Construir el PDF
    doc.build(story)

@app.route('/')
def index():
    return render_template('formulario.html')

@app.route('/generar', methods=['POST'])
def generar():
    titulo = request.form.get('titulo')
    opcion = request.form.get('tipo_opcion')
    
    print(f"\n--- Datos Recibidos ---")
    print(f"Título: {titulo}")
    print(f"Opción Seleccionada: {opcion}\n-----------------------\n")
    
    # Crear un buffer en memoria para evitar guardar archivos físicos en el servidor
    buffer = io.BytesIO()
    
    # Generar el PDF directamente en el buffer
    crear_pdf_dinamico(buffer, titulo, opcion)
    
    # Mover el puntero del buffer al inicio para que pueda ser leído por Flask
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte_configurado.pdf",
        mimetype="application/pdf"
    )

if __name__ == '__main__':
    app.run(debug=True)