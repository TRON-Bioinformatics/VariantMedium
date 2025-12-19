process FILTER_CANDIDATES {
    label "process_high"

    conda "${moduleDir}/environment.yml"
    container "https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/a7/a73b7de4a8d00029f69b6cef20b74e1a1d6b48c1d7d5a65b5e55cf09c3fe6ce7/data"

    input:
    path(input_tsv)
    path(model)
    val(calling_type)
    val(output_dir)

    output:
    path("filtered_candidates/*.tsv"), emit: filtered_candidates
    path("versions.yml")             , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def call_type = "${calling_type}" == 'snv' ? '--snv' : '--indel'
    
    """
    mkdir -p filtered_candidates/
    
    filter_candidates.py \\
        -i "${input_tsv}" \\
        -o "${output_dir}" \\
        -m "${model}" \\
        "${call_type}" \\
        ${args}

    mv *.tsv filtered_candidates/

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        variantmedium: "${params.version}"
    END_VERSIONS
    """

    stub:
    """
    mkdir -p filtered_candidates/
    touch "filtered_candidates/sample.tsv"

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        variantmedium: "${params.version}"
    END_VERSIONS
    """
}
