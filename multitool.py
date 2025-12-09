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
    """Write serial number to NFC tag using nfcpy"""
    try:
        import nfc
        from ndef import TextRecord, Message

        print(f"\nPreparing to write: '{serial_number}'")
        print("Waiting for NFC tag to write to...\n")

        # Create NDEF message with the serial number
        record = TextRecord(serial_number, language='en')
        message = Message(record)

        # Try to connect and write
        clf = nfc.ContactlessFrontend()

        with clf:
            from nfc.clf import RemoteTarget

            # Poll for tag
            target = clf.sense(RemoteTarget('106A'), timeout=10)

            if target is None:
                print("✗ No tag detected")
                return False

            print("✓ Tag detected!")

            # Activate tag
            tag = nfc.tag.activate(clf, target)

            if tag is None:
                print("✗ Failed to activate tag")
                return False

            print(f"✓ Tag activated: {tag.identifier.hex()}")

            # Check if writable
            if tag.ndef is None:
                print("✗ Tag does not support NDEF")
                return False

            if not tag.ndef.is_writeable:
                print("✗ Tag is read-only")
                return False

            # Write the message
            print("Writing to tag...")
            tag.ndef.message = message

            print(f"✓ Successfully wrote: '{serial_number}'")
            print(f"  Tag ID: {tag.identifier.hex()}")
            print(f"  NDEF Capacity: {tag.ndef.capacity} bytes")
            print(f"  Used: {tag.ndef.length} bytes")

            return True

    except ImportError:
        print("✗ nfcpy or ndef not installed")
        print("Install: pip install nfcpy ndef")
        return False
    except IOError:
        print("✗ Could not connect to NFC reader")
        print("Make sure ACR122U is connected")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
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
        print("  2. Write serial number to tag")
        print("  3. Exit")

        choice = input("\nSelect option (1-3): ").strip()

        if choice == '1':
            print()
            read_nfc_tag()

        elif choice == '2':
            serial = input("\nEnter serial number to write: ").strip()

            if not serial:
                print("✗ Serial number cannot be empty")
                continue

            if len(serial) > 255:
                print("✗ Serial number too long (max 255 characters)")
                continue

            confirm = input(f"Write '{serial}' to tag? (y/n): ").strip().lower()
            if confirm == 'y':
                write_nfc_tag(serial)
            else:
                print("Cancelled")

        elif choice == '3':
            print("Exiting...")
            break

        else:
            print("✗ Invalid option")


if __name__ == "__main__":
    main()