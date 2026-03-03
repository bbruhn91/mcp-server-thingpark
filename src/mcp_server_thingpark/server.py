"""
MCP Server for Actility ThingPark

Manage LoRaWAN devices on ThingPark (Community / Enterprise) via the DX Core API.
List devices, send downlink commands, and query downlink queues.

Sensor-specific helper tools are auto-loaded from the sensors/ directory.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

import click
import httpx
from mcp.server.fastmcp import FastMCP

log = logging.getLogger(__name__)

# --- Configuration ---
THINGPARK_URL = os.environ.get("THINGPARK_URL", "").rstrip("/")
THINGPARK_CLIENT_ID = os.environ.get("THINGPARK_CLIENT_ID", "")
THINGPARK_CLIENT_SECRET = os.environ.get("THINGPARK_CLIENT_SECRET", "")

# --- HTTP Client (lazy init) ---
_client: httpx.Client | None = None


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        if not THINGPARK_URL:
            raise ValueError("THINGPARK_URL environment variable is not set")
        _client = httpx.Client(base_url=THINGPARK_URL, timeout=30.0)
    return _client


# --- Token management ---
_token_cache: dict = {}


def _get_bearer_token() -> str:
    """Get a valid bearer token, refreshing if expired."""
    now = time.time()
    if _token_cache.get("access_token") and _token_cache.get("expires_at", 0) > now + 60:
        return _token_cache["access_token"]

    if not THINGPARK_URL or not THINGPARK_CLIENT_ID or not THINGPARK_CLIENT_SECRET:
        raise ValueError(
            "ThingPark credentials not configured. "
            "Set THINGPARK_URL, THINGPARK_CLIENT_ID, and THINGPARK_CLIENT_SECRET."
        )

    token_url = (
        THINGPARK_URL.replace("/thingpark", "")
        + "/users-auth/protocol/openid-connect/token"
    )
    resp = httpx.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": THINGPARK_CLIENT_ID,
            "client_secret": THINGPARK_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()

    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)

    return _token_cache["access_token"]


def _api_request(method: str, path: str, **kwargs) -> httpx.Response:
    """Make an authenticated API request to ThingPark DX Core."""
    token = _get_bearer_token()
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    headers.setdefault("Accept", "application/json")

    client = _get_client()
    resp = client.request(
        method, f"/dx/core/latest/api{path}", headers=headers, **kwargs
    )
    resp.raise_for_status()
    return resp


# --- DevEUI -> ref mapping ---
# The DX Core API uses an internal ref ID (not the DevEUI) in URL paths.
_eui_to_ref: dict[str, str] = {}


def _resolve_dev_eui(dev_eui: str) -> str:
    """Resolve a DevEUI to the ThingPark internal ref ID."""
    eui = dev_eui.upper()
    if eui in _eui_to_ref:
        return _eui_to_ref[eui]

    resp = _api_request("GET", "/devices")
    data = resp.json()
    devices = data if isinstance(data, list) else data.get("briefs", data.get("data", []))

    for d in devices:
        d_eui = d.get("EUI", "").upper()
        d_ref = str(d.get("ref", ""))
        if d_eui and d_ref:
            _eui_to_ref[d_eui] = d_ref

    if eui not in _eui_to_ref:
        raise ValueError(f"Device with EUI {dev_eui} not found in ThingPark")

    return _eui_to_ref[eui]


# =============================================================================
# MCP Server + Core Tools
# =============================================================================

mcp = FastMCP(
    "thingpark",
    instructions=(
        "Manage LoRaWAN devices on Actility ThingPark. "
        "List devices, send downlink commands, and query device information. "
        "Use DevEUI (hex string) to identify devices. "
        "Sensor-specific helper tools may also be available."
    ),
)


@mcp.tool()
def list_devices() -> str:
    """List all LoRaWAN devices registered on the ThingPark account.

    Returns device names, DevEUIs, and status information.
    """
    resp = _api_request("GET", "/devices")
    data = resp.json()

    if isinstance(data, list):
        devices = data
    else:
        devices = data.get("briefs", data.get("data", [data]))

    results = []
    for d in devices:
        results.append({
            "name": d.get("name", "unknown"),
            "DevEUI": d.get("EUI", d.get("DevEUI", d.get("devEUI", "unknown"))),
            "deviceClass": d.get("deviceClass", "unknown"),
            "activationType": d.get("activationType", "unknown"),
            "connectivityPlanId": d.get("connectivityPlanId", ""),
            "deviceProfileId": d.get("deviceProfileId", ""),
        })

    return json.dumps(results, indent=2)


@mcp.tool()
def get_device(dev_eui: str) -> str:
    """Get detailed information about a specific device.

    Args:
        dev_eui: The DevEUI of the device (hex string, e.g. 'A84041F21867E433').
    """
    ref = _resolve_dev_eui(dev_eui)
    resp = _api_request("GET", f"/devices/{ref}")
    return json.dumps(resp.json(), indent=2)


@mcp.tool()
def send_downlink(
    dev_eui: str,
    payload_hex: str,
    fport: int = 2,
    confirmed: bool = False,
    flush_queue: bool = False,
) -> str:
    """Send a raw downlink message to a device.

    Args:
        dev_eui: The DevEUI of the target device (hex string).
        payload_hex: The hex-encoded payload to send (e.g. '0100003C').
        fport: The LoRaWAN FPort (default: 2 for config commands).
        confirmed: Whether to request a confirmed downlink (default: False).
        flush_queue: Whether to flush the existing downlink queue first (default: False).
    """
    ref = _resolve_dev_eui(dev_eui)

    params = {}
    if flush_queue:
        params["flushDownlinkQueue"] = "true"

    body = {
        "payloadHex": payload_hex,
        "targetPorts": str(fport),
        "confirmDownlink": confirmed,
    }

    resp = _api_request(
        "POST",
        f"/devices/{ref}/downlinkMessages",
        json=body,
        params=params,
        headers={"Content-Type": "application/json"},
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return json.dumps({
        "status": "queued",
        "timestamp": timestamp,
        "dev_eui": dev_eui,
        "payload_hex": payload_hex,
        "fport": fport,
        "confirmed": confirmed,
        "response_status": resp.status_code,
    }, indent=2)


@mcp.tool()
def get_downlink_queue(dev_eui: str) -> str:
    """Get pending downlink messages for a device.

    Args:
        dev_eui: The DevEUI of the device (hex string).
    """
    ref = _resolve_dev_eui(dev_eui)
    resp = _api_request("GET", f"/devices/{ref}/downlinkMessages")
    return json.dumps(resp.json(), indent=2)


@mcp.tool()
def invalidate_token() -> str:
    """Clear the cached OAuth token. Use if authentication errors occur."""
    _token_cache.clear()
    return "Token cache cleared. Next API call will request a fresh token."


# =============================================================================
# CLI entry point
# =============================================================================


@click.command()
@click.option("-v", "--verbose", count=True, help="Increase logging verbosity")
def main(verbose: int) -> None:
    """MCP server for Actility ThingPark LoRaWAN device management."""
    # Configure logging: default WARNING, -v INFO, -vv DEBUG
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    logging.basicConfig(level=level, stream=sys.stderr, format="%(levelname)s: %(message)s")

    # Validate configuration early
    missing = []
    if not THINGPARK_URL:
        missing.append("THINGPARK_URL")
    if not THINGPARK_CLIENT_ID:
        missing.append("THINGPARK_CLIENT_ID")
    if not THINGPARK_CLIENT_SECRET:
        missing.append("THINGPARK_CLIENT_SECRET")

    if missing:
        click.echo(
            f"Error: missing environment variables: {', '.join(missing)}\n"
            "See README.md for setup instructions.",
            err=True,
        )
        raise SystemExit(1)

    # Auto-load sensor helpers
    from . import sensors

    loaded = sensors.load_all(mcp, send_downlink)
    if loaded:
        log.info("Sensor modules loaded: %s", ", ".join(loaded))

    mcp.run()
