import json
import requests
from frappe.utils import get_datetime, now_datetime
import frappe

class EIMSConnectorAuth:
    def get_valid_token(self, force_refresh=False):
        default_client = self.get_default_client_data()
        current_sys = (default_client.system_number or "").strip()
        cached_sys = (getattr(self.settings, "token_system_number", "") or "").strip()

        if (not force_refresh and self.settings.current_access_token
                and self.settings.token_expiry
                and get_datetime(self.settings.token_expiry) > now_datetime()
                and cached_sys == current_sys):
            return self.settings.current_access_token

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
        data_bytes = json_string.encode("utf-8")

        is_https = login_url.lower().startswith("https://")

        if is_https:
            envelope_string = self._build_signed_envelope(json_string, default_client)
            response = requests.post(
                login_url,
                data=envelope_string.encode("utf-8"),
                headers=self.headers,
                timeout=15,
                verify=False
            )
            print(f"Request to {login_url} sent with signed envelope. Response status: {response.status_code}")
        else:
            response = requests.post(
                login_url,
                data=data_bytes,
                headers=self.headers,
                timeout=10
            )
            print(f"Request to {login_url} sent. Response status: {response.status_code}")

        if response.status_code == 200:
            res_data = response.json()
            token = res_data.get("data", {}).get("accessToken")

            self.settings.current_access_token = token
            self.settings.token_system_number = current_sys
            self.settings.token_expiry = frappe.utils.add_to_date(now_datetime(), minutes=60)
            self.settings.save(ignore_permissions=True)
            frappe.db.commit()

            return token
        else:
            frappe.throw(f"EIMS Authentication Failed (Status {response.status_code}): {response.text}")
