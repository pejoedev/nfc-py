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


def write_nfc_tag(serial_number):
    """Write serial number to NFC tag using nfc-mfsetuid"""
    print(f"\nPreparing to write: '{serial_number}'")
    print("Waiting for NFC tag to write to...\n")

    try:
        # For writing UID/serial to Mifare Classic cards
        result = subprocess.run(
            ['nfc-mfsetuid', serial_number],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)

        if result.returncode == 0:
            print(f"✓ Successfully wrote: '{serial_number}'")
            return True
        else:
            if result.stderr:
                print(f"Error: {result.stderr}")
            print("✗ Failed to write tag")
            return False

    except FileNotFoundError:
        print("✗ nfc-mfsetuid not found")
        print("Install: sudo apt-get install nfc-tools")
        return False
    except subprocess.TimeoutExpired:
        print("✗ Timeout - no tag detected or write failed")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def write_ndef_text(serial_number):
    """Alternative: write as NDEF text record"""
    print(f"\nPreparing to write NDEF: '{serial_number}'")
    print("Waiting for NFC tag...\n")

    try:
        # Create temporary NDEF message file
        import tempfile
        import os

        # Try using nfcpy with explicit Python path
        script = f"""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
from nfc import ContactlessFrontend
from nfc.clf import RemoteTarget
from ndef import TextRecord, Message

try:
    clf = ContactlessFrontend()
    with clf:
        target = clf.sense(RemoteTarget('106A'), timeout=10)
        if target:
            tag = nfc.tag.activate(clf, target)
            if tag and tag.ndef and tag.ndef.is_writeable:
                record = TextRecord('{serial_number}', language='en')
                tag.ndef.message = Message(record)
                print("✓ Successfully wrote NDEF")
            else:
                print("✗ Tag not writable")
        else:
            print("✗ No tag detected")
except Exception as e:
    print(f"✗ Error: {{e}}")
"""

        result = subprocess.run(
            [sys.executable, '-c', script],
            capture_output=True,
            text=True,
            timeout=15
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        return result.returncode == 0

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


def main():
    """Main menu"""
    print("\n" + "=" * 50)
    print("NFC Tag Manager - ACR122U")
    print("=" * 50 + "\n")

    list_devices()

    while True:
        print("\nOptions:")
        print("  1. Read NFC tag")
        print("  2. Write serial number to tag (UID)")
        print("  3. Write as NDEF text")
        print("  4. Exit")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == '1':
            print()
            read_nfc_tag()

        elif choice == '2':
            serial = input("\nEnter serial number (hex, e.g. 1B2A0A31): ").strip()

            if not serial:
                print("✗ Serial number cannot be empty")
                continue

            # Validate hex format
            try:
                int(serial, 16)
            except ValueError:
                print("✗ Invalid hex format")
                continue

            confirm = input(f"Write UID '{serial}' to tag? (y/n): ").strip().lower()
            if confirm == 'y':
                write_nfc_tag(serial)
            else:
                print("Cancelled")

        elif choice == '3':
            serial = input("\nEnter serial number to write as text: ").strip()

            if not serial:
                print("✗ Serial number cannot be empty")
                continue

            confirm = input(f"Write '{serial}' to tag as NDEF? (y/n): ").strip().lower()
            if confirm == 'y':
                write_ndef_text(serial)
            else:
                print("Cancelled")

        elif choice == '4':
            print("Exiting...")
            break

        else:
            print("✗ Invalid option")


if __name__ == "__main__":
    main()