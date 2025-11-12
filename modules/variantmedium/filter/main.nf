process VARIANTMEDIUM_FILTER_CANDIDATES {
    tag "${sample_name}"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "community.wave.seqera.io/library/numpy_pandas_scikit-learn_scipy_pruned:9cd8ec05ff7a5fac"

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
