"""
Open Dental integration — modular connector.
Default workflow: copy to clipboard (safe, no direct DB writes).
Optional: REST API write-back when credentials are configured.
Any chart insertion REQUIRES explicit user confirmation.
"""
import json
import urllib.request
import urllib.error
from typing import Any


class OpenDentalConnector:
    """
    Wraps the Open Dental REST API.
    API docs: https://www.opendental.com/manual/apiintroduction.html
    The API must be enabled in Open Dental: Setup > API > Enable.
    """

    def __init__(self, base_url: str, developer_key: str, customer_key: str = ""):
        # base_url example: "http://localhost:8027"
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {developer_key}",
        }
        if customer_key:
            self.headers["CustomerKey"] = customer_key

    def _request(self, method: str, path: str, body: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Open Dental API error {e.code}: {e.read().decode()}") from e
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot reach Open Dental API at {self.base_url}. "
                "Ensure Open Dental is running with the API enabled."
            ) from e

    def get_patient(self, patient_num: int) -> dict:
        return self._request("GET", f"/api/v1/patients/{patient_num}")

    def search_patients(self, last_name: str = "", first_name: str = "") -> list[dict]:
        params = f"?LName={last_name}&FName={first_name}"
        return self._request("GET", f"/api/v1/patients{params}")

    def insert_progress_note(
        self,
        patient_num: int,
        note_text: str,
        proc_date: str,          # "YYYY-MM-DD"
        provider_num: int = 0,
        confirmed: bool = False,  # Must be True; caller must obtain user confirmation.
    ) -> dict:
        if not confirmed:
            raise PermissionError(
                "Chart insertion requires explicit user confirmation. "
                "Set confirmed=True only after the user has approved."
            )
        body = {
            "PatNum": patient_num,
            "Note": note_text,
            "ProcDate": proc_date,
            "ProvNum": provider_num,
        }
        return self._request("POST", "/api/v1/procnotes", body)

    def test_connection(self) -> bool:
        try:
            self._request("GET", "/api/v1/patients?limit=1")
            return True
        except Exception:
            return False

    def send_chart_note(self, patient_id: str, note_text: str) -> tuple[bool, str]:
        try:
            result = self.add_proc_note(patient_id, note_text)
            return True, str(result)
        except Exception as exc:
            return False, str(exc)


def connector_from_config(cfg: dict) -> OpenDentalConnector | None:
    """Build a connector from the settings dict. Returns None if not configured."""
    url = cfg.get("od_api_url", "")
    dev_key = cfg.get("od_developer_key", "")
    if not url or not dev_key:
        return None
    return OpenDentalConnector(
        base_url=url,
        developer_key=dev_key,
        customer_key=cfg.get("od_customer_key", ""),
    )
