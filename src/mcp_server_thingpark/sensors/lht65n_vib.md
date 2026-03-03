# Dragino LHT65N-VIB — Downlink Command Reference

Vibration sensor with temperature/humidity. Detects vibration count, runtime, and raw acceleration.

- **Manufacturer**: Dragino
- **Manual**: https://wiki.dragino.com/xwiki/bin/view/Main/User%20Manual%20for%20LoRaWAN%20End%20Nodes/LHT65N-VIB/
- **Device profile**: `DRAG/LHT65A.1.0.3a_ETSI`
- **Config FPort**: 2

## MCP Tools Provided

| Tool | Description |
|---|---|
| `set_transmit_interval` | Set uplink interval in seconds (TDC, command `0x01`) |
| `set_vibration_mode` | Set vibration mode 1-4 (command `0x0A`) |
| `set_vibration_mode5` | Set Mode 5 max acceleration (command `0x0A 05`) |
| `set_vibration_sensitivity` | Set detection threshold/frequency (VIBSET, command `0x09`) |
| `set_alarm_interval` | Set alarm repeat interval (command `0x08`) |

## Downlink Commands

All commands use **FPort 2**.

### TDC — Transmit Interval (0x01)

Format: `01 <seconds_3B>`

| Payload | Interval |
|---|---|
| `01 00003C` | 60 seconds |
| `01 000078` | 120 seconds |
| `01 0004B0` | 1200 seconds (20 min, factory default) |

### VIBMOD — Vibration Mode (0x0A)

**Mode 1** — Vibration count + runtime (uplink FPort 2):
`0A 01 <alarm_time_2B> <stop_duration_2B>` (6 bytes)

**Mode 2** — Count + temp/humidity (uplink FPort 2):
`0A 02 <alarm_time_2B> <stop_duration_2B>` (6 bytes)

**Mode 3** — Runtime + temp/humidity (uplink FPort 2):
`0A 03 <alarm_time_2B> <stop_duration_2B>` (6 bytes)

**Mode 4** — 3-axis acceleration (uplink FPort 7):
`0A 04 <interval_ms_2B> <groups_1B>` **(5 bytes — groups is 1 byte, not 2!)**

| Payload | Description |
|---|---|
| `0A 04 2710 01` | 10s intervals, 1 group |
| `0A 04 7530 01` | 30s intervals, 1 group |

**Mode 5** — Max acceleration (uplink FPort 9, firmware v1.3+):
`0A 05 <odr_1B> <scale_1B> <res_1B> <watermark_1B> <tdc_2B>` (8 bytes)

| Parameter | Values |
|---|---|
| odr | 1-9 (9 = 5376Hz) |
| scale | 0=+/-2g, 1=+/-4g, 2=+/-8g, 3=+/-16g |
| res | 0=12-bit HR, 1=10-bit normal, 2=8-bit LP |
| watermark | fixed 0x14 |
| tdc | 15-3600 seconds |

Example: `0A 05 09 00 00 14 001E` = 5376Hz, +/-2g, 12-bit, 30s

### VIBSET — Sensitivity (0x09)

Format: `09 <accel_2B> <freq_2B> <threshold_2B> <duration_2B>` (9 bytes)

| Parameter | Values |
|---|---|
| accel | 0=+/-2g, 1=+/-4g, 2=+/-8g, 3=+/-16g |
| freq | 0=25Hz, 1=50Hz, 2=100Hz, 3=200Hz, 4=400Hz |
| threshold | units of 16mg (1=16mg, 2=32mg, 6=96mg, 10=160mg) |
| duration | interrupt duration in milliseconds |

Examples:

| Payload | Description |
|---|---|
| `09 0000 0004 000A 000C` | +/-2g, 400Hz, 160mg, 12ms (factory default) |
| `09 0000 0004 0002 0008` | +/-2g, 400Hz, 32mg, 8ms (aggressive) |
| `09 0000 0004 0001 0008` | +/-2g, 400Hz, 16mg, 8ms (most sensitive) |

### Alarm Interval (0x08)

Format: `08 <minutes_1B>`

| Payload | Description |
|---|---|
| `08 00` | Alarm once only |
| `08 01` | Alarm every 1 minute |

## Gotchas

- **Mode 4 groups field** is 1 byte, not 2. Sending 2 bytes causes the sensor to reject the command silently.
- **Mode 5** uplinks on FPort 9 — make sure your decoder/codec supports it.
- **Default sensitivity** (160mg threshold) is too high for low-vibration sources like small HVAC circulators with zip-tie mounting. Try 16-32mg for weak vibration sources.
- Sensors are LoRaWAN **Class A** — downlinks are only received after an uplink. With a 1200s default TDC, it can take up to 20 minutes for a downlink to be applied.
