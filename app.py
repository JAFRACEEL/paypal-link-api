from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ API PayPal activa"

@app.route('/generar_link', methods=['POST'])
def generar_link():
    data = request.get_json()
    id_pago = data.get("id_pago")

    if not id_pago:
        return jsonify({"error": "Falta el parámetro 'id_pago'"}), 400

    link_paypal = f"https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-63387215JM106504CNA3AAGA&custom_id={id_pago}"

    return jsonify({
        "id_pago": id_pago,
        "link": link_paypal
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
