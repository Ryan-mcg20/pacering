import asyncio
from bleak import BleakScanner, BleakClient

# Standard BLE Heart Rate Service UUIDs
HR_SERVICE_UUID    = "0000180d-0000-1000-8000-00805f9b34fb"
HR_CHAR_UUID       = "00002a37-0000-1000-8000-00805f9b34fb"

# This will hold the latest heart rate reading
latest_hr = 0

def parse_hr_measurement(data: bytearray) -> int:
    """
    The heart rate comes as raw bytes. This function decodes them.
    Byte 0 is a flags byte. If bit 0 is 0, HR is 1 byte. If bit 0 is 1, HR is 2 bytes.
    """
    flags = data[0]
    if flags & 0x01:  # 16-bit HR value
        hr = int.from_bytes(data[1:3], byteorder='little')
    else:             # 8-bit HR value (most common)
        hr = data[1]
    return hr

async def scan_for_band():
    """Scans for nearby BLE devices and prints them all."""
    print("Scanning for BLE devices... (10 seconds)")
    devices = await BleakScanner.discover(timeout=10.0)
    print(f"\nFound {len(devices)} devices:")
    for i, d in enumerate(devices):
        print(f"  [{i}] {d.name or 'Unknown'} | Address: {d.address}")
    return devices

async def connect_and_stream(device_address: str, hr_callback):
    """
    Connects to the band at device_address and streams heart rate.
    hr_callback is a function you supply — it gets called with each new BPM value.
    """
    print(f"Connecting to {device_address}...")
    async with BleakClient(device_address, timeout=20.0) as client:
        print("Connected! Starting heart rate stream...")

        def notification_handler(sender, data: bytearray):
            bpm = parse_hr_measurement(data)
            if bpm > 0:  # ignore zero readings (band not on wrist)
                hr_callback(bpm)

        # Subscribe to HR notifications (this is the key — NOT polling)
        await client.start_notify(HR_CHAR_UUID, notification_handler)
        print("Streaming... press Ctrl+C to stop.")

        # Keep the connection alive
        while client.is_connected:
            await asyncio.sleep(1)

# Quick test — run this file directly to see if your band is found
if __name__ == "__main__":
    async def test():
        devices = await scan_for_band()
        if not devices:
            print("No devices found. Is Bluetooth on?")
            return
        # Look for your Xiaomi Band in the list
        band = next((d for d in devices if d.name and
                     any(x in d.name.lower() for x in
                         ['mi band', 'xiaomi', 'band', 'mi smart'])), None)
        if band:
            print(f"\nFound your band: {band.name} at {band.address}")
            def on_hr(bpm):
                print(f"Heart Rate: {bpm} BPM")
            await connect_and_stream(band.address, on_hr)
        else:
            print("\nXiaomi Band not found. Check it's unpaired from Mi Fitness.")

    asyncio.run(test())
