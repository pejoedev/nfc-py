import subprocess
import sys
import os


def read_nfc_tag():
    """Read NFC tag using libnfc (nfc-poll)"""
    print("NFC Tag Reader - ACR122U")
    print("=" * 50)
    print("Place NFC tag on reader (and remove after approx 5sec to continue)...\n")

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
    print("Identifying card type...")
    print("Place NFC tag on reader (and remove after approx 5sec to continue)...\n")

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
            card_type = "mifare_classic"
        elif "Mifare Ultralight" in output:
            print("Card Type: Mifare Ultralight (limited write)")
            card_type = "mifare_ultralight"
        elif "NTAG" in output:
            print("Card Type: NTAG (use NDEF for text)")
            card_type = "ntag"
        elif "ISO/IEC 14443A" in output:
            print("Card Type: ISO14443A (generic)")
            print("\nFull output:")
            print(output)
            card_type = "iso14443a"
        else:
            print("Card Type: Unknown")
            print("\nFull output:")
            print(output)
            card_type = "unknown"

        return card_type

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
    print("  Genuine/commercial → use alternative method\n")

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
    print("Place NFC tag on reader...\n")

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
            elif "Not a special card" in error_text or \
                 "not special" in error_text.lower():
                print("→ This is NOT a Chinese clone card")
                print("→ nfc-mfsetuid only works with clones")
            elif "Permission denied" in error_text or \
                 "not allowed" in error_text.lower():
                print("→ Write permission denied")
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
    print("=" * 50 + "\n")

    list_devices()

    while True:
        print("\nOptions:")
        print("  1. Read NFC tag")
        print("  2. Identify card type")
        print("  3. Diagnose card (UID write capability)")
        print("  4. Write serial number to tag (UID - clones only)")
        print("  5. Exit")

        choice = input("\nSelect option (1-5): ").strip()

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
            serial = input(
                "\nEnter serial number (hex, e.g. C2B44B41): "
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

        elif choice == '5':
            print("Exiting...")
            break

        else:
            print("✗ Invalid option")


if __name__ == "__main__":
    main()