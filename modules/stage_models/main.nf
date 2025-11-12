process STAGE_MODELS {
    tag "-"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "community.wave.seqera.io/library/pandas:2.3.3--5a902bf824a79745c"

    input:
    path(models_outdir)

    output:
    path("${models_outdir}/"), emit: models
    path("versions.yml"     ), emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def model_dir = "${models_outdir}" ? "${models_outdir}" : "models"

    """
    stage_models.py ${model_dir}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        stage_models: 1.0.0
    END_VERSIONS
    """

    stub:
    """
    mkdir -p models/

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        stage_models: 1.0.0
    END_VERSIONS
    """
}
