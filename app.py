from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Configuración de PayPal
PLAN_ID = "P-63387215JM106504CNA3AAGA"  # ← Tu plan real
CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

def obtener_access_token():
    url = "https://api-m.paypal.com/v1/oauth2/token"
    auth = (CLIENT_ID, CLIENT_SECRET)
    headers = {"Accept": "application/json"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data, auth=auth)
    return response.json()["access_token"]

@app.route('/')
def home():
    return "✅ API PayPal activa"

@app.route('/generar_link', methods=['POST'])
def generar_link():
    data = request.get_json()
    id_pago = data.get("id_pago")

    if not id_pago:
        return jsonify({"error": "Falta el parámetro 'id_pago'"}), 400

    access_token = obtener_access_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "plan_id": PLAN_ID,
        "custom_id": id_pago,
        "application_context": {
            "brand_name": "MedicVida",
            "locale": "es-PE",
            "user_action": "SUBSCRIBE_NOW",
            "shipping_preference": "NO_SHIPPING",
            "return_url": "https://tuapp.com/gracias",
            "cancel_url": "https://tuapp.com/cancelado"
        }
    }

    response = requests.post(
        "https://api-m.paypal.com/v1/billing/subscriptions",
        headers=headers,
        json=payload
    )

    if response.status_code != 201:
        return jsonify({
            "error": "No se pudo crear la suscripción",
            "detalle": response.json()
        }), 500

    resp_json = response.json()
    approve_url = next((link["href"] for link in resp_json["links"] if link["rel"] == "approve"), None)

    return jsonify({
        "id_pago": id_pago,
        "subscription_id": resp_json.get("id"),
        "approve_url": approve_url
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
