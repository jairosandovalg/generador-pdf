from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)

@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/generar", methods=["POST"])
def generar():

    datos = request.form.to_dict()

    archivo_pdf = "pdfs/prueba_ruta.pdf"

    os.makedirs("pdfs", exist_ok=True)

    c = canvas.Canvas(archivo_pdf, pagesize=A4)

    ancho, alto = A4

    y = alto - 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(150, y, "PRUEBA DE RUTA VOLKSWAGEN")

    y -= 40

    c.setFont("Helvetica", 10)

    c.drawString(40, y, f"N° Orden: {datos.get('orden','')}")
    c.drawString(220, y, f"Placa: {datos.get('placa','')}")

    y -= 20

    c.drawString(40, y, f"Modelo: {datos.get('modelo','')}")
    c.drawString(220, y, f"Motor: {datos.get('motor','')}")

    y -= 20

    c.drawString(40, y, f"Km Prueba: {datos.get('km','')}")

    y -= 40

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "1. ILUMINACION")

    y -= 20

    c.setFont("Helvetica", 10)

    c.drawString(
        50,
        y,
        f"Exterior: {datos.get('exterior','')}"
    )

    y -= 15

    c.drawString(
        50,
        y,
        f"Solucion: {datos.get('solucion_exterior','')}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Interior: {datos.get('interior','')}"
    )

    y -= 15

    c.drawString(
        50,
        y,
        f"Solucion: {datos.get('solucion_interior','')}"
    )

    y -= 30

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "2. INTERIOR")

    y -= 20

    c.setFont("Helvetica", 10)

    campos = [
        ("Claxon", "claxon"),
        ("Limpiaparabrisas", "limpia"),
        ("AC", "ac"),
        ("Cinturones", "cinturones"),
        ("Airbag", "airbag"),
        ("Radio", "radio"),
        ("RPM", "rpm"),
        ("Ruido Interior", "ruido")
    ]

    for titulo, campo in campos:

        c.drawString(
            50,
            y,
            f"{titulo}: {datos.get(campo,'')}"
        )

        y -= 18

        if y < 100:
            c.showPage()
            y = alto - 40

    secciones = [
        ("3. MOTOR", "motor_obs"),
        ("4. CAJA AUTOMATICA", "caja_auto"),
        ("5. CAJA MANUAL", "caja_manual"),
        ("6. SISTEMA DE FRENOS", "frenos"),
        ("7. DIRECCION Y SUSPENSION", "direccion"),
        ("OBSERVACIONES", "observaciones")
    ]

    for titulo, campo in secciones:

        y -= 15

        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, titulo)

        y -= 18

        c.setFont("Helvetica", 10)

        texto = datos.get(campo, "")

        c.drawString(50, y, texto)

        y -= 25

        if y < 100:
            c.showPage()
            y = alto - 40

    y -= 20

    c.drawString(
        40,
        y,
        f"Tecnico: {datos.get('tecnico','')}"
    )

    y -= 20

    c.drawString(
        40,
        y,
        f"Fecha: {datos.get('fecha','')}"
    )

    c.save()

    return send_file(
        archivo_pdf,
        as_attachment=True,
        download_name="Prueba_Ruta_VW.pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)
