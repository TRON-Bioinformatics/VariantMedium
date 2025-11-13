process CALL_VARIANTS {
    tag "${sample_name}"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "community.wave.seqera.io/library/numpy_pandas_scikit-learn_scipy_pruned:9cd8ec05ff7a5fac"

    input:
    tuple val(sample_name), path(out_path), path(home_folder), path(pretrained_model), val(prediction_mode), val(strategy_call)

    output:
    path ("${sample_name}/${out_path}/"), emit: call_outs
    path ("versions.yml")               , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def predict_mode = "${prediction_mode}" ? "--prediction_mode ${prediction_mode}": "--prediction_mode somatic_snv"
    
    """
    run_variant_medium.py run \\
        --home_folder ${home_folder} \\
        --unknown_strategy_call keep_as_false \\
        --pretrained_model ${pretrained_model} \\
        ${predict_mode} \\
        --out_path ${out_path} \\
        --learning_rate ${params.learning_rate} \\
        --epoch ${params.epoch} \\
        --drop_rate ${params.drop_rate} \\
        --aug_rate ${params.aug_rate} \\
        --aug_mixes ${params.aug_mixes} \\
        --run call \\
        ${args}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        variantmedium: 1.1.0
    END_VERSIONS
    """

    stub:
    """
    mkdir -p ${out_path}/
    touch "${out_path}/fake_file.txt"

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        variantmedium: 1.1.0
    END_VERSIONS
    """
}
