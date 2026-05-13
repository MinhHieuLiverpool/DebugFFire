import urllib.error
import urllib.request


DEFAULT_HOST = "127.0.0.1:8000"

LABEL_TO_LOCATION = {
    "HEV": (1, 0, 0),
    "HEV.ALAN": (1, 0, 1),
    "BOOYAH": (1, 0, 2),
    "WAG": (1, 0, 3),
    "PGM 5": (1, 0, 4),
}


def press_button(host: str, page: int, row: int, col: int) -> None:
    url = f"http://{host}/api/location/{page}/{row}/{col}/press"
    request = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(request, timeout=3) as response:
        response.read()


def interactive_loop() -> None:
    host = input(f"Companion host [{DEFAULT_HOST}]: ").strip() or DEFAULT_HOST
    print("Nhap ten nut de goi (Enter de thoat). Vi du: HEV")
    print("Nut ho tro:", ", ".join(LABEL_TO_LOCATION.keys()))

    while True:
        label = input("> ").strip()
        if not label:
            break

        location = LABEL_TO_LOCATION.get(label)
        if not location:
            print("Khong tim thay nut. Hay nhap dung ten.")
            continue

        page, row, col = location
        try:
            press_button(host, page, row, col)
            print(f"Da goi: {label} ({page}/{row}/{col})")
        except urllib.error.URLError as exc:
            print(f"Loi goi Companion: {exc}")


def main() -> None:
    interactive_loop()


if __name__ == "__main__":
    main()
