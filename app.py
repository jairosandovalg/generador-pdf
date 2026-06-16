from flask import Flask, render_template, request, send_file

app = Flask(__name__)

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/generar", methods=["POST"])
def generar():

    datos = request.form.to_dict()

    print(datos)

    return "PDF generado"

if __name__ == "__main__":
    app.run(debug=True)
