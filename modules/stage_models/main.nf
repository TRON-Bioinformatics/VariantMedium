process STAGE_MODELS {
    label 'process_low'

    conda "${moduleDir}/environment.yml"

    input:
    val(models_dir)

    output:
    path("${models_dir}/3ddensenet_snv.pt")       , emit: ddensenet_snv
    path("${models_dir}/3ddensenet_indel.pt")     , emit: ddensenet_indel
    path("${models_dir}/extra_trees.snv.joblib")  , emit: extra_trees_snv
    path("${models_dir}/extra_trees.indel.joblib"), emit: extra_trees_indel
    path("versions.yml")                          , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    python ${moduleDir}/templates/stage_models.py \\
        --models_dir "${models_dir}" \\
        --task_process "${task.process}" \\
        --version "${params.version}"
    """

    stub:
    """
    mkdir -p ${models_dir}/
    touch ${models_dir}/3ddensenet_indel.pt
    touch ${models_dir}/3ddensenet_snv.pt
    touch ${models_dir}/extra_trees.indel.joblib
    touch ${models_dir}/extra_trees.snv.joblib

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        stage_models: "${params.version}"
    END_VERSIONS
    """
}
