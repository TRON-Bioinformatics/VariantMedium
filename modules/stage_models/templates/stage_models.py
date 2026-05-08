import fire
import hashlib
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def download_file(url: str, dest: Path):
    """Stream-download file from a URL with retries."""
    for attempt in range(5):
        try:
            with requests.get(url, timeout=60, stream=True) as response:
                response.raise_for_status()
                with dest.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        f.write(chunk)
            return
        except requests.RequestException as e:
            print("Attempt {}/5 failed: {}".format(attempt + 1, e))
    raise RuntimeError("Failed to download {} after 5 attempts".format(url))


def verify_checksum(file_path: Path, expected_md5: str):
    """Verify file MD5 checksum."""
    md5 = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    actual_md5 = md5.hexdigest()
    if actual_md5 != expected_md5:
        raise ValueError(
            "Checksum mismatch for {} Expected: {} Actual:   {}".format(
                file_path.name, expected_md5, actual_md5
            )
        )
    print(" Checksum Verified: {}".format(file_path.name))


def generate_version_yml(task_process: str, version: str) -> None:
    with open("versions.yml", "w") as yml:
        yml.write("{}\n".format(task_process))
        yml.write("stage_models: {}\n".format(version))


def download_and_verify(f, output_dir):
    """Download a single file and verify its checksum. Returns filename."""
    dest = Path(os.path.join(output_dir, f["filename"]))
    if dest.exists():
        print("Already exists, verifying checksum: {}".format(f["filename"]))
        try:
            verify_checksum(dest, f["checksum"])
            print("Skipping download: {}".format(f["filename"]))
            return f["filename"]
        except ValueError:
            print(
                "Checksum mismatch for existing file, re-downloading: {}".format(
                    f["filename"]
                )
            )

    print("Downloading {} ...".format(f["filename"]))
    download_file(f["url"], dest)
    verify_checksum(dest, f["checksum"])
    return f["filename"]


def main(models_dir: str, task_process: str, version: str):
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

    output_dir = Path(models_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print("Downloading models to {}".format(output_dir.resolve()))

    with ThreadPoolExecutor(max_workers=len(files)) as executor:
        futures = {
            executor.submit(download_and_verify, f, output_dir): f["filename"]
            for f in files
        }
        for future in as_completed(futures):
            future.result()  # re-raises any exception from the worker

    print("All models downloaded and verified")

    generate_version_yml(task_process, version)
    print("Generated versions.yml")


if __name__ == "__main__":
    fire.Fire(main)
