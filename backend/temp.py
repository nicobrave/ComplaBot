from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    input_value = data.get("input", "sin valor")

    respuesta = {
        "mensaje": f"Recibido: {input_value}",
        "recomendacion": "✔️ Todo funcionando con Flask + n8n"
    }

    return jsonify(respuesta), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)


