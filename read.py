import subprocess
import sys


def read_nfc_tag():
    """Read NFC tag using libnfc (nfc-poll)"""
    print("NFC Tag Reader - ACR122U")
    print("=" * 50)
    print("Waiting for NFC tag...\n")

    try:
        result = subprocess.run(
            ['nfc-poll'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.stdout:
            print(result.stdout)

        if "ISO/IEC 14443A" in result.stdout:
            print("✓ Tag read successfully!")
            return True
        else:
            print("✗ No tag detected")
            return False

    except FileNotFoundError:
        print("✗ nfc-poll not installed")
        print("Install: sudo apt-get install libnfc-bin")
        return False
    except subprocess.TimeoutExpired:
        print("✗ Timeout - no tag detected")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def list_devices():
    """List available NFC readers"""
    print("Available NFC Devices:")
    print("=" * 50 + "\n")

    try:
        result = subprocess.run(
            ['nfc-list'],
            capture_output=True,
            text=True,
            timeout=5
        )

        print(result.stdout if result.stdout else "No devices found")

    except FileNotFoundError:
        print("nfc-list not installed")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    list_devices()
    print("\n")
    read_nfc_tag()