process STAGE_REFERENCES {
    tag "-"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/b7/b77f6190e0770242d259d2982968ec82d3fb244d1e7f207c13bcf85d44b468e1/data"

    input:
    val(ref_outdir)

    output:
    path("${ref_outdir}/ALL.wgs.1000G_phase3.GRCh38.ncbi_remapper.20150424.shapeit2_indels.vcf.gz"), emit: grch38_vcf_gz
    path("${ref_outdir}/dbsnp_146.hg38.vcf.gz"), emit: dbsnp_vcf_gz
    path("${ref_outdir}/GRCh38.d1.vd1_GATK_indices.tar.gz"), emit: grch38_gatk_indices
    path("${ref_outdir}/GRCh38.d1.vd1.dict"), emit: grch38_dict
    path("${ref_outdir}/GRCh38.d1.vd1.fa"), emit: grch38_fa
    path("${ref_outdir}/GRCh38.d1.vd1.fa.fai"), emit: grch38_fai
    path("${ref_outdir}/GRCh38.d1.vd1.fa.tar.gz"), emit: grch38_fa_targz
    path("${ref_outdir}/S07604624_Covered.bb"), emit: covered_bb_S07604624
    path("${ref_outdir}/S07604624_Covered.bed"), emit: covered_bed_S07604624
    path("versions.yml")  , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    stage_refs.py

    mkdir -p ${ref_outdir}/
    mv *.{gz,dict,fa,fai,bb,bed} ${ref_outdir}/

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        stage_refs: 1.0.0
    END_VERSIONS
    """

    stub:
    """
    mkdir -p ${ref_outdir}/
    touch ${ref_outdir}/fake_file.txt

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        stage_refs: 1.0.0
    END_VERSIONS
    """
}
