process FILTER_CANDIDATES {
    tag "-"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/a7/a73b7de4a8d00029f69b6cef20b74e1a1d6b48c1d7d5a65b5e55cf09c3fe6ce7/data"

    input:
    path(input_tsv)
    path(model)
    val(output_dir)

    output:
    path("${output_dir}/*.tsv"), emit: filtered_candidates
    path ("versions.yml")      , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    
    """
    filter_candidates.py \
        -i ${input_tsv} \
        -o ${output_dir} \
        -m ${model} \
        ${args}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        variantmedium: 1.1.0
    END_VERSIONS
    """

    stub:
    """
    mkdir -p ${output_dir}/
    touch "${output_dir}/fake_file.tsv"

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        variantmedium: 1.1.0
    END_VERSIONS
    """
}
