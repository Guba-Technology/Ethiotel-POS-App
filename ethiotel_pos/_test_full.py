import requests
import json
import frappe

frappe.connect('pos2.localhost')
try:
    s = frappe.get_single('EIMS Setting')
    clients = frappe.db.sql("SELECT name FROM `tabClient Data` WHERE is_default=1", as_dict=True)
    cd = frappe.get_doc('Client Data', clients[0].name)

    decrypted_id = cd.get_password("client_id")
    decrypted_secret = cd.get_password("client_secret")
    decrypted_apikey = s.get_password("api_key")
    payload = {"clientId": decrypted_id, "clientSecret": decrypted_secret, "apikey": decrypted_apikey, "tin": s.seller_tin}
    json_auth = json.dumps(payload, separators=(",", ":"))

    print("=== 1. Auth HTTP ===")
    r = requests.post("http://core.mor.gov.et/auth/login", data=json_auth.encode("utf-8"), 
                      headers={"Content-Type": "application/json"}, timeout=15)
    print("Auth status:", r.status_code)
    if r.status_code != 200:
        print("Auth failed:", r.text[:300])
        exit()
    token = r.json()["data"]["accessToken"]
    print("Token OK")

    from ethiotel_pos.eims.connector import EIMSConnector
    conn = EIMSConnector()
    doc = frappe.get_doc('Sales Invoice', 'ACC-SINV-2026-00072')

    # Test doc 201
    print("\n=== Register doc 201 ===")
    invoice_payload = conn.build_invoice_payload(doc, override_doc_num=201)
    json_string = json.dumps(invoice_payload, separators=(",", ":"))
    print(f"Payload doc number: {invoice_payload.get('DocumentDetails', {}).get('DocumentNumber')}")

    r = requests.post(
        "http://core.mor.gov.et/v1/register",
        data=json_string.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "apikey": decrypted_apikey,
        },
        timeout=60,
    )
    print("Register status:", r.status_code)
    print("Register body:", r.text[:1500])
finally:
    frappe.db.close()