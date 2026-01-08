#!/usr/bin/env python

import hashlib
import requests
from pathlib import Path

def download_file(url: str, dest: Path):
    """Download file from a URL with retries."""
    for attempt in range(5):
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            dest.write_bytes(response.content)
            return
        except requests.RequestException as e:
            print(f"Attempt {attempt+1}/5 failed: {e}")
    raise RuntimeError(f"Failed to download {url} after 5 attempts")

def verify_checksum(file_path: Path, expected_md5: str):
    """Verify file MD5 checksum."""
    md5 = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    actual_md5 = md5.hexdigest()
    if actual_md5 != expected_md5:
        raise ValueError(f"Checksum mismatch for {file_path.name}\nExpected: {expected_md5}\nActual:   {actual_md5}")
    print(f" Checksum Verified: {file_path.name}")

def main():

    files = [
        {
            "url": "https://huggingface.co/tron-mainz/3ddensenet_snv/resolve/main/3ddensenet_snv.pt",
            "filename": "3ddensenet_snv.pt",
            "checksum": "0caf56d20bf3324a7d36614229105cc1",
        },
        {
            "url": "https://huggingface.co/tron-mainz/3ddensenet_indel/resolve/main/3ddensenet_indel.pt",
            "filename": "3ddensenet_indel.pt",
            "checksum": "a48a4d46df5c041c61d320d10c3857ca",
        },
        {
            "url": "https://huggingface.co/tron-mainz/extra_trees.snv/resolve/main/extra_trees.snv.joblib",
            "filename": "extra_trees.snv.joblib",
            "checksum": "8fa269b15cba16b98b107b594b162b72",
        },
        {
            "url": "https://huggingface.co/tron-mainz/extra_trees.indel/resolve/main/extra_trees.indel.joblib",
            "filename": "extra_trees.indel.joblib",
            "checksum": "511718696c1c0997832b5b942beebf54",
        },
    ]

    for f in files:
        
        dest = Path(f["filename"])
        print(f"\nDownloading {f['filename']} ...")
        download_file(f["url"], dest)
        verify_checksum(dest, f["checksum"])

    print("\n All models downloaded and verified")

if __name__ == "__main__":
    main()
