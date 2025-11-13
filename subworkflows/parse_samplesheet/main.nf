workflow PARSE_SAMPLESHEET {

    take:
    ch_samplesheet // channel ["path-to-samplesheet"]

    main:

    // ch_samplesheet.view()
    ch_samplesheet
        .splitCsv(header: true)
        .map { row ->
            // Trim paths to remove extra spaces
            def tumorPath = row.tumor_bam_path.trim()
            def normalPath = row.normal_bam_path.trim()

            // Convert to file object
            def tumorFile = file(tumorPath)
            def normalFile = file(normalPath)

            // Debug check
            if( !tumorFile.exists() ) { error "Tumor BAM does not exist: $tumorPath" }
            if( !normalFile.exists() ) { error "Normal BAM does not exist: $normalPath" }

            tuple(row.sample_name, row.replicate_pair_identifier, tumorFile, normalFile)
        }
        .set { sample_info_ch }

    // Example: print out the parsed data
    // sample_info_ch.view {
    //     sample_name, pair_id, tumor_bam, normal_bam ->
    //     "Sample: ${sample_name}, Pair: ${pair_id}  Tumor: ${tumor_bam}  Normal: ${normal_bam}"
    // }
    
    emit:
    ch_samples = sample_info_ch

}