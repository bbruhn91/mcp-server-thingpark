# Supported Sensors

Sensor helper modules provide high-level MCP tools for configuring specific LoRaWAN sensors via downlink commands, so you don't need to know the raw hex payload format.

The generic ThingPark tools (`list_devices`, `send_downlink`, etc.) work with **any** LoRaWAN device — sensor helpers are optional convenience wrappers.

## Available Modules

| Module | Sensor | Manufacturer | Tools | Reference |
|---|---|---|---|---|
| `lht65n_vib` | [LHT65N-VIB](https://www.dragino.com/products/temperature-humidity-sensor/item/279-lht65n-vib.html) | Dragino | TDC, vibration mode, sensitivity, alarm | [lht65n_vib.md](lht65n_vib.md) |

## Adding a New Sensor

1. Create `sensors/<sensor_name>.py` with a `register(mcp, send_downlink)` function
2. Create `sensors/<sensor_name>.md` with the downlink command reference
3. Add a row to the table above
4. Submit a PR

See [lht65n_vib.py](lht65n_vib.py) for an example of the module structure.
