#!/bin/bash

source ./config.conf


mkdir -p ${REF_FOLDER}/bin

#-------------------------------------------------------------
# Download reference VCF files
#-------------------------------------------------------------

wget -P ${REF_FOLDER} ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/GRCh38_reference_genome/other_mapping_resources/ALL.wgs.1000G_phase3.GRCh38.ncbi_remapper.20150424.shapeit2_indels.vcf.gz
wget -P ${REF_FOLDER} ftp://gsapubftp-anonymous@ftp.broadinstitute.org/bundle/hg38/dbsnp_146.hg38.vcf.gz

#-------------------------------------------------------------
# Download reference genome
#-------------------------------------------------------------

# download hg38 reference from https://gdc.cancer.gov/about-data/gdc-data-processing/gdc-reference-files
curl 'https://api.gdc.cancer.gov/data/254f697d-310d-4d7d-a27b-27fbf767a834' \
    --output ${REF_FOLDER}/GRCh38.d1.vd1.fa.tar.gz
tar xvfz ${REF_FOLDER}/GRCh38.d1.vd1.fa.tar.gz -C ${REF_FOLDER}

# download related GATK indexes:
curl 'https://api.gdc.cancer.gov/data/2c5730fb-0909-4e2a-8a7a-c9a7f8b2dad5' \
    --output ${REF_FOLDER}/GRCh38.d1.vd1_GATK_indices.tar.gz
tar xvfz ${REF_FOLDER}/GRCh38.d1.vd1_GATK_indices.tar.gz -C ${REF_FOLDER}

#-------------------------------------------------------------
# Download exome target region
#-------------------------------------------------------------

# get S07604624 SureSelect Human All Exon V6+UTR from UCSC
wget -P ${REF_FOLDER} http://hgdownload.soe.ucsc.edu/gbdb/hg38/exomeProbesets/S07604624_Covered.bb

# get bigBedtobed
wget -P ${REF_FOLDER}/bin https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/bigBedToBed
chmod +x ${REF_FOLDER}/bin/bigBedToBed
${REF_FOLDER}/bin/bigBedToBed ${REF_FOLDER}/S07604624_Covered.bb ${REF_FOLDER}/S07604624_Covered.bed