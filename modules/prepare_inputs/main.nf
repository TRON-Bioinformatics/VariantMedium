process PREPARE_INPUTS {
    tag "${sample_name}"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "community.wave.seqera.io/library/pandas:2.3.3--5a902bf824a79745c"

    input:
    tuple val(sample_name), path(input_file), path(out_folder), path(out_folder_vm), val(skip_preprocessing)

    output:
    path("preproc.tsv")        , emit: preproc_tsv
    path("bams.tsv")           , emit: bam_tsv
    path("vcfs.tsv")           , emit: vcfs_tsv
    path("pairs_wo_reps.tsv")  , emit: pairs_wo_reps_tsv
    path("pairs_w_cands.tsv")  , emit: pairs_w_cands_tsv
    path("samples_w_cands.tsv"), emit: samples_w_cands_tsv
    path("versions.yml")       , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    
    """
    prepare_input_files.py \
        -i ${input_file} \
        -o ${out_folder} \
        -O ${out_folder_vm} \
        -s ${skip_preprocessing} \
        ${args}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        prepare_input_files: 1.1.0
    END_VERSIONS
    """

    stub:
    """
    touch preproc.tsv
    touch bams.tsv
    touch vcfs.tsv
    touch pairs_wo_reps.tsv
    touch pairs_w_cands.tsv
    touch samples_w_cands.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        prepare_input_files: 1.1.0
    END_VERSIONS
    """
}
