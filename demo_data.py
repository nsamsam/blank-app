"""Demo/sample data for testing the UI without a live PetroVault API connection."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def _random_uid():
    """Generate a random UID-like string."""
    import hashlib, random
    return hashlib.md5(str(random.random()).encode()).hexdigest()[:12]


# ── Well Model Data ─────────────────────────────────────────

DEMO_WELLS = {
    "pageNumber": 1,
    "hasMore": False,
    "cursor": None,
    "items": [
        {
            "metadata": {
                "id": "a1b2c3d4-0001-4000-8000-000000000001",
                "uri": "//W001",
                "name": "Eagle Ford #1",
                "type": "well",
                "createdTime": "2024-03-15T08:00:00Z",
                "modifiedTime": "2025-01-10T14:30:00Z",
            },
            "model": {
                "modelType": "well",
                "well": {
                    "uid": "W001",
                    "name": "Eagle Ford #1",
                    "wellStatus": "active",
                    "apiNumber": "42-301-12345",
                    "geographicContext": {"field": "Eagle Ford", "country": "US", "state": "Texas", "county": "Webb"},
                },
            },
        },
        {
            "metadata": {
                "id": "a1b2c3d4-0002-4000-8000-000000000002",
                "uri": "//W002",
                "name": "Permian Basin A-7",
                "type": "well",
                "createdTime": "2024-06-20T10:00:00Z",
                "modifiedTime": "2025-02-05T09:15:00Z",
            },
            "model": {
                "modelType": "well",
                "well": {
                    "uid": "W002",
                    "name": "Permian Basin A-7",
                    "wellStatus": "active",
                    "apiNumber": "42-103-67890",
                    "geographicContext": {"field": "Midland Basin", "country": "US", "state": "Texas", "county": "Midland"},
                },
            },
        },
        {
            "metadata": {
                "id": "a1b2c3d4-0003-4000-8000-000000000003",
                "uri": "//W003",
                "name": "Bakken H-12",
                "type": "well",
                "createdTime": "2023-11-01T12:00:00Z",
                "modifiedTime": "2024-12-20T16:45:00Z",
            },
            "model": {
                "modelType": "well",
                "well": {
                    "uid": "W003",
                    "name": "Bakken H-12",
                    "wellStatus": "drilling",
                    "apiNumber": "33-053-54321",
                    "geographicContext": {"field": "Bakken", "country": "US", "state": "North Dakota", "county": "McKenzie"},
                },
            },
        },
        {
            "metadata": {
                "id": "a1b2c3d4-0004-4000-8000-000000000004",
                "uri": "//W004",
                "name": "Marcellus V-3",
                "type": "well",
                "createdTime": "2024-01-10T09:00:00Z",
                "modifiedTime": "2025-01-28T11:00:00Z",
            },
            "model": {
                "modelType": "well",
                "well": {
                    "uid": "W004",
                    "name": "Marcellus V-3",
                    "wellStatus": "completed",
                    "apiNumber": "37-081-11111",
                    "geographicContext": {"field": "Marcellus", "country": "US", "state": "West Virginia", "county": "Harrison"},
                },
            },
        },
        {
            "metadata": {
                "id": "a1b2c3d4-0005-4000-8000-000000000005",
                "uri": "//W005",
                "name": "GOM Deepwater SS-1",
                "type": "well",
                "createdTime": "2024-08-05T07:00:00Z",
                "modifiedTime": "2025-03-01T13:20:00Z",
            },
            "model": {
                "modelType": "well",
                "well": {
                    "uid": "W005",
                    "name": "GOM Deepwater SS-1",
                    "wellStatus": "drilling",
                    "apiNumber": "17-700-99999",
                    "geographicContext": {"field": "Gulf of Mexico", "country": "US", "state": "Federal Waters"},
                },
            },
        },
    ],
}


DEMO_WELLBORES = {
    "pageNumber": 1,
    "hasMore": False,
    "cursor": None,
    "items": [
        {
            "metadata": {
                "id": "b1b2c3d4-0001-4000-8000-000000000001",
                "uri": "//W001/WB001",
                "name": "Eagle Ford #1 - Main Bore",
                "type": "wellbore",
            },
            "model": {
                "modelType": "wellbore",
                "wellbore": {
                    "uid": "WB001", "name": "Main Bore", "wellUid": "W001",
                    "wellName": "Eagle Ford #1", "status": "active", "isActive": True,
                    "purpose": "production", "type": "horizontal", "shape": "deviated",
                },
            },
        },
        {
            "metadata": {
                "id": "b1b2c3d4-0002-4000-8000-000000000002",
                "uri": "//W001/WB002",
                "name": "Eagle Ford #1 - Lateral A",
                "type": "wellbore",
            },
            "model": {
                "modelType": "wellbore",
                "wellbore": {
                    "uid": "WB002", "name": "Lateral A", "wellUid": "W001",
                    "wellName": "Eagle Ford #1", "status": "active", "isActive": True,
                    "purpose": "production", "type": "horizontal",
                },
            },
        },
        {
            "metadata": {
                "id": "b1b2c3d4-0003-4000-8000-000000000003",
                "uri": "//W002/WB001",
                "name": "Permian Basin A-7 - Vertical",
                "type": "wellbore",
            },
            "model": {
                "modelType": "wellbore",
                "wellbore": {
                    "uid": "WB001", "name": "Vertical Section", "wellUid": "W002",
                    "wellName": "Permian Basin A-7", "status": "drilling", "isActive": True,
                    "purpose": "exploration", "type": "vertical", "shape": "vertical",
                },
            },
        },
        {
            "metadata": {
                "id": "b1b2c3d4-0004-4000-8000-000000000004",
                "uri": "//W003/WB001",
                "name": "Bakken H-12 - Horizontal",
                "type": "wellbore",
            },
            "model": {
                "modelType": "wellbore",
                "wellbore": {
                    "uid": "WB001", "name": "Horizontal Leg", "wellUid": "W003",
                    "wellName": "Bakken H-12", "status": "drilling", "isActive": True,
                    "purpose": "development", "type": "horizontal",
                },
            },
        },
    ],
}


DEMO_LOGS = {
    "pageNumber": 1,
    "hasMore": False,
    "cursor": None,
    "items": [
        {
            "metadata": {
                "id": "c1b2c3d4-0001-4000-8000-000000000001",
                "uri": "//W001/WB001/LOG001",
                "name": "Drilling Parameters Log",
                "type": "log",
            },
            "model": {
                "modelType": "log",
                "log": {
                    "uid": "LOG001", "name": "Drilling Parameters Log",
                    "wellUid": "W001", "wellName": "Eagle Ford #1",
                    "wellboreUid": "WB001", "wellboreName": "Main Bore",
                    "indexType": "double", "indexDirection": "increasing",
                    "indexName": "DEPTH", "indexUom": "ft",
                    "startDepth": 0.0, "endDepth": 15200.0,
                },
            },
        },
        {
            "metadata": {
                "id": "c1b2c3d4-0002-4000-8000-000000000002",
                "uri": "//W001/WB001/LOG002",
                "name": "Time-Based Log",
                "type": "log",
            },
            "model": {
                "modelType": "log",
                "log": {
                    "uid": "LOG002", "name": "Time-Based Log",
                    "wellUid": "W001", "wellName": "Eagle Ford #1",
                    "wellboreUid": "WB001", "wellboreName": "Main Bore",
                    "indexType": "time", "indexDirection": "increasing",
                    "indexName": "TIME",
                    "startTime": "2025-01-01T00:00:00Z", "endTime": "2025-03-10T23:59:59Z",
                },
            },
        },
        {
            "metadata": {
                "id": "c1b2c3d4-0003-4000-8000-000000000003",
                "uri": "//W002/WB001/LOG001",
                "name": "MWD Log",
                "type": "log",
            },
            "model": {
                "modelType": "log",
                "log": {
                    "uid": "LOG001", "name": "MWD Log",
                    "wellUid": "W002", "wellName": "Permian Basin A-7",
                    "wellboreUid": "WB001", "wellboreName": "Vertical Section",
                    "indexType": "double", "indexDirection": "increasing",
                    "indexName": "DEPTH", "indexUom": "ft",
                    "startDepth": 500.0, "endDepth": 9800.0,
                },
            },
        },
    ],
}


# ── Channel Data ────────────────────────────────────────────

def generate_demo_channel_data(num_rows=500, mode="range"):
    """Generate realistic drilling channel data as a DataFrame dict."""
    np.random.seed(42)
    depths = np.linspace(5000, 15000, num_rows)

    # Realistic drilling parameters
    rop = 30 + 20 * np.sin(depths / 1000) + np.random.normal(0, 3, num_rows)  # ft/hr
    rop = np.clip(rop, 5, 80)

    wob = 15 + 10 * np.sin(depths / 800) + np.random.normal(0, 2, num_rows)  # klbs
    wob = np.clip(wob, 5, 40)

    rpm = 120 + 30 * np.sin(depths / 1200) + np.random.normal(0, 5, num_rows)
    rpm = np.clip(rpm, 60, 200)

    torque = 5 + 3 * np.sin(depths / 600) + np.random.normal(0, 0.5, num_rows)  # kft-lbs
    torque = np.clip(torque, 1, 15)

    spp = 2500 + 500 * np.sin(depths / 1500) + np.random.normal(0, 50, num_rows)  # psi
    spp = np.clip(spp, 1500, 4000)

    flow_rate = 650 + 100 * np.sin(depths / 2000) + np.random.normal(0, 15, num_rows)  # gpm
    flow_rate = np.clip(flow_rate, 400, 900)

    hookload = 200 + 50 * (depths / 15000) + np.random.normal(0, 5, num_rows)  # klbs
    hookload = np.clip(hookload, 150, 350)

    mud_weight = 10.5 + 2.0 * (depths / 15000) + np.random.normal(0, 0.1, num_rows)  # ppg
    mud_weight = np.clip(mud_weight, 9.0, 14.0)

    data = {
        "columnNames": ["DEPTH", "ROP", "WOB", "RPM", "TORQUE", "SPP", "FLOW_RATE", "HOOKLOAD", "MUD_WEIGHT"],
        "data": [],
    }
    for i in range(num_rows):
        data["data"].append([
            round(depths[i], 2),
            round(rop[i], 2),
            round(wob[i], 2),
            round(rpm[i], 1),
            round(torque[i], 2),
            round(spp[i], 1),
            round(flow_rate[i], 1),
            round(hookload[i], 1),
            round(mud_weight[i], 2),
        ])

    if mode == "latest":
        data["data"] = data["data"][-10:]

    return data


def generate_demo_channel_report(num_rows=100, mode="latest"):
    """Generate demo channel report rows."""
    np.random.seed(42)
    base_time = datetime(2025, 3, 10, 0, 0, 0)

    rows = []
    channels = ["DEPTH", "ROP", "WOB", "RPM", "SPP"]
    for i in range(num_rows):
        for ch in channels:
            t = base_time - timedelta(minutes=(num_rows - i) * 5)
            val = {
                "DEPTH": round(5000 + i * 10 + np.random.normal(0, 0.5), 2),
                "ROP": round(30 + np.random.normal(0, 5), 2),
                "WOB": round(20 + np.random.normal(0, 3), 2),
                "RPM": round(120 + np.random.normal(0, 10), 1),
                "SPP": round(2800 + np.random.normal(0, 100), 1),
            }[ch]
            rows.append({
                "channel": ch,
                "index": t.isoformat() + "Z",
                "value": val,
                "well": "Eagle Ford #1",
                "wellbore": "Main Bore",
                "country": "US",
                "field": "Eagle Ford",
                "rig": "Rig 7",
                "run": "Run 3",
                "holeSection": "8.5 in",
            })
    return rows


# ── Resources ───────────────────────────────────────────────

DEMO_RESOURCES = {
    "pageNumber": 1,
    "hasMore": False,
    "cursor": None,
    "items": [
        {
            "metadata": {
                "id": "a1b2c3d4-0001-4000-8000-000000000001",
                "uri": "//W001",
                "name": "Eagle Ford #1",
                "type": "well",
                "createdTime": "2024-03-15T08:00:00Z",
            },
        },
        {
            "metadata": {
                "id": "b1b2c3d4-0001-4000-8000-000000000001",
                "uri": "//W001/WB001",
                "name": "Eagle Ford #1 - Main Bore",
                "type": "wellbore",
                "createdTime": "2024-03-15T08:30:00Z",
            },
        },
        {
            "metadata": {
                "id": "c1b2c3d4-0001-4000-8000-000000000001",
                "uri": "//W001/WB001/LOG001",
                "name": "Drilling Parameters Log",
                "type": "log",
                "createdTime": "2024-03-15T09:00:00Z",
            },
        },
    ],
}

DEMO_RESOURCE_DETAIL = {
    "metadata": {
        "id": "a1b2c3d4-0001-4000-8000-000000000001",
        "uri": "//W001",
        "name": "Eagle Ford #1",
        "type": "well",
        "createdTime": "2024-03-15T08:00:00Z",
        "modifiedTime": "2025-01-10T14:30:00Z",
        "contentType": "application/xml",
        "witsmlVersion": "1.4.1.1",
    },
    "properties": {
        "wellStatus": [{"key": "wellStatus", "type": "string", "value": "active"}],
        "apiNumber": [{"key": "apiNumber", "type": "string", "value": "42-301-12345"}],
    },
    "parents": [],
    "model": {
        "modelType": "well",
        "well": {
            "uid": "W001",
            "name": "Eagle Ford #1",
            "wellStatus": "active",
            "apiNumber": "42-301-12345",
        },
    },
}


# ── Health / Version ────────────────────────────────────────

DEMO_HEALTH = {"status": "healthy", "totalDuration": "00:00:00.0312"}
DEMO_VERSION = {"version": "1.0.0-demo"}
