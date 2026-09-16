import json
import frappe
from ethiotel_pos.eims.connector import EIMSConnector

frappe.connect('pos2.localhost')
try:
    # Temporarily override to HTTP for test
    s = frappe.get_single('EIMS Setting')
    original_url = s.base_url
    s.base_url = 'http://core.mor.gov.et'
    s.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"Testing with base_url = {s.base_url}")
    
    conn = EIMSConnector()
    doc = frappe.get_doc('Sales Invoice', 'ACC-SINV-2026-00072')
    
    # Clear any cached token to force fresh auth
    s.current_access_token = None
    s.token_expiry = None
    s.save(ignore_permissions=True)
    frappe.db.commit()
    
    result = conn.submit_single_invoice(doc.name)
    print("Result:", result)
finally:
    frappe.db.close()