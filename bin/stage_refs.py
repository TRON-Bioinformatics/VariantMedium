#!/usr/bin/env python3
"""
Download and prepare hg38 reference data.

Usage:
    ./download_references.py <output_dir>

Example:
    ./download_references.py /path/to/ref_data
"""

import os
import sys
import subprocess
import tarfile
import urllib.request
from pathlib import Path


def run(cmd: list[str]):
    """Run a shell command safely."""
    print(f"[RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Command failed: {' '.join(cmd)}\n{result.stderr}")
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result.stdout


def download_file(url: str, dest: Path):
    """Download a file if it does not already exist."""
    if dest.exists():
        print(f"[SKIP] {dest.name} already exists.")
        return
    print(f"[DOWNLOAD] {url} → {dest}")
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        raise RuntimeError(f"Failed to download {url}: {e}")


def extract_tar_gz(tar_path: Path, dest_dir: Path):
    """Extract a .tar.gz archive."""
    print(f"[EXTRACT] {tar_path.name} → {dest_dir}")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(dest_dir)


def main():
    # -------------------------
    # Parse argument
    # -------------------------
    if len(sys.argv) != 2:
        print("Usage: ./download_references.py <output_dir>")
        sys.exit(1)

    ref_folder = Path(sys.argv[1]).resolve()
    bin_folder = ref_folder / "bin"
    ref_folder.mkdir(parents=True, exist_ok=True)
    bin_folder.mkdir(parents=True, exist_ok=True)

    print(f"📂 Output directory: {ref_folder}\n")

    # -------------------------
    # Reference VCF files
    # -------------------------
    vcf_urls = [
        "ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/GRCh38_reference_genome/other_mapping_resources/ALL.wgs.1000G_phase3.GRCh38.ncbi_remapper.20150424.shapeit2_indels.vcf.gz",
        "ftp://gsapubftp-anonymous@ftp.broadinstitute.org/bundle/hg38/dbsnp_146.hg38.vcf.gz"
    ]
    for url in vcf_urls:
        dest = ref_folder / os.path.basename(url)
        download_file(url, dest)

    # -------------------------
    # Reference genome
    # -------------------------
    genome_urls = {
        "GRCh38.d1.vd1.fa.tar.gz": "https://api.gdc.cancer.gov/data/254f697d-310d-4d7d-a27b-27fbf767a834",
        "GRCh38.d1.vd1_GATK_indices.tar.gz": "https://api.gdc.cancer.gov/data/2c5730fb-0909-4e2a-8a7a-c9a7f8b2dad5",
    }
    for fname, url in genome_urls.items():
        dest = ref_folder / fname
        download_file(url, dest)
        extract_tar_gz(dest, ref_folder)

    # -------------------------
    # Exome target region
    # -------------------------
    bb_url = "http://hgdownload.soe.ucsc.edu/gbdb/hg38/exomeProbesets/S07604624_Covered.bb"
    bb_dest = ref_folder / "S07604624_Covered.bb"
    download_file(bb_url, bb_dest)

    # -------------------------
    # bigBedToBed binary
    # -------------------------
    bigbed_url = "https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/bigBedToBed"
    bigbed_bin = bin_folder / "bigBedToBed"
    download_file(bigbed_url, bigbed_bin)
    bigbed_bin.chmod(0o755)

    # Convert .bb to .bed
    bed_dest = ref_folder / "S07604624_Covered.bed"
    run([str(bigbed_bin), str(bb_dest), str(bed_dest)])

    print("\n✅ All reference files downloaded and prepared successfully.")


if __name__ == "__main__":
    main()
