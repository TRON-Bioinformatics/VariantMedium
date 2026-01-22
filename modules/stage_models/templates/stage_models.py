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
            print("Attempt {}/5 failed: {}".format(attempt+1, e))
    raise RuntimeError("Failed to download {} after 5 attempts".format(url))

def verify_checksum(file_path: Path, expected_md5: str):
    """Verify file MD5 checksum."""
    md5 = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    actual_md5 = md5.hexdigest()
    if actual_md5 != expected_md5:
        raise ValueError("Checksum mismatch for {} Expected: {} Actual:   {}".format(file_path.name, expected_md5, actual_md5))
    print(" Checksum Verified: {}".format(file_path.name))

def generate_version_yml() -> None:
    with open("versions.yml", "w") as yml:
        yml.write("${task.process}\\n")
        yml.write("stage_models: ${params.version}\\n")

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

    output_dir = Path("./models")
    output_dir.mkdir(parents=True, exist_ok=True)
    print("Downloading models to {}".format(output_dir.resolve()))

    for f in files:
        
        dest = output_dir / f["filename"]
        print("Downloading {} ...".format(f["filename"]))
        download_file(f["url"], dest)
        verify_checksum(dest, f["checksum"])

    print("All models downloaded and verified")

    generate_version_yml()
    print("Generated versions.yml")

if __name__ == "__main__":
    main()
