#!/usr/bin/env python

import os
import subprocess
import tarfile
import urllib.request
from pathlib import Path


def run(cmd):
    """Run a shell command and fail only if exit code is non-zero."""
    print("[RUN] {}".format(" ".join(cmd)), flush=True)

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("[ERROR] Command failed with exit code {}".format(result.returncode))
        print("[STDOUT] {}".format(result.stdout))
        print("[STDERR] {}".format(result.stderr))
        raise RuntimeError("Command failed: {}".format(" ".join(cmd)))


def download_file(url, dest):
    """Download a file if it does not already exist."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        print("[SKIP] {} already exists.".format(dest.name))
        return

    print("[DOWNLOAD] {} → {}".format(url, dest))
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        raise RuntimeError("Failed to download {}: {}".format(url, e))


def extract_tar_gz(tar_path, dest_dir):
    """Extract a .tar.gz archive."""
    print("[EXTRACT] {} → {}".format(tar_path.name, dest_dir))
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(dest_dir)


def compress_and_index_bed(bed_path):
    """Compress a BED file and index it with tabix."""
    bed_gz = bed_path.with_suffix(".bed.gz")
    tbi_file = bed_gz.with_suffix(".bed.gz.tbi")

    if bed_gz.exists() and tbi_file.exists():
        print("[SKIP] {} and {} already exist.".format(bed_gz.name, tbi_file.name))
        return

    print("[COMPRESS] {} → {}".format(bed_path.name, bed_gz.name))
    run(["bgzip", "-f", str(bed_path.resolve())])

    print("[INDEX] {} → {}".format(bed_gz.name, tbi_file.name))
    run(["tabix", "-p", "bed", str(bed_gz.resolve())])


def generate_version_yml() -> None:
        with open("versions.yml", "w") as yml:
            yml.write("${task.process}\\n")
            yml.write("stage_refs: ${params.version}\\n")


def main():
    bed_url = "${bed_url}"
    ref_outdir = "${ref_outdir}"

    ref_dir = Path(ref_outdir).resolve()
    ref_dir.mkdir(parents=True, exist_ok=True)

    print("[INFO] Using reference output directory: {}".format(ref_dir))

    # -------------------------
    # Reference VCF files
    # -------------------------
    vcf_urls = [
        "ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/GRCh38_reference_genome/other_mapping_resources/ALL.wgs.1000G_phase3.GRCh38.ncbi_remapper.20150424.shapeit2_indels.vcf.gz",
        "ftp://gsapubftp-anonymous@ftp.broadinstitute.org/bundle/hg38/dbsnp_146.hg38.vcf.gz"
    ]

    print("[INFO] Downloading VCF files")
    for url in vcf_urls:
        dest = ref_dir / os.path.basename(url)
        download_file(url, dest)

    # -------------------------
    # Reference genome
    # -------------------------
    genome_urls = {
        "GRCh38.d1.vd1.fa.tar.gz": "https://api.gdc.cancer.gov/data/254f697d-310d-4d7d-a27b-27fbf767a834",
        "GRCh38.d1.vd1_GATK_indices.tar.gz": "https://api.gdc.cancer.gov/data/2c5730fb-0909-4e2a-8a7a-c9a7f8b2dad5",
    }

    print("[INFO] Downloading reference genome files")
    for fname, url in genome_urls.items():
        tar_dest = ref_dir / fname
        download_file(url, tar_dest)
        extract_tar_gz(tar_dest, ref_dir)

    # -------------------------
    # Exome target region (.bb)
    # -------------------------
    bb_name = os.path.basename(bed_url.strip())
    bb_dest = ref_dir / bb_name

    print("[INFO] Downloading exome target region: {}".format(bed_url))
    download_file(bed_url, bb_dest)

    if not bb_dest.exists():
        raise RuntimeError("Input .bb file not found: {}".format(bb_dest))

    # -------------------------
    # bigBedToBed binary
    # -------------------------
    print("[INFO] Downloading bigBedToBed binary")
    bigbed_url = "https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/bigBedToBed"
    bigbed_bin = ref_dir / "bigBedToBed"
    download_file(bigbed_url, bigbed_bin)
    bigbed_bin.chmod(0o755)

    # -------------------------
    # Convert .bb → .bed
    # -------------------------
    bed_dest = ref_dir / bb_name.replace(".bb", ".bed")

    print("[INFO] Converting .bb to .bed")
    run([
        str(bigbed_bin.resolve()),
        str(bb_dest.resolve()),
        str(bed_dest.resolve())
    ])

    # -------------------------
    # Compress & index BED
    # -------------------------
    print("[INFO] Compressing and indexing BED file")
    compress_and_index_bed(bed_dest)

    print("[INFO] All reference files staged at {}".format(ref_dir))

    # -------------------------
    # versions.yml
    # -------------------------
    print("[INFO] Generating versions.yml")
    generate_version_yml()


if __name__ == "__main__":
    main()
