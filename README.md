# MCP Server for Actility ThingPark

A Model Context Protocol (MCP) server that connects AI assistants to the **Actility ThingPark** LoRaWAN network server. Manage devices and send downlink commands through natural language.

Works with ThingPark Community, ThingPark Enterprise, and other deployments that expose the DX Core API.

## Tools

| Tool | Description |
|---|---|
| `list_devices` | List all registered LoRaWAN devices with DevEUI, class, and profile |
| `get_device` | Get detailed device information by DevEUI |
| `send_downlink` | Send a raw hex downlink payload to any device |
| `get_downlink_queue` | View pending downlink messages for a device |
| `invalidate_token` | Clear cached OAuth token (troubleshooting) |

These tools work with **any** LoRaWAN device on your ThingPark account.

## Sensor Helpers

The server auto-loads sensor-specific helper modules from `sensors/`. These provide high-level tools for configuring specific sensors without needing to know the raw hex payload format.

See [sensors/SUPPORTED.md](src/mcp_server_thingpark/sensors/SUPPORTED.md) for the list of supported sensors and how to add your own.

| Sensor | Manufacturer | Tools |
|---|---|---|
| [LHT65N-VIB](src/mcp_server_thingpark/sensors/lht65n_vib.md) | Dragino | Transmit interval, vibration mode, sensitivity, alarm |

## Installation

### Using uv (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. Use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run the server:

```bash
uvx mcp-server-thingpark
```

### Using pip

```bash
pip install mcp-server-thingpark
```

After installation, run it as:

```bash
mcp-server-thingpark
```

### From source

```bash
git clone https://github.com/bbruhn91/mcp-server-thingpark.git
cd mcp-server-thingpark

python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

The server requires three environment variables for ThingPark API authentication:

| Variable | Description | Example |
|---|---|---|
| `THINGPARK_URL` | ThingPark platform base URL | `https://community.thingpark.io/thingpark` |
| `THINGPARK_CLIENT_ID` | API client ID | `sub-XXXXXXXXX/your-username` |
| `THINGPARK_CLIENT_SECRET` | API client secret | `your-client-secret` |

### Getting API Credentials

1. Log in to your ThingPark platform (e.g. [community.thingpark.io](https://community.thingpark.io))
2. Go to your account settings
3. Create an API client with `client_credentials` grant type
4. Note the **client ID** (`sub-XXXXXXXXX/username`) and **client secret**

### Usage with Claude Desktop

Add to your Claude Desktop configuration file:

<details>
<summary>macOS: ~/Library/Application Support/Claude/claude_desktop_config.json</summary>

```json
{
  "mcpServers": {
    "thingpark": {
      "command": "uvx",
      "args": ["mcp-server-thingpark"],
      "env": {
        "THINGPARK_URL": "https://community.thingpark.io/thingpark",
        "THINGPARK_CLIENT_ID": "sub-XXXXXXXXX/your-username",
        "THINGPARK_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

</details>

<details>
<summary>Windows: %APPDATA%\Claude\claude_desktop_config.json</summary>

```json
{
  "mcpServers": {
    "thingpark": {
      "command": "uvx",
      "args": ["mcp-server-thingpark"],
      "env": {
        "THINGPARK_URL": "https://community.thingpark.io/thingpark",
        "THINGPARK_CLIENT_ID": "sub-XXXXXXXXX/your-username",
        "THINGPARK_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

</details>

### Usage with Claude Code

Add to `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "thingpark": {
      "command": "uvx",
      "args": ["mcp-server-thingpark"],
      "env": {
        "THINGPARK_URL": "https://community.thingpark.io/thingpark",
        "THINGPARK_CLIENT_ID": "sub-XXXXXXXXX/your-username",
        "THINGPARK_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

### Usage with VS Code

Install the [MCP extension](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-mcp) and add to your VS Code settings or `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "thingpark": {
        "command": "uvx",
        "args": ["mcp-server-thingpark"],
        "env": {
          "THINGPARK_URL": "https://community.thingpark.io/thingpark",
          "THINGPARK_CLIENT_ID": "sub-XXXXXXXXX/your-username",
          "THINGPARK_CLIENT_SECRET": "your-client-secret"
        }
      }
    }
  }
}
```

## Examples

```
> List all my LoRaWAN devices

> Show me details for device A84041F21867E433

> Send downlink 0100003C to device A84041F21867E433 on FPort 2

> Set the transmit interval to 60 seconds on my vibration sensor
```

## Adding Support for a New Sensor

1. Create `src/mcp_server_thingpark/sensors/<sensor_name>.py` with a `register(mcp, send_downlink)` function:

```python
def register(mcp, send_downlink):
    @mcp.tool()
    def my_sensor_set_interval(dev_eui: str, seconds: int) -> str:
        """Set transmit interval for MySensor."""
        payload = f"01{seconds:06X}"
        return send_downlink(dev_eui, payload, fport=2)
```

2. Create `src/mcp_server_thingpark/sensors/<sensor_name>.md` with the downlink command reference
3. Add a row to `src/mcp_server_thingpark/sensors/SUPPORTED.md`
4. Submit a PR

The module is auto-discovered on startup — no need to edit `server.py`.

## Debugging

You can use the [MCP inspector](https://modelcontextprotocol.io/docs/tools/inspector) to debug the server:

```bash
npx @modelcontextprotocol/inspector uvx mcp-server-thingpark
```

Increase logging verbosity with the `-v` flag:

```bash
mcp-server-thingpark -v     # INFO level
mcp-server-thingpark -vv    # DEBUG level
```

## Technical Notes

### DevEUI vs ref

The ThingPark DX Core API uses an internal `ref` identifier in URL paths, not the DevEUI. This server maps DevEUI to ref automatically — you always use DevEUIs.

### Authentication

OAuth2 client credentials flow against the ThingPark Keycloak OIDC endpoint. Tokens are cached and refreshed automatically.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
