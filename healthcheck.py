import os
import sys
import urllib.request


def main() -> int:
    # В режиме long polling HTTP-сервер не поднимается — проверять нечего.
    if not os.environ.get("WEBHOOK_BASE_URL"):
        return 0

    port = os.environ.get("WEBHOOK_PORT", "8080")
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3)
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
