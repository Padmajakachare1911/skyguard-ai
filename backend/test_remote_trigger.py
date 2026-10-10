"""
SkyGuard AI — Remote Trigger Verification Test
==============================================
Run this script from ANY computer on the same Wi-Fi / LAN network
(or locally) to verify that violation events are successfully delivered
to the SkyGuard FastAPI backend and immediately appear on the React dashboard.

Usage:
    python backend/test_remote_trigger.py
    python backend/test_remote_trigger.py --host 10.241.28.122 --port 8000
    python backend/test_remote_trigger.py --type no-vest
    python backend/test_remote_trigger.py --upload sample.jpg
"""

import sys
import argparse
import datetime
from pathlib import Path
import requests


def main():
    parser = argparse.ArgumentParser(description="Test remote violation trigger to SkyGuard AI dashboard")
    parser.add_argument(
        "--host",
        default="192.168.1.6",
        help="Backend IP address (e.g. 192.168.1.6 or 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        default="8000",
        help="Backend port (default: 8000)"
    )
    parser.add_argument(
        "--type",
        default="no-helmet",
        choices=["no-helmet", "no-vest", "restricted-zone", "machinery-proximity", "person-down"],
        help="Violation type to trigger"
    )
    parser.add_argument(
        "--upload",
        default=None,
        help="Optional local image file path to test /violations/upload-snapshot before triggering"
    )
    args = parser.parse_args()

    backend_url = f"http://{args.host}:{args.port}"
    violations_endpoint = f"{backend_url}/violations"
    upload_endpoint = f"{backend_url}/violations/upload-snapshot"

    print("=" * 65)
    print("  🛡️  SKYGUARD AI — REMOTE TRIGGER VERIFICATION TEST")
    print("=" * 65)
    print(f"Target Backend : {backend_url}")
    print(f"Endpoint       : {violations_endpoint}")
    print(f"Violation Type : {args.type}")
    print("-" * 65)

    # 1. Health check
    try:
        print("[1/2] Checking connection to backend...")
        r = requests.get(backend_url, timeout=3.0)
        print(f"      Connected! Server response: {r.json()}")
    except requests.exceptions.RequestException as e:
        print(f"      [WARN] Root check failed: {e}")
        print("      Attempting POST /violations directly anyway...")

    # Optional snapshot upload
    image_url = "test_snapshot.jpg"
    if args.upload:
        upload_path = Path(args.upload)
        if upload_path.exists():
            try:
                print(f"[Upload] Uploading snapshot image {upload_path.name}...")
                with open(upload_path, "rb") as f:
                    files = {"file": (upload_path.name, f, "image/jpeg")}
                    up_res = requests.post(upload_endpoint, files=files, timeout=5.0)
                if up_res.status_code in (200, 201):
                    image_url = up_res.json().get("image_url", image_url)
                    print(f"         Upload success! Image URL: {image_url}")
                else:
                    print(f"         [WARN] Upload failed with status {up_res.status_code}: {up_res.text}")
            except Exception as e:
                print(f"         [WARN] Upload exception: {e}")
        else:
            print(f"[Upload] File not found: {args.upload}, proceeding with fallback snapshot string.")

    # 2. Dispatch test payload
    payload = {
        "person_id": "WORKER-101",
        "type": args.type,
        "confidence": 0.94,
        "latitude": 19.0332,
        "longitude": 73.0299,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "image_url": image_url
    }

    try:
        print("\n[2/2] Sending test violation payload...")
        res = requests.post(violations_endpoint, json=payload, timeout=4.0)
        print(f"      HTTP Status Code : {res.status_code}")
        if res.status_code in (200, 201):
            print("      SUCCESS! Response from server:")
            print(f"      {res.json()}")
            print("\n" + "=" * 65)
            print("  ✅ VERIFICATION COMPLETE!")
            print("  Check your React Dashboard screen now — the new alert should")
            print(f"  be displayed under 'Recent Violations' as '{args.type}'.")
            print("=" * 65)
        else:
            print(f"      [ERROR] Server responded with error: {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"\n[FAILED] Could not connect to {violations_endpoint}")
        print(f"Reason: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure run_backend.bat is running on the host PC.")
        print(f"2. Ensure both PCs are connected to the SAME Wi-Fi or mobile hotspot.")
        print("3. Check Windows Firewall on the host PC (allow Python / port 8000).")
        print(f"4. If testing on the same PC, try: python backend/test_remote_trigger.py --host 127.0.0.1")
        sys.exit(1)


if __name__ == "__main__":
    main()
