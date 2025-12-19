process CALL_VARIANTS {
    label "process_high_memory"

    conda "${moduleDir}/environment.yml"
    container "https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/a7/a73b7de4a8d00029f69b6cef20b74e1a1d6b48c1d7d5a65b5e55cf09c3fe6ce7/data"

    input:
    path(home_folder)
    path(pretrained_model)
    val(prediction_mode)

    output:
    path("*.{somatic,germline}_{snv,indel}.VariantMedium.{tsv,vcf}"), emit: call_outs
    path("scores_{somatic,germline}_{snv,indel}.tsv")               , emit: score_outs
    path("all_scores_{somatic,germline}_{snv,indel}.tsv")           , emit: all_score_outs
    path("versions.yml")                                            , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''

    """
    run_variant_medium.py call \\
        --home_folder "${home_folder}" \\
        --unknown_strategy_call keep_as_false \\
        --pretrained_model "${pretrained_model}" \\
        --prediction_mode "${prediction_mode}" \\
        --learning_rate "${params.learning_rate}" \\
        --epoch "${params.epoch}" \\
        --drop_rate "${params.drop_rate}" \\
        --aug_rate 5 \\
        --aug_mixes nan \\
        --run call \\
        ${args}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        variantmedium: "${params.version}"
    END_VERSIONS
    """

    stub:
    """
    touch sample.somatic_snv.VariantMedium.tsv
    touch sample.germline_snv.VariantMedium.tsv
    touch sample.somatic_indel.VariantMedium.tsv
    touch sample.germline_indel.VariantMedium.tsv
    touch sample.scores_somatic_snv.tsv
    touch sample.scores_germline_snv.tsv
    touch sample.scores_somatic_indel.tsv
    touch sample.scores_germline_indel.tsv
    touch sample.all_scores_somatic_snv.tsv
    touch sample.all_scores_germline_snv.tsv
    touch sample.all_scores_somatic_indel.tsv
    touch sample.all_scores_germline_indel.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        variantmedium: "${params.version}"
    END_VERSIONS
    """
}
