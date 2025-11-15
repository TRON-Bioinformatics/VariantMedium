process FILTER_CANDIDATES {
    tag "${sample_name}"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/a7/a73b7de4a8d00029f69b6cef20b74e1a1d6b48c1d7d5a65b5e55cf09c3fe6ce7/data"

    input:
    tuple val(sample_name), path(input_files), path(output), val(model)

    output:
    tuple val(sample_name), path("${sample_name}/*.tsv"), emit: filtered_candidates
    path ("versions.yml")                               , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    
    """
    filter_candidates.py \
        -i ${input_files} \
        -o ${output} \
        -m ${model}/Production_Model.joblib \
        ${args}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        variantmedium: 1.1.0
    END_VERSIONS
    """

    stub:
    """
    mkdir -p ${sample_name}/
    touch "${sample_name}/fake_file.tsv"

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        variantmedium: 1.1.0
    END_VERSIONS
    """
}
