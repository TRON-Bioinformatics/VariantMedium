#!/usr/bin/env python

import os
import subprocess
import tarfile
import urllib.request
from pathlib import Path


def run(cmd: list[str]):
    """Run a shell command."""
    print(f"[RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Command failed: {' '.join(cmd)}\n{result.stderr}")
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def download_file(url: str, dest: Path):
    """Download a file if it does not already exist."""
    dest.parent.mkdir(parents=True, exist_ok=True)
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


def compress_and_index_bed(bed_path: Path):
    """Compress a BED file with bgzip (-k to keep original) and index it with tabix."""

    bed_gz = bed_path.with_suffix(".bed.gz")
    tbi_file = bed_gz.with_suffix(".bed.gz.tbi")

    # If both outputs exist, skip
    if bed_gz.exists() and tbi_file.exists():
        print(f"[SKIP] {bed_gz.name} and {tbi_file.name} already exist.")
        return

    print(f"[COMPRESS] {bed_path.name} → {bed_gz.name}")
    run(["bgzip", "-f", str(bed_path.resolve())])

    print(f"[INDEX] {bed_gz.name} → {tbi_file.name}")
    run(["tabix", "-p", "bed", str(bed_gz.resolve())])



def main():
    cwd = Path(".")

    # -------------------------
    # Reference VCF files
    # -------------------------
    vcf_urls = [
        "ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/GRCh38_reference_genome/other_mapping_resources/ALL.wgs.1000G_phase3.GRCh38.ncbi_remapper.20150424.shapeit2_indels.vcf.gz",
        "ftp://gsapubftp-anonymous@ftp.broadinstitute.org/bundle/hg38/dbsnp_146.hg38.vcf.gz"
    ]
    for url in vcf_urls:
        dest = cwd / os.path.basename(url)
        download_file(url, dest)

    # -------------------------
    # Reference genome
    # -------------------------
    genome_urls = {
        "GRCh38.d1.vd1.fa.tar.gz": "https://api.gdc.cancer.gov/data/254f697d-310d-4d7d-a27b-27fbf767a834",
        "GRCh38.d1.vd1_GATK_indices.tar.gz": "https://api.gdc.cancer.gov/data/2c5730fb-0909-4e2a-8a7a-c9a7f8b2dad5",
    }
    for fname, url in genome_urls.items():
        dest = cwd / fname
        download_file(url, dest)
        extract_tar_gz(dest, cwd)

    # -------------------------
    # Exome target region
    # -------------------------
    bb_url = "http://hgdownload.soe.ucsc.edu/gbdb/hg38/exomeProbesets/S07604624_Covered.bb"
    bb_dest = cwd / "S07604624_Covered.bb"
    download_file(bb_url, bb_dest)

    # -------------------------
    # bigBedToBed binary
    # -------------------------
    bigbed_url = "https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/bigBedToBed"
    bigbed_bin = cwd / "bigBedToBed"
    download_file(bigbed_url, bigbed_bin)
    bigbed_bin.chmod(0o755)

    # Convert .bb → .bed
    bed_dest = cwd / "S07604624_Covered.bed"
    run([str(bigbed_bin.resolve()), str(bb_dest.resolve()), str(bed_dest.resolve())])

    # -------------------------
    # Compress BED and create .tbi
    # -------------------------
    compress_and_index_bed(bed_dest)

    print("\n✅ All reference files downloaded and prepared successfully in current directory.")


if __name__ == "__main__":
    main()
