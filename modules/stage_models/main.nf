process STAGE_MODELS {
    tag "-"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/b7/b77f6190e0770242d259d2982968ec82d3fb244d1e7f207c13bcf85d44b468e1/data"

    input:
    val(models_dir)

    output:
    path("${models_dir}/3ddensenet_indel.pt")     , emit: ddensenet_indel
    path("${models_dir}/3ddensenet_snv.pt")       , emit: ddensenet_snv
    path("${models_dir}/extra_trees.indel.joblib"), emit: extra_trees_indel
    path("${models_dir}/extra_trees.snv.joblib")  , emit: extra_trees_snv
    path("versions.yml")                          , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:

    """
    stage_models.py
    
    mkdir "${models_dir}/"
    mv *.{pt,joblib} "${models_dir}/"

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
