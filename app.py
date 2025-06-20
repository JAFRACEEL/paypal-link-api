from flask import Flask, request, jsonify
import requests
import os
import json
import gspread
from io import StringIO
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Configuración de PayPal
PLAN_ID = "P-63387215JM106504CNA3AAGA"
CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

# Configuración de Google Sheets
SHEET_NAME = "MEDICINAS_GRATIS"
TABLA = "PAGOS_EN_CURSO"

def obtener_access_token():
    url = "https://api-m.paypal.com/v1/oauth2/token"
    auth = (CLIENT_ID, CLIENT_SECRET)
    headers = {"Accept": "application/json"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data, auth=auth)
    return response.json()["access_token"]

def actualizar_link_en_google_sheets(id_pago, link):
    scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
    cred_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if not cred_json:
        raise Exception("GOOGLE_CREDENTIALS_JSON no está definido")

    info = json.loads(cred_json)
    credentials = Credentials.from_service_account_info(info, scopes=scope)
    gc = gspread.authorize(credentials)

    sheet = gc.open(SHEET_NAME).worksheet(TABLA)
    records = sheet.get_all_records()

    for i, row in enumerate(records, start=2):  # Fila 2 por encabezado
        if row.get("IDPAGO") == id_pago:
            col_index = list(row.keys()).index("LINK_PAYPAL") + 1
            sheet.update_cell(i, col_index, link)
            return True
    return False

@app.route('/')
def home():
    return "✅ API PayPal activa"

@app.route('/generar_link', methods=['POST'])
def generar_link():
    data = request.get_json()
    id_pago = data.get("id_pago")

    if not id_pago:
        return jsonify({"error": "Falta el parámetro 'id_pago'"}), 400

    try:
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

        # Manejo seguro de error al actualizar Google Sheets
        try:
            actualizado = actualizar_link_en_google_sheets(id_pago, approve_url)
        except Exception as e:
            return jsonify({
                "id_pago": id_pago,
                "subscription_id": resp_json.get("id"),
                "approve_url": approve_url,
                "error_google_sheet": str(e)
            }), 200

        return jsonify({
            "id_pago": id_pago,
            "subscription_id": resp_json.get("id"),
            "approve_url": approve_url,
            "actualizado_en_google_sheets": actualizado
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)

