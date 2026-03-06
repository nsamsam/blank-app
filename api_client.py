import requests
import pandas as pd
from datetime import datetime


class PetroVaultClient:
    """Client for connecting to PetroVault Public API."""

    def __init__(self, base_url, api_key="", auth_token="", auth_type="bearer"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.auth_token = auth_token
        self.auth_type = auth_type
        self.session = requests.Session()
        self._set_auth()

    def _set_auth(self):
        if self.auth_type == "bearer" and self.auth_token:
            self.session.headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.auth_type == "api_key" and self.api_key:
            self.session.headers["X-API-Key"] = self.api_key
        elif self.auth_type == "basic" and self.auth_token:
            self.session.headers["Authorization"] = f"Basic {self.auth_token}"

    def test_connection(self):
        """Test if the API is reachable."""
        try:
            resp = self.session.get(f"{self.base_url}", timeout=10)
            return resp.status_code, resp.text[:500]
        except requests.exceptions.ConnectionError as e:
            return None, f"Connection error: {e}"
        except requests.exceptions.Timeout:
            return None, "Connection timed out"
        except Exception as e:
            return None, str(e)

    def get(self, endpoint, params=None):
        """Make a GET request to an API endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json(), None
        except requests.exceptions.HTTPError as e:
            return None, f"HTTP {resp.status_code}: {resp.text[:300]}"
        except requests.exceptions.JSONDecodeError:
            return resp.text, None
        except Exception as e:
            return None, str(e)

    def post(self, endpoint, data=None, json_data=None):
        """Make a POST request to an API endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.post(url, data=data, json=json_data, timeout=30)
            resp.raise_for_status()
            return resp.json(), None
        except requests.exceptions.HTTPError as e:
            return None, f"HTTP {resp.status_code}: {resp.text[:300]}"
        except requests.exceptions.JSONDecodeError:
            return resp.text, None
        except Exception as e:
            return None, str(e)

    def fetch_data_as_df(self, endpoint, params=None):
        """Fetch data from endpoint and return as DataFrame."""
        data, error = self.get(endpoint, params)
        if error:
            return None, error
        if isinstance(data, list):
            return pd.DataFrame(data), None
        elif isinstance(data, dict):
            # Try common response patterns
            for key in ["data", "results", "items", "records", "value", "rows"]:
                if key in data and isinstance(data[key], list):
                    return pd.DataFrame(data[key]), None
            return pd.DataFrame([data]), None
        return None, "Unexpected response format"


def create_client(config_row):
    """Create a PetroVaultClient from a database config row."""
    return PetroVaultClient(
        base_url=config_row["base_url"],
        api_key=config_row.get("api_key", ""),
        auth_token=config_row.get("auth_token", ""),
        auth_type=config_row.get("auth_type", "bearer"),
    )
