import subprocess
import sys
import os


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


def identify_card_type():
    """Identify the NFC card type"""
    print("Identifying card type...\n")

    try:
        result = subprocess.run(
            ['nfc-poll', '-v'],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + result.stderr

        if "MIFARE Classic" in output:
            print("Card Type: MIFARE Classic 1K (should support UID write)")
            return "mifare_classic"
        elif "Mifare Ultralight" in output:
            print("Card Type: Mifare Ultralight (limited write)")
            return "mifare_ultralight"
        elif "NTAG" in output:
            print("Card Type: NTAG (use NDEF for text)")
            return "ntag"
        elif "ISO/IEC 14443A" in output:
            print("Card Type: ISO14443A (generic)")
            print("\nFull output:")
            print(output)
            return "iso14443a"
        else:
            print("Card Type: Unknown")
            print("\nFull output:")
            print(output)
            return "unknown"

    except FileNotFoundError:
        print("✗ nfc-poll not installed")
        return None
    except subprocess.TimeoutExpired:
        print("✗ Timeout - no tag detected")
        return None
    except Exception as e:
        print(f"Error identifying card: {e}")
        return None


def diagnose_card():
    """Diagnose card write capability"""
    print("Diagnosing card...\n")

    print("Checking nfc-mfsetuid requirements...")
    print(
        "→ nfc-mfsetuid ONLY works with Chinese clone "
        "Mifare Classic 1K cards"
    )
    print("→ Most commercial/genuine cards are NOT compatible\n")

    # Try to read the card
    print("Attempting to read card with nfc-mfclassic...\n")

    try:
        # Create a temp file for the dump
        temp_dump = "/tmp/nfc_test.mfd"

        result = subprocess.run(
            ['nfc-mfclassic', 'r', 'a', 'u', temp_dump],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + result.stderr

        # Clean up temp file
        if os.path.exists(temp_dump):
            os.remove(temp_dump)

        if result.returncode == 0:
            print("✓ Successfully read card")
            print("→ Card is readable (default keys work)")
            print("→ Card MAY be writable\n")

            # Try to test write capability
            print("Testing write capability...\n")
            diagnose_write_capability()
            return True

        elif "Permission denied" in output or \
             "Access violation" in output or \
             "Authentication failed" in output:
            print("✗ Authentication failed")
            print("→ Card has restricted access")
            print("→ UID cannot be rewritten\n")
            return False

        else:
            print("⚠ Read attempt produced output:")
            print(output)
            return None

    except FileNotFoundError:
        print("✗ nfc-mfclassic not installed")
        print("Install: sudo apt-get install nfc-tools")
        return None

    except subprocess.TimeoutExpired:
        print("✗ Timeout - card not responding")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return None


def diagnose_write_capability():
    """Test if card supports UID write"""
    print("Card vendor detection:")
    print("  Chinese clones → nfc-mfsetuid will work")
    print("  Genuine/commercial → use option 5 (NDEF) instead\n")

    try:
        # Try nfc-mfsetuid with a dummy value to see if it detects the card
        result = subprocess.run(
            ['nfc-mfsetuid', '00000000'],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout + result.stderr

        if "No suitable card found" in output:
            print("Result: Card not detected by nfc-mfsetuid")
            print("→ May not be compatible with nfc-mfsetuid")
            return False

        elif "Setting UID" in output or "Successfully" in output:
            print("Result: Card compatible with nfc-mfsetuid")
            print("→ Card is a Chinese clone (UID writable)")
            return True

        else:
            print("Result: Uncertain compatibility")
            print("Output:", output)
            return None

    except subprocess.TimeoutExpired:
        print("Timeout during write test")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return None


def write_nfc_tag(serial_number):
    """Write serial number to NFC tag using nfc-mfsetuid"""
    print(f"\nPreparing to write: '{serial_number}'")
    print("Waiting for NFC tag to write to...\n")

    try:
        result = subprocess.run(
            ['nfc-mfsetuid', serial_number],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)

        if result.returncode == 0 or "Setting UID" in result.stdout:
            print(f"✓ Successfully wrote: '{serial_number}'")
            return True
        else:
            error_text = result.stderr + result.stdout

            print("✗ Failed to write tag\n")

            if "No suitable card found" in error_text:
                print("→ Card not detected or not compatible")
                print("→ This card may not support UID rewriting")
                print("→ Use option 5 (NDEF text) instead")
            elif "Not a special card" in error_text or \
                 "not special" in error_text.lower():
                print("→ This is NOT a Chinese clone card")
                print("→ nfc-mfsetuid only works with clones")
                print("→ Use option 5 (NDEF text) instead")
            elif "Permission denied" in error_text or \
                 "not allowed" in error_text.lower():
                print("→ Write permission denied")
                print("→ Use option 5 (NDEF text) instead")
            else:
                print("Error output:", error_text)

            return False

    except FileNotFoundError:
        print("✗ nfc-mfsetuid not found")
        print("Install: sudo apt-get install nfc-tools")
        return False
    except subprocess.TimeoutExpired:
        print("✗ Timeout - no tag detected")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def write_ndef_text(serial_number):
    """Alternative: write as NDEF text record"""
    print(f"\nPreparing to write NDEF: '{serial_number}'")
    print("Waiting for NFC tag...\n")

    try:
        script = f"""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
try:
    from nfc import ContactlessFrontend
    from nfc.clf import RemoteTarget
    from ndef import TextRecord, Message
except ImportError as e:
    print("✗ Required package missing:", e)
    print("Install: pip install nfcpy ndef")
    sys.exit(1)

try:
    clf = ContactlessFrontend()
    with clf:
        target = clf.sense(RemoteTarget('106A'), timeout=10)
        if target:
            tag = nfc.tag.activate(clf, target)
            if tag and tag.ndef and tag.ndef.is_writeable:
                record = TextRecord('{serial_number}', language='en')
                tag.ndef.message = Message(record)
                print("✓ Successfully wrote NDEF: {serial_number}")
            else:
                print("✗ Tag not writable or no NDEF support")
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
        if result.stderr and "Deprecation" not in result.stderr:
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
    print("=" * 50)
    print("\nIMPORTANT:")
    print("• Option 4 only works with CHINESE CLONE Mifare 1K cards")
    print("• Most commercial/genuine cards require option 5 (NDEF)")
    print("=" * 50 + "\n")

    list_devices()

    while True:
        print("\nOptions:")
        print("  1. Read NFC tag")
        print("  2. Identify card type")
        print("  3. Diagnose card (UID write capability)")
        print("  4. Write serial number to tag (UID - clones only)")
        print("  5. Write as NDEF text (universal)")
        print("  6. Exit")

        choice = input("\nSelect option (1-6): ").strip()

        if choice == '1':
            print()
            read_nfc_tag()

        elif choice == '2':
            print()
            identify_card_type()

        elif choice == '3':
            print()
            diagnose_card()

        elif choice == '4':
            card_type = identify_card_type()

            if card_type in ["mifare_classic", "iso14443a"]:
                serial = input(
                    "\nEnter serial number (hex, e.g. "
                    "1B2A0A31): "
                ).strip()

                if not serial:
                    print("✗ Serial number cannot be empty")
                    continue

                if len(serial) != 8:
                    print("✗ Serial must be exactly 8 hex characters")
                    continue

                try:
                    int(serial, 16)
                except ValueError:
                    print("✗ Invalid hex format")
                    continue

                confirm = (
                    input(
                        f"Write UID '{serial}' to tag? (y/n): "
                    )
                    .strip()
                    .lower()
                )
                if confirm == 'y':
                    write_nfc_tag(serial)
                else:
                    print("Cancelled")

            elif card_type in ["mifare_ultralight", "ntag"]:
                print("\n⚠ This card type doesn't support UID rewriting")
                print("Use option 5 (NDEF text) instead")

            elif card_type == "unknown":
                print("\n⚠ Unknown card type")
                print("Try option 3 (Diagnose) first")

            elif card_type is None:
                print("\n✗ Could not identify card")

        elif choice == '5':
            serial = input(
                "\nEnter text to write (any string): "
            ).strip()

            if not serial:
                print("✗ Text cannot be empty")
                continue

            confirm = (
                input(
                    f"Write '{serial}' to tag as NDEF? (y/n): "
                )
                .strip()
                .lower()
            )
            if confirm == 'y':
                write_ndef_text(serial)
            else:
                print("Cancelled")

        elif choice == '6':
            print("Exiting...")
            break

        else:
            print("✗ Invalid option")


if __name__ == "__main__":
    main()