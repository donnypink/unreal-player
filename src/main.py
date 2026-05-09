"""Main entry point for UE Controller."""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controllers.ue_controller import UEController


def main():
    """Main entry point."""
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    try:
        controller = UEController(config_path)
        controller.run()
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
