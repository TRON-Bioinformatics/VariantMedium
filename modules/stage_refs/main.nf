process STAGE_REFERENCES {
    tag "-"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "community.wave.seqera.io/library/pandas:2.3.3--5a902bf824a79745c"

    input:
    path(ref_outdir)

    output:
    path("${ref_outdir}/"), emit: models
    path("versions.yml")  , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def ref_dir = "${ref_outdir}" ? "${ref_outdir}" : "ref"

    """
    stage_refs.py ${ref_dir}

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
