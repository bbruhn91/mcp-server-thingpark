"""
Dragino LHT65N-VIB — Vibration sensor helpers.

Provides MCP tools to configure vibration modes, sensitivity thresholds,
transmit intervals, and alarm settings via LoRaWAN downlink commands.

Reference: https://wiki.dragino.com/xwiki/bin/view/Main/User%20Manual%20for%20LoRaWAN%20End%20Nodes/LHT65N-VIB/
"""


def register(mcp, send_downlink):
    """Register LHT65N-VIB tools on the MCP server."""

    @mcp.tool()
    def set_transmit_interval(
        dev_eui: str,
        seconds: int,
        confirmed: bool = False,
    ) -> str:
        """Set the uplink transmit interval (TDC) for a Dragino LHT65N sensor.

        Args:
            dev_eui: The DevEUI of the target device.
            seconds: Transmit interval in seconds (1 to 16777215).
            confirmed: Whether to request confirmed downlink.
        """
        if seconds < 1 or seconds > 16777215:
            return "Error: seconds must be between 1 and 16777215"

        payload = f"01{seconds:06X}"
        return send_downlink(dev_eui, payload, fport=2, confirmed=confirmed)

    @mcp.tool()
    def set_vibration_mode(
        dev_eui: str,
        mode: int,
        param1: int = 0,
        param2: int = 0,
        confirmed: bool = False,
    ) -> str:
        """Set the vibration operating mode for an LHT65N-VIB sensor.

        Args:
            dev_eui: The DevEUI of the target device.
            mode: Vibration mode (1-4).
                1 = Vibration count + runtime (param1=alarm_time_s, param2=stop_duration_s)
                2 = Count + temp/humidity (param1=alarm_time_s, param2=stop_duration_s)
                3 = Runtime + temp/humidity (param1=alarm_time_s, param2=stop_duration_s)
                4 = 3-axis acceleration data (param1=interval_ms, param2=groups)
            param1: First parameter (meaning depends on mode).
            param2: Second parameter (meaning depends on mode).
            confirmed: Whether to request confirmed downlink.
        """
        if mode < 1 or mode > 5:
            return "Error: mode must be 1-5"

        if mode == 5:
            return "Error: use set_vibration_mode5() for Mode 5 (requires additional params)"

        if mode == 4:
            # Mode 4: 0A 04 <interval_ms_2B> <groups_1B>  (5 bytes total)
            payload = f"0A{mode:02X}{param1:04X}{param2:02X}"
        else:
            # Modes 1-3: 0A <mode_1B> <alarm_time_2B> <stop_duration_2B>  (6 bytes total)
            payload = f"0A{mode:02X}{param1:04X}{param2:04X}"
        return send_downlink(dev_eui, payload, fport=2, confirmed=confirmed)

    @mcp.tool()
    def set_vibration_mode5(
        dev_eui: str,
        odr: int = 9,
        scale: int = 0,
        resolution: int = 0,
        watermark: int = 0x14,
        tdc_seconds: int = 30,
        confirmed: bool = False,
    ) -> str:
        """Set Mode 5 (max acceleration) for an LHT65N-VIB sensor.

        Args:
            dev_eui: The DevEUI of the target device.
            odr: Output data rate 1-9 (9 = 5376Hz default).
            scale: Acceleration range: 0=+/-2g, 1=+/-4g, 2=+/-8g, 3=+/-16g.
            resolution: 0=12-bit HR, 1=10-bit normal, 2=8-bit low-power.
            watermark: Fixed to 0x14 (20).
            tdc_seconds: Measurement interval 15-3600 seconds (default 30).
            confirmed: Whether to request confirmed downlink.
        """
        if tdc_seconds < 15 or tdc_seconds > 3600:
            return "Error: tdc_seconds must be 15-3600"

        payload = f"0A05{odr:02X}{scale:02X}{resolution:02X}{watermark:02X}{tdc_seconds:04X}"
        return send_downlink(dev_eui, payload, fport=2, confirmed=confirmed)

    @mcp.tool()
    def set_vibration_sensitivity(
        dev_eui: str,
        accel_range: int = 0,
        frequency: int = 4,
        threshold: int = 10,
        duration_ms: int = 12,
        confirmed: bool = False,
    ) -> str:
        """Set vibration detection sensitivity (VIBSET) for an LHT65N-VIB sensor.

        Args:
            dev_eui: The DevEUI of the target device.
            accel_range: 0=+/-2g, 1=+/-4g, 2=+/-8g, 3=+/-16g (default: 0).
            frequency: 0=25Hz, 1=50Hz, 2=100Hz, 3=200Hz, 4=400Hz (default: 4).
            threshold: Interrupt threshold in units of 16mg (e.g. 6=96mg, 10=160mg). Default: 10.
            duration_ms: Interrupt detection duration in milliseconds (default: 12).
            confirmed: Whether to request confirmed downlink.
        """
        if accel_range not in (0, 1, 2, 3):
            return "Error: accel_range must be 0-3"
        if frequency not in (0, 1, 2, 3, 4):
            return "Error: frequency must be 0-4"

        payload = f"09{accel_range:04X}{frequency:04X}{threshold:04X}{duration_ms:04X}"
        return send_downlink(dev_eui, payload, fport=2, confirmed=confirmed)

    @mcp.tool()
    def set_alarm_interval(
        dev_eui: str,
        minutes: int = 0,
        confirmed: bool = False,
    ) -> str:
        """Set the alarm repeat interval for an LHT65N-VIB sensor.

        Args:
            dev_eui: The DevEUI of the target device.
            minutes: Alarm interval in minutes. 0 = alarm once only (default: 0).
            confirmed: Whether to request confirmed downlink.
        """
        if minutes < 0 or minutes > 255:
            return "Error: minutes must be 0-255"

        payload = f"08{minutes:02X}"
        return send_downlink(dev_eui, payload, fport=2, confirmed=confirmed)
