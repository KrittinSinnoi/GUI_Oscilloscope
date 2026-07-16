import pyvisa
from datetime import datetime
from pathlib import Path


def find_rigol_instrument(rm):
    """Find the first RIGOL oscilloscope."""
    resources = rm.list_resources()
    usb_resources = [r for r in resources if r.startswith("USB")]

    if not usb_resources:
        raise RuntimeError("No USB VISA instruments found.")

    print("Searching for RIGOL oscilloscope...")

    for resource in usb_resources:
        try:
            scope = rm.open_resource(resource)
            scope.timeout = 3000

            idn = scope.query("*IDN?").strip()

            print(resource)
            print(idn)

            if "RIGOL" in idn.upper():
                print("\nUsing:", resource)
                return scope

            scope.close()

        except Exception as ex:
            print(ex)

    raise RuntimeError("No RIGOL oscilloscope found.")


def read_ieee_block(scope):
    """
    Read an IEEE-488.2 definite-length binary block.
    """
    header = scope.read_bytes(2)

    if header[0:1] != b"#":
        raise RuntimeError(
            f"Unexpected header {header!r}"
        )

    digits = int(header[1:2])

    if digits == 0:
        raise RuntimeError(
            "Indefinite-length block not supported."
        )

    length = int(scope.read_bytes(digits).decode())

    print(f"Receiving {length} bytes...")

    data = scope.read_bytes(length)

    return data


def capture_screenshot(scope):
    """
    Capture a PNG screenshot from a DHO800 series oscilloscope.
    """
    scope.timeout = 5000

    # DHO800 screenshot command
    scope.write(":DISPlay:SNAP?")

    png = read_ieee_block(scope)

    if not png.startswith(b"\x89PNG"):
        raise RuntimeError(
            "Returned data is not a PNG image."
        )

    return png


def save_png(data, directory="."):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = Path(directory) / f"dho814_{timestamp}.png"
    filename.write_bytes(data)
    return filename


def main():
    rm = pyvisa.ResourceManager("@py")
    scope = None

    try:
        scope = find_rigol_instrument(rm)

        print(scope.query("*IDN?"))

        png = capture_screenshot(scope)

        outfile = save_png(
            png,
            Path(__file__).parent
        )

        print(f"\nSaved {len(png)} bytes")
        print(outfile)

    finally:
        if scope is not None:
            scope.close()

        rm.close()


if __name__ == "__main__":
    main()
