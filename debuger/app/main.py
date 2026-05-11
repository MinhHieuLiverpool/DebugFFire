import argparse
import os
import sys

from player_tracker import iter_player_names



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FreeFire InitTrackingPlayer tracker (GUI by default)."
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to the debug log file.",
    )
    parser.add_argument(
        "--poll",
        type=float,
        default=0.2,
        help="Polling interval in seconds (default: 0.2).",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in console mode instead of GUI.",
    )
    return parser.parse_args()


def _run_cli(path: str, poll_interval: float) -> int:
    try:
        for name in iter_player_names(path, poll_interval=poll_interval):
            print(name, flush=True)
    except KeyboardInterrupt:
        return 0

    return 0


def main() -> int:
    args = parse_args()
    if not args.cli:
        from gui import main as gui_main

        return gui_main()

    path = args.path
    if not path:
        path = input("Nhap duong dan file debug: ").strip()

    if not path:
        print("Khong co duong dan file.", file=sys.stderr)
        return 2

    if not os.path.isfile(path):
        print(f"File khong ton tai: {path}", file=sys.stderr)
        return 2

    return _run_cli(path, args.poll)


if __name__ == "__main__":
    raise SystemExit(main())
