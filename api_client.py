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
        """Test if the API is reachable using the health endpoint."""
        try:
            resp = self.session.get(f"{self.base_url}/v1/info/health", timeout=10)
            return resp.status_code, resp.text[:500]
        except requests.exceptions.ConnectionError as e:
            return None, f"Connection error: {e}"
        except requests.exceptions.Timeout:
            return None, "Connection timed out"
        except Exception as e:
            return None, str(e)

    def _get(self, endpoint, params=None):
        """Make a GET request to an API endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json(), None
        except requests.exceptions.HTTPError:
            return None, f"HTTP {resp.status_code}: {resp.text[:300]}"
        except requests.exceptions.JSONDecodeError:
            return resp.text, None
        except Exception as e:
            return None, str(e)

    def _post(self, endpoint, json_data=None):
        """Make a POST request to an API endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.post(url, json=json_data, timeout=30)
            resp.raise_for_status()
            return resp.json(), None
        except requests.exceptions.HTTPError:
            return None, f"HTTP {resp.status_code}: {resp.text[:300]}"
        except requests.exceptions.JSONDecodeError:
            return resp.text, None
        except Exception as e:
            return None, str(e)

    def get(self, endpoint, params=None):
        """Public GET for custom endpoint calls."""
        return self._get(endpoint, params)

    def post(self, endpoint, data=None, json_data=None):
        """Public POST for custom endpoint calls."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.post(url, data=data, json=json_data, timeout=30)
            resp.raise_for_status()
            return resp.json(), None
        except requests.exceptions.HTTPError:
            return None, f"HTTP {resp.status_code}: {resp.text[:300]}"
        except requests.exceptions.JSONDecodeError:
            return resp.text, None
        except Exception as e:
            return None, str(e)

    # ── Info Endpoints ──────────────────────────────────────────

    def get_version(self):
        """GET /v1/info/version"""
        return self._get("v1/info/version")

    def get_health(self):
        """GET /v1/info/health"""
        return self._get("v1/info/health")

    # ── Well Model Endpoints ────────────────────────────────────

    def get_wells(self, page=None, page_size=None):
        """GET /v1/wellmodel/wells - Gets all wells as a paged list."""
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size
        return self._get("v1/wellmodel/wells", params or None)

    def get_wellbores(self, well=None, page=None, page_size=None):
        """GET /v1/wellmodel/wellbores or /v1/wellmodel/wellbores/{well}"""
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size
        if well:
            return self._get(f"v1/wellmodel/wellbores/{well}", params or None)
        return self._get("v1/wellmodel/wellbores", params or None)

    def get_logs(self, well=None, wellbore=None, log=None, page=None, page_size=None):
        """GET /v1/wellmodel/logs with optional well/wellbore/log filters."""
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size
        if well and wellbore and log:
            return self._get(f"v1/wellmodel/logs/{well}/{wellbore}/{log}", params or None)
        elif well and wellbore:
            return self._get(f"v1/wellmodel/logs/{well}/{wellbore}", params or None)
        elif well:
            return self._get(f"v1/wellmodel/logs/{well}", params or None)
        return self._get("v1/wellmodel/logs", params or None)

    # ── Channel Data Endpoints ──────────────────────────────────

    def get_channel_data_latest(self, log_id, channels=None, max_rows=None):
        """GET /v1/channels/data/latest - Gets latest channel data from a log."""
        params = {"logId": log_id}
        if channels:
            params["channels"] = channels
        if max_rows is not None:
            params["maxRows"] = max_rows
        return self._get("v1/channels/data/latest", params)

    def get_channel_data_range(self, log_id, start=None, end=None, channels=None, max_rows=None):
        """GET /v1/channels/data/range - Gets a range of channel data."""
        params = {"logId": log_id}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if channels:
            params["channels"] = channels
        if max_rows is not None:
            params["maxRows"] = max_rows
        return self._get("v1/channels/data/range", params)

    def get_channel_report_range(self, log_id, start=None, end=None, channels=None, max_rows=None):
        """GET /v1/channels/report/range - Gets range data in report format."""
        params = {"logId": log_id}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if channels:
            params["channels"] = channels
        if max_rows is not None:
            params["maxRows"] = max_rows
        return self._get("v1/channels/report/range", params)

    def get_channel_report_latest(self, log_id, channels=None, max_rows=None):
        """GET /v1/channels/report/latest - Gets latest data in report format."""
        params = {"logId": log_id}
        if channels:
            params["channels"] = channels
        if max_rows is not None:
            params["maxRows"] = max_rows
        return self._get("v1/channels/report/latest", params)

    def post_channel_data(self, json_data):
        """POST /v1/channels/data - Updates data for a log object."""
        return self._post("v1/channels/data", json_data)

    # ── Resource Endpoints ──────────────────────────────────────

    def get_resources(self, params=None):
        """GET /v1/resources - Gets a list of resources with filters."""
        return self._get("v1/resources", params)

    def get_resource_by_id(self, resource_id):
        """GET /v1/resources/{id} - Gets a resource by its ID."""
        return self._get(f"v1/resources/{resource_id}")

    # ── ACL Endpoints ───────────────────────────────────────────

    def get_acds(self, resource_id):
        """GET /v1/acl/acds/{id} - Gets the ACD's of a resource."""
        return self._get(f"v1/acl/acds/{resource_id}")

    # ── DataFile Endpoints ──────────────────────────────────────

    def import_las_file(self, file_data):
        """POST /v1/datafile/las/import - Import a LAS file."""
        url = f"{self.base_url}/v1/datafile/las/import"
        try:
            resp = self.session.post(url, files=file_data, timeout=60)
            resp.raise_for_status()
            return resp.json(), None
        except requests.exceptions.HTTPError:
            return None, f"HTTP {resp.status_code}: {resp.text[:300]}"
        except Exception as e:
            return None, str(e)

    # ── Helper Methods ──────────────────────────────────────────

    def fetch_data_as_df(self, endpoint, params=None):
        """Fetch data from endpoint and return as DataFrame."""
        data, error = self._get(endpoint, params)
        if error:
            return None, error
        return self._to_dataframe(data)

    @staticmethod
    def _to_dataframe(data):
        """Convert API response to DataFrame."""
        if isinstance(data, list):
            return pd.DataFrame(data), None
        elif isinstance(data, dict):
            # Handle paged results (common PetroVault pattern)
            for key in ["data", "results", "items", "records", "value", "rows", "resources"]:
                if key in data and isinstance(data[key], list):
                    return pd.DataFrame(data[key]), None
            # Handle DataFrame format from channel data
            if "columns" in data and "rows" in data:
                columns = data["columns"]
                rows = data["rows"]
                if isinstance(columns, list) and isinstance(rows, list):
                    return pd.DataFrame(rows, columns=columns), None
            return pd.DataFrame([data]), None
        return None, "Unexpected response format"

    def wells_as_df(self, page=None, page_size=None):
        """Get wells as DataFrame."""
        data, err = self.get_wells(page, page_size)
        if err:
            return None, err
        return self._to_dataframe(data)

    def wellbores_as_df(self, well=None, page=None, page_size=None):
        """Get wellbores as DataFrame."""
        data, err = self.get_wellbores(well, page, page_size)
        if err:
            return None, err
        return self._to_dataframe(data)

    def logs_as_df(self, well=None, wellbore=None, page=None, page_size=None):
        """Get logs as DataFrame."""
        data, err = self.get_logs(well, wellbore, page=page, page_size=page_size)
        if err:
            return None, err
        return self._to_dataframe(data)

    def channel_data_as_df(self, log_id, start=None, end=None, channels=None, max_rows=None, mode="range"):
        """Get channel data as DataFrame (range or latest)."""
        if mode == "latest":
            data, err = self.get_channel_data_latest(log_id, channels, max_rows)
        else:
            data, err = self.get_channel_data_range(log_id, start, end, channels, max_rows)
        if err:
            return None, err
        return self._to_dataframe(data)

    def channel_report_as_df(self, log_id, start=None, end=None, channels=None, max_rows=None, mode="range"):
        """Get channel report data as DataFrame."""
        if mode == "latest":
            data, err = self.get_channel_report_latest(log_id, channels, max_rows)
        else:
            data, err = self.get_channel_report_range(log_id, start, end, channels, max_rows)
        if err:
            return None, err
        return self._to_dataframe(data)


def create_client(config_row):
    """Create a PetroVaultClient from a database config row."""
    return PetroVaultClient(
        base_url=config_row["base_url"],
        api_key=config_row.get("api_key", ""),
        auth_token=config_row.get("auth_token", ""),
        auth_type=config_row.get("auth_type", "bearer"),
    )
