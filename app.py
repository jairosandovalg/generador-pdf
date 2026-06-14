from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
import io
import os

# 🔌 Cargar las variables de entorno desde el archivo .env
load_dotenv()

# 🛠️ Configuración de rutas absolutas del proyecto
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)

# 🗄️ Configuración de la Base de Datos (Supabase / local)
# Si no encuentra DATABASE_URL en el .env, usará un archivo SQLite local por seguridad
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(base_dir, "reportes.db")}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 📊 Modelo de Datos: Estructura de la tabla para el posterior análisis
class Reporte(db.Model):
    __tablename__ = 'reportes'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    opcion_seleccionada = db.Column(db.String(100), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)  # Temporal para análisis cronológico

    def __repr__(self):
        return f'<Reporte {self.id} - {self.opcion_seleccionada}>'

# Creación automática de la tabla en Supabase si no existe
with app.app_context():
    db.create_all()


def crear_pdf_dinamico(buffer, titulo_usuario, opcion_seleccionada):
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

    # Ruta absoluta de la imagen
    ruta_imagen = os.path.join(base_dir, "logo.jpg")
    
    if os.path.exists(ruta_imagen):
        try:
            logo = Image(ruta_imagen, width=120, height=50)
            logo.hAlign = 'LEFT'
            story.append(logo)
            story.append(Spacer(1, 15))
        except Exception as e:
            print(f"Error al procesar la imagen: {e}")

    story.append(Paragraph(f"Reporte: {titulo_usuario}", estilo_titulo))
    story.append(Spacer(1, 10))
    
    texto_contenido = f"Este documento confirma que el usuario ha seleccionado la **{opcion_seleccionada}**. " \
                      f"Los datos han sido procesados y almacenados correctamente en el servidor en la sesión actual."
    
    story.append(Paragraph(texto_contenido, estilo_cuerpo))
    doc.build(story)


@app.route('/')
def index():
    return render_template('formulario.html')

@app.route('/generar', methods=['POST'])
def generar():
    titulo = request.form.get('titulo')
    opcion = request.form.get('tipo_opcion')
    
    print(f"\n--- Procesando Datos ---")
    print(f"Título: {titulo}")
    print(f"Opción: {opcion}")
    
    # 💾 1. ALMACENAR EN LA BASE DE DATOS DE SUPABASE
    try:
        nuevo_reporte = Reporte(titulo=titulo, opcion_seleccionada=opcion)
        db.session.add(nuevo_reporte)
        db.session.commit()
        print("✅ Registro guardado exitosamente en Supabase.")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al guardar en la base de datos: {e}")
    
    # 📄 2. GENERAR Y RETORNAR EL ARCHIVO PDF
    buffer = io.BytesIO()
    crear_pdf_dinamico(buffer, titulo, opcion)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte_configurado.pdf",
        mimetype="application/pdf"
    )

# 🔓 Endpoint API: Para extraer los datos con Pandas para tu análisis
@app.route('/api/datos')
def obtener_datos():
    reportes = Reporte.query.all()
    resultado = [
        {
            "id": r.id, 
            "titulo": r.titulo, 
            "opcion": r.opcion_seleccionada, 
            "fecha": r.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
        } 
        for r in reportes
    ]
    return {"data": resultado}

if __name__ == '__main__':
    app.run(debug=True)