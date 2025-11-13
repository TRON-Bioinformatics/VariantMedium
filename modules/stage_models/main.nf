process STAGE_MODELS {
    tag "-"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "community.wave.seqera.io/library/requests:2.32.5--734a8dc164d0c716"

    input:
    path(models_outdir)

    output:
    path("${models_outdir}/3ddensenet_indel.pt")     , emit: ddensenet_indel
    path("${models_outdir}/3ddensenet_snv.pt")       , emit: ddensenet_snv
    path("${models_outdir}/extra_trees.indel.joblib"), emit: extra_trees_indel
    path("${models_outdir}/extra_trees.snv.joblib")  , emit: extra_trees_snv
    path("versions.yml")                             , emit: versions

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
