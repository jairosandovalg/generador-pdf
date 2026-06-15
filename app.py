from flask import Flask, render_template, request, send_file

# ==============================
# BASE DE DATOS (DESHABILITADA)
# ==============================

# from flask_sqlalchemy import SQLAlchemy
# from dotenv import load_dotenv

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image
)
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib import colors

# from datetime import datetime

import io
import os

# =====================================
# VARIABLES DE ENTORNO (DESHABILITADO)
# =====================================

# load_dotenv()

# =====================================
# CONFIGURACIÓN DE LA APLICACIÓN
# =====================================

base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(
    __name__,
    template_folder=template_dir
)

# =====================================
# CONFIGURACIÓN SUPABASE (DESHABILITADA)
# =====================================

# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
#     'DATABASE_URL',
#     f'sqlite:///{os.path.join(base_dir, "reportes.db")}'
# )

# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)

# =====================================
# MODELO DE DATOS (DESHABILITADO)
# =====================================

# class Reporte(db.Model):
#
#     __tablename__ = 'reportes'
#
#     id = db.Column(
#         db.Integer,
#         primary_key=True
#     )
#
#     titulo = db.Column(
#         db.String(150),
#         nullable=False
#     )
#
#     opcion_seleccionada = db.Column(
#         db.String(100),
#         nullable=False
#     )
#
#     fecha_creacion = db.Column(
#         db.DateTime,
#         default=datetime.utcnow
#     )
#
#     def __repr__(self):
#         return f'<Reporte {self.id}>'

# =====================================
# CREAR TABLAS (DESHABILITADO)
# =====================================

# with app.app_context():
#     db.create_all()

# =====================================
# GENERADOR PDF
# =====================================

def crear_pdf_dinamico(
    buffer,
    titulo_usuario,
    opcion_seleccionada
):

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'TituloPDF',
        parent=estilos['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=20
    )

    estilo_cuerpo = ParagraphStyle(
        'CuerpoPDF',
        parent=estilos['Normal'],
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#2D3748")
    )

    story = []

    ruta_imagen = os.path.join(
        base_dir,
        "logo.jpg"
    )

    if os.path.exists(ruta_imagen):

        try:

            logo = Image(
                ruta_imagen,
                width=120,
                height=50
            )

            logo.hAlign = 'LEFT'

            story.append(logo)
            story.append(Spacer(1, 15))

        except Exception as e:

            print(
                f"Error al cargar logo: {e}"
            )

    story.append(
        Paragraph(
            f"Reporte: {titulo_usuario}",
            estilo_titulo
        )
    )

    story.append(
        Spacer(1, 10)
    )

    texto = f"""
    Este documento confirma que el usuario seleccionó la opción:
    <b>{opcion_seleccionada}</b>.
    <br/><br/>
    El PDF fue generado correctamente.
    """

    story.append(
        Paragraph(
            texto,
            estilo_cuerpo
        )
    )

    doc.build(story)

# =====================================
# RUTA PRINCIPAL
# =====================================

@app.route('/')
def index():

    return render_template(
        'formulario.html'
    )

# =====================================
# GENERAR PDF
# =====================================

@app.route(
    '/generar',
    methods=['POST']
)
def generar():

    titulo = request.form.get(
        'titulo'
    )

    opcion = request.form.get(
        'tipo_opcion'
    )

    print("\n--- DATOS RECIBIDOS ---")
    print(f"Titulo: {titulo}")
    print(f"Opcion: {opcion}")

    # =====================================
    # GUARDAR EN SUPABASE (DESHABILITADO)
    # =====================================

    # try:
    #
    #     nuevo_reporte = Reporte(
    #         titulo=titulo,
    #         opcion_seleccionada=opcion
    #     )
    #
    #     db.session.add(
    #         nuevo_reporte
    #     )
    #
    #     db.session.commit()
    #
    #     print(
    #         "Registro guardado correctamente"
    #     )
    #
    # except Exception as e:
    #
    #     db.session.rollback()
    #
    #     print(
    #         f"Error BD: {e}"
    #     )

    buffer = io.BytesIO()

    crear_pdf_dinamico(
        buffer,
        titulo,
        opcion
    )

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='reporte_configurado.pdf',
        mimetype='application/pdf'
    )

# =====================================
# API DATOS (DESHABILITADA)
# =====================================

# @app.route('/api/datos')
# def obtener_datos():
#
#     reportes = Reporte.query.all()
#
#     resultado = [
#         {
#             "id": r.id,
#             "titulo": r.titulo,
#             "opcion": r.opcion_seleccionada,
#             "fecha": r.fecha_creacion.strftime(
#                 '%Y-%m-%d %H:%M:%S'
#             )
#         }
#         for r in reportes
#     ]
#
#     return {
#         "data": resultado
#     }

# =====================================
# INICIO DE APLICACIÓN
# =====================================

if __name__ == '__main__':

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
