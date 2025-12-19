process STAGE_REFERENCES {
    label 'process_single'

    conda "${moduleDir}/environment.yml"
    container "https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/b7/b77f6190e0770242d259d2982968ec82d3fb244d1e7f207c13bcf85d44b468e1/data"

    input:
    val(bed_url)
    val(ref_outdir)

    output:
    path("${ref_outdir}/*.{vcf.gz,dict,fa,fai,bb,bed.gz,bed.gz.tbi}"), emit: references
    path("versions.yml")  , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    template("stage_refs.py")

    stub:
    """
    mkdir -p ${ref_outdir}
    touch ${ref_outdir}/dummy_ref_file.vcf.gz
    touch ${ref_outdir}/dummy_ref_file.dict
    touch ${ref_outdir}/dummy_ref_file.fa
    touch ${ref_outdir}/dummy_ref_file.fa.fai
    touch ${ref_outdir}/dummy_ref_file.fa.bb
    touch ${ref_outdir}/dummy_ref_file.bed.gz
    touch ${ref_outdir}/dummy_ref_file.bed.gz.tbi

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        stage_refs: "${params.version}"
    END_VERSIONS
    """
}
