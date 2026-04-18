"""
Phase 1: Scan for Xiaomi Band, connect, and print BPM in real time.
Run on desktop first to verify the BLE connection works.
"""

import asyncio
from bleak import BleakScanner, BleakClient

# Standard BLE Heart Rate Service and Characteristic UUIDs
HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

def parse_heart_rate(data: bytearray) -> tuple[int, list[float]]:
    """
    Parse the raw BLE heart rate measurement packet.
    
    The first byte is a flags byte:
      - Bit 0: 0 = HR value is uint8, 1 = HR value is uint16
      - Bit 4: 1 = RR interval data is present
    
    Returns: (bpm, list_of_rr_intervals_in_seconds)
    """
    flags = data[0]
    hr_format_16bit = flags & 0x01  # Is HR stored as 16-bit?
    rr_present = (flags >> 4) & 0x01  # Are RR intervals present?

    if hr_format_16bit:
        bpm = int.from_bytes(data[1:3], byteorder="little")
        rr_start = 3
    else:
        bpm = data[1]
        rr_start = 2

    rr_intervals = []
    if rr_present:
        # RR intervals are stored as uint16, in units of 1/1024 seconds
        for i in range(rr_start, len(data) - 1, 2):
            rr_raw = int.from_bytes(data[i:i+2], byteorder="little")
            rr_seconds = rr_raw / 1024.0
            rr_intervals.append(rr_seconds)

    return bpm, rr_intervals


def hr_notification_handler(sender, data: bytearray):
    """Called automatically every time the band sends a heart rate update."""
    bpm, rr_intervals = parse_heart_rate(data)
    rr_str = f"  RR: {[f'{r:.3f}s' for r in rr_intervals]}" if rr_intervals else ""
    print(f"❤  {bpm} BPM{rr_str}")


async def find_xiaomi_band() -> str | None:
    """Scan for BLE devices and return the address of the Xiaomi Band."""
    print("Scanning for BLE devices (10 seconds)...")
    devices = await BleakScanner.discover(timeout=10.0)

    print(f"\nFound {len(devices)} devices:")
    for d in devices:
        print(f"  {d.address}  {d.name or '(unnamed)'}")

    # Look for Xiaomi Band by name — adjust this if your device shows differently
    xiaomi_keywords = ["mi band", "xiaomi", "mi smart band", "band 10", "mi band 10"]
    for d in devices:
        if d.name and any(kw in d.name.lower() for kw in xiaomi_keywords):
            print(f"\n✓ Found Xiaomi Band: {d.name} ({d.address})")
            return d.address

    print("\n⚠  No Xiaomi Band found automatically.")
    print("Copy an address from the list above and paste it below.")
    address = input("Enter device address manually: ").strip()
    return address if address else None


async def connect_and_monitor(address: str):
    """Connect to the band and stream heart rate until interrupted."""
    print(f"\nConnecting to {address}...")

    async with BleakClient(address, timeout=20.0) as client:
        print(f"✓ Connected! MTU: {client.mtu_size}")

        # Verify the Heart Rate Service exists on this device
        services = client.services
        hr_service = services.get_service(HR_SERVICE_UUID)
        if hr_service is None:
            print("✗ Heart Rate Service not found on this device.")
            print("  Available services:")
            for s in services:
                print(f"    {s.uuid}")
            return

        print("✓ Heart Rate Service found")
        print("Streaming heart rate — press Ctrl+C to stop\n")

        # Subscribe to notifications (NOT polling — much more efficient)
        await client.start_notify(HR_MEASUREMENT_UUID, hr_notification_handler)

        # Keep running until user presses Ctrl+C
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            await client.stop_notify(HR_MEASUREMENT_UUID)


async def main():
    address = await find_xiaomi_band()
    if address:
        await connect_and_monitor(address)
    else:
        print("No device selected. Exiting.")


if __name__ == "__main__":
    asyncio.run(main())