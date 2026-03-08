import requests
import pandas as pd
from datetime import datetime


class PetroVaultClient:
    """Client for connecting to PetroVault Public API.

    All parameter names and endpoint paths match the official OpenAPI spec at:
    https://pv1.petrolink.net/petrovault/publicapi/swagger/v1/swagger.json
    """

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
    # Paging uses: limit (int, max 1000), cursor (string), fetch (string)

    def get_wells(self, limit=None, cursor=None, fetch=None):
        """GET /v1/wellmodel/wells - Gets all wells as a paged list."""
        params = {}
        if limit is not None:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor
        if fetch:
            params["fetch"] = fetch
        return self._get("v1/wellmodel/wells", params or None)

    def get_wellbores(self, well=None, limit=None, cursor=None, fetch=None):
        """GET /v1/wellmodel/wellbores or /v1/wellmodel/wellbores/{well}"""
        params = {}
        if limit is not None:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor
        if fetch:
            params["fetch"] = fetch
        if well:
            return self._get(f"v1/wellmodel/wellbores/{well}", params or None)
        return self._get("v1/wellmodel/wellbores", params or None)

    def get_logs(self, well=None, wellbore=None, log=None, limit=None, cursor=None, fetch=None):
        """GET /v1/wellmodel/logs with optional well/wellbore/log path params."""
        params = {}
        if limit is not None:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor
        if fetch:
            params["fetch"] = fetch
        if well and wellbore and log:
            return self._get(f"v1/wellmodel/logs/{well}/{wellbore}/{log}", params or None)
        elif well and wellbore:
            return self._get(f"v1/wellmodel/logs/{well}/{wellbore}", params or None)
        elif well:
            return self._get(f"v1/wellmodel/logs/{well}", params or None)
        return self._get("v1/wellmodel/logs", params or None)

    # ── Channel Data Endpoints ──────────────────────────────────
    # /v1/channels/data/latest  — params: target (required), limit, fields
    # /v1/channels/data/range   — params: target (required), limit, cursor, fields, start, end
    # /v1/channels/data POST    — params: well, wellbore, log; body: DataFrame

    def get_channel_data_latest(self, target, limit=None, fields=None):
        """GET /v1/channels/data/latest - Gets latest channel data from a log.

        Args:
            target: Required. URI for a log object.
            limit: Max number of latest values from each channel (0-100000).
            fields: Comma-separated list of mnemonics. Empty = all fields.
        """
        params = {"target": target}
        if limit is not None:
            params["limit"] = limit
        if fields:
            params["fields"] = fields
        return self._get("v1/channels/data/latest", params)

    def get_channel_data_range(self, target, start=None, end=None, limit=None, cursor=None, fields=None):
        """GET /v1/channels/data/range - Gets a range of channel data.

        Args:
            target: Required. URI for a log, trajectory, or mud log resource.
            start: Optional start depth or time index.
            end: Optional end depth or time index.
            limit: Number of DataFrame rows per response (0-100000).
            cursor: Cursor from previous page to get next page.
            fields: Comma-separated list of fields/mnemonics.
        """
        params = {"target": target}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if limit is not None:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor
        if fields:
            params["fields"] = fields
        return self._get("v1/channels/data/range", params)

    def post_channel_data(self, well=None, wellbore=None, log=None, json_data=None):
        """POST /v1/channels/data - Updates data for a log object.

        Args:
            well: The log's well UID.
            wellbore: The log's wellbore UID.
            log: The log's UID.
            json_data: DataFrame body with columnNames and data.
        """
        params = {}
        if well:
            params["well"] = well
        if wellbore:
            params["wellbore"] = wellbore
        if log:
            params["log"] = log
        url = f"{self.base_url}/v1/channels/data"
        try:
            resp = self.session.post(url, params=params, json=json_data, timeout=30)
            resp.raise_for_status()
            return resp.json() if resp.content else {"status": "success"}, None
        except requests.exceptions.HTTPError:
            return None, f"HTTP {resp.status_code}: {resp.text[:300]}"
        except Exception as e:
            return None, str(e)

    # ── Channel Report Endpoints ────────────────────────────────
    # /v1/channels/report/range  — params: channels (required), aliases, metadata, start, end, limit, cursorId
    # /v1/channels/report/latest — params: channels (required), aliases, metadata, count

    def get_channel_report_range(self, channels, aliases=None, metadata=None,
                                  start=None, end=None, limit=None, cursor_id=None):
        """GET /v1/channels/report/range - Gets range data in report format.

        Args:
            channels: Required. Comma-separated list of WITSML 1.4 log/channel URIs.
            aliases: Comma-separated list of aliases (use "-" for no alias).
            metadata: Set to "true" to include metadata per row.
            start: Optional start time or depth index.
            end: Optional end time or depth index.
            limit: Max results per page (0-100000).
            cursor_id: Cursor from previous result page.
        """
        params = {"channels": channels}
        if aliases:
            params["aliases"] = aliases
        if metadata:
            params["metadata"] = metadata
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if limit is not None:
            params["limit"] = limit
        if cursor_id:
            params["cursorId"] = cursor_id
        return self._get("v1/channels/report/range", params)

    def get_channel_report_latest(self, channels, aliases=None, metadata=None, count=None):
        """GET /v1/channels/report/latest - Gets latest data in report format.

        Args:
            channels: Required. Comma-separated list of WITSML 1.4 log/channel URIs.
            aliases: Comma-separated list of aliases (use "-" for no alias).
            metadata: Set to "true" to include metadata per row.
            count: How many latest data points per channel (0-100000).
        """
        params = {"channels": channels}
        if aliases:
            params["aliases"] = aliases
        if metadata:
            params["metadata"] = metadata
        if count is not None:
            params["count"] = count
        return self._get("v1/channels/report/latest", params)

    # ── Resource Endpoints ──────────────────────────────────────
    # /v1/resources — params: uri, parentUri, parentId, fetch, type, cursor, depth, limit

    def get_resources(self, uri=None, parent_uri=None, parent_id=None,
                      resource_type=None, fetch=None, cursor=None, depth=None, limit=None):
        """GET /v1/resources - Gets a list of resources with filters.

        Note: Only one of uri, parent_uri, or parent_id may be specified.
        """
        params = {}
        if uri:
            params["uri"] = uri
        if parent_uri:
            params["parentUri"] = parent_uri
        if parent_id:
            params["parentId"] = parent_id
        if resource_type:
            params["type"] = resource_type
        if fetch:
            params["fetch"] = fetch
        if cursor:
            params["cursor"] = cursor
        if depth is not None:
            params["depth"] = depth
        if limit is not None:
            params["limit"] = limit
        return self._get("v1/resources", params or None)

    def get_resource_by_id(self, resource_id, fetch=None):
        """GET /v1/resources/{id} - Gets a resource by its ID."""
        params = {}
        if fetch:
            params["fetch"] = fetch
        return self._get(f"v1/resources/{resource_id}", params or None)

    # ── ACL Endpoints ───────────────────────────────────────────

    def get_acds(self, resource_id):
        """GET /v1/acl/acds/{id} - Gets the ACD's of a resource."""
        return self._get(f"v1/acl/acds/{resource_id}")

    def update_acds(self, resource_id, acds):
        """POST /v1/acl/acds/{id} - Creates, edits, or deletes ACD's."""
        return self._post(f"v1/acl/acds/{resource_id}", acds)

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

    @staticmethod
    def _to_dataframe(data):
        """Convert API response to DataFrame.

        Handles:
        - Direct list of objects
        - Paged results with 'items' array (ResourcePagedResultDto, PagedChannelDataReportRowDto)
        - DataFrame format with 'columnNames' and 'data' arrays
        - PagedDataFrameDto with 'items' containing DataFrame objects
        """
        if data is None:
            return None, "No data"

        if isinstance(data, list):
            if not data:
                return pd.DataFrame(), None
            # List of ChannelDataReportRow or similar
            return pd.DataFrame(data), None

        if isinstance(data, dict):
            # Handle DataFrame format: { columnNames: [...], data: [[...], ...] }
            if "columnNames" in data and "data" in data:
                columns = data["columnNames"]
                rows = data["data"]
                if isinstance(columns, list) and isinstance(rows, list):
                    return pd.DataFrame(rows, columns=columns), None

            # Handle paged results with 'items'
            if "items" in data and isinstance(data["items"], list):
                items = data["items"]
                if not items:
                    return pd.DataFrame(), None
                # Check if items are DataFrame objects (PagedDataFrameDto)
                if isinstance(items[0], dict) and "columnNames" in items[0] and "data" in items[0]:
                    frames = []
                    for item in items:
                        cols = item.get("columnNames", [])
                        rows = item.get("data", [])
                        if cols and rows:
                            frames.append(pd.DataFrame(rows, columns=cols))
                    if frames:
                        return pd.concat(frames, ignore_index=True), None
                    return pd.DataFrame(), None
                # Items are regular objects (ResourceDto, etc.)
                return pd.DataFrame(items), None

            # Handle other common list keys
            for key in ["data", "results", "records", "value", "rows", "resources"]:
                if key in data and isinstance(data[key], list):
                    return pd.DataFrame(data[key]), None

            # Single object
            return pd.DataFrame([data]), None

        return None, "Unexpected response format"

    @staticmethod
    def _extract_paging(data):
        """Extract paging info from a paged response."""
        if isinstance(data, dict):
            return {
                "pageNumber": data.get("pageNumber"),
                "hasMore": data.get("hasMore", False),
                "cursor": data.get("cursor"),
            }
        return {"pageNumber": None, "hasMore": False, "cursor": None}

    @staticmethod
    def _flatten_resource_items(data):
        """Flatten ResourceDto items for display as a table.

        Extracts metadata fields and model fields into flat columns.
        """
        if not isinstance(data, dict) or "items" not in data:
            return data
        items = data.get("items", [])
        if not items:
            return data
        flat = []
        for item in items:
            row = {}
            # Extract metadata
            meta = item.get("metadata") or {}
            for k, v in meta.items():
                row[k] = v
            # Extract model type-specific fields
            model = item.get("model") or {}
            model_type = model.get("modelType", "none")
            row["modelType"] = model_type
            if model_type != "none" and model_type in model:
                model_data = model[model_type] or {}
                for k, v in model_data.items():
                    if not isinstance(v, (dict, list)):
                        row[f"model.{k}"] = v
            flat.append(row)
        return flat

    def channel_data_as_df(self, target, start=None, end=None, fields=None,
                           limit=None, mode="range"):
        """Get channel data as DataFrame (range or latest)."""
        if mode == "latest":
            data, err = self.get_channel_data_latest(target, limit=limit, fields=fields)
        else:
            data, err = self.get_channel_data_range(
                target, start=start, end=end, limit=limit, fields=fields
            )
        if err:
            return None, err
        # For paged results, extract items
        paging = self._extract_paging(data)
        df, df_err = self._to_dataframe(data)
        return df, df_err

    def channel_report_as_df(self, channels, aliases=None, metadata=None,
                              start=None, end=None, limit=None, count=None, mode="range"):
        """Get channel report data as DataFrame."""
        if mode == "latest":
            data, err = self.get_channel_report_latest(
                channels, aliases=aliases, metadata=metadata, count=count
            )
        else:
            data, err = self.get_channel_report_range(
                channels, aliases=aliases, metadata=metadata,
                start=start, end=end, limit=limit
            )
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
