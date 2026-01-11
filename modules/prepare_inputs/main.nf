process PREPARE_INPUTS {
    label 'process_low'

    conda "${moduleDir}/environment.yml"
    container "https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/e8/e87c143b4e7b31e1d5db5518d5c3d0e82fe20c4a9607e668e3fc8b390257d4f7/data"

    input:
    path(input_file)
    val(output_path)
    val(skip_preprocessing)

    output:
    path("tsv_folder/*.tsv"), emit: tsv_folder
    path("versions.yml")    , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    
    """
    mkdir -p tsv_folder/
    
    prepare_input_files.py \
        -i "${input_file}" \
        -o "${output_path}" \
        -s "${skip_preprocessing}" \
        ${args}

    mv *.tsv tsv_folder/

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        prepare_input_files: ${params.version}
    END_VERSIONS
    """

    stub:
    """
    mkdir -p tsv_folder
    touch tsv_folder/preproc.tsv
    touch tsv_folder/bams.tsv
    touch tsv_folder/vcfs.tsv
    touch tsv_folder/pairs_wo_reps.tsv
    touch tsv_folder/pairs_w_cands.tsv
    touch tsv_folder/samples_w_cands.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        prepare_input_files: "${params.version}"
    END_VERSIONS
    """
}