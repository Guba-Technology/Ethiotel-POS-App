import json

import requests

from frappe.utils import get_datetime, now_datetime

import frappe


class EIMSConnectorAuth:
    def get_valid_token(self, force_refresh=False):
        if (not force_refresh and self.settings.current_access_token
                and self.settings.token_expiry
                and get_datetime(self.settings.token_expiry) > now_datetime()):
            return self.settings.current_access_token

        default_client = self.get_default_client_data()

        decrypted_id = default_client.get_password("client_id")
        decrypted_secret = default_client.get_password("client_secret")
        decrypted_apikey = self.settings.get_password("api_key")

        payload = {
            "clientId": decrypted_id,
            "clientSecret": decrypted_secret,
            "apikey": decrypted_apikey,
            "tin": self.settings.seller_tin
        }

        clean_url = self.settings.base_url.strip().rstrip('/')
        login_url = f"{clean_url}/auth/login"

        json_string = json.dumps(payload, separators=(",", ":"))

        envelope_string = self._build_signed_envelope(json_string, default_client)
        response = requests.post(
            login_url,
            data=envelope_string.encode("utf-8"),
            headers=self.headers,
            timeout=15,
            verify=False
        )

        if response.status_code == 200:
            res_data = response.json()
            token = res_data.get("data", {}).get("accessToken")

            self.settings.current_access_token = token
            self.settings.token_expiry = frappe.utils.add_to_date(now_datetime(), minutes=60)
            self.settings.save(ignore_permissions=True)
            frappe.db.commit()

            return token
        else:
            frappe.throw(f"EIMS Authentication Failed (Status {response.status_code}): {response.text}")
