import json
import requests
from frappe.utils import get_datetime, now_datetime
import frappe

from .logging_setup import eims_logger
from .sanitize import redact_payload

class EIMSConnectorAuth:
    def get_valid_token(self, force_refresh=False):
        default_client = self.get_default_client_data()
        current_sys = (default_client.system_number or "").strip()
        cached_sys = (getattr(self.settings, "token_system_number", "") or "").strip()

        cached_token = self._get_cached_token()

        if (not force_refresh and cached_token
                and self.settings.token_expiry
                and get_datetime(self.settings.token_expiry) > now_datetime()
                and cached_sys == current_sys):
            return cached_token

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
        verify_tls = self._verify_tls()

        if is_https:
            envelope_string = self._build_signed_envelope(json_string, default_client)
            response = requests.post(
                login_url,
                data=envelope_string.encode("utf-8"),
                headers=self.headers,
                timeout=15,
                verify=verify_tls
            )
            eims_logger.debug(f"Request to {login_url} sent with signed envelope. Response status: {response.status_code}")
        else:
            response = requests.post(
                login_url,
                data=data_bytes,
                headers=self.headers,
                timeout=10
            )
            eims_logger.debug(f"Request to {login_url} sent. Response status: {response.status_code}")

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
            frappe.throw(f"EIMS Authentication Failed (Status {response.status_code}): {redact_payload(response.text)}")

    def _get_cached_token(self):
        """Read the cached MoR bearer token. The field is a Password field, so
        the raw attribute holds an encrypted value - always decrypt via
        get_password so the plaintext token is never materialised twice."""
        if not self.settings.current_access_token:
            return None
        try:
            return self.settings.get_password("current_access_token")
        except Exception:
            return None

    def _verify_tls(self):
        """Return whether TLS certificate verification should be enforced for
        MoR HTTPS calls. Defaults to secure (True). A site/system manager can
        disable it only via a dedicated flag, never silently."""
        flag = getattr(self.settings, "verify_tls", None)
        if flag is None:
            return frappe.conf.get("eims_verify_tls", True)
        return bool(flag)
