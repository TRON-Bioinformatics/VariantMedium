process CALL_VARIANTS {
    tag "-"
    label 'process_high'

    conda "${moduleDir}/environment.yml"
    container "https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/a7/a73b7de4a8d00029f69b6cef20b74e1a1d6b48c1d7d5a65b5e55cf09c3fe6ce7/data"

    input:
    path(home_folder)
    path(pretrained_model)
    val(prediction_mode)
    val(out_path)

    output:
    path ("${out_path}/"), emit: call_outs
    path ("versions.yml"), emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''

    """
    run_variant_medium.py run \\
        --home_folder ${home_folder} \\
        --unknown_strategy_call keep_as_false \\
        --pretrained_model ${pretrained_model} \\
        --prediction_mode ${prediction_mode} \\
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
