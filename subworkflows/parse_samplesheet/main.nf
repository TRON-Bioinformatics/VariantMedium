// -------------------------------------------------------
// Samplesheet validation
// -------------------------------------------------------
def validateSamplesheet(samplesheet_ch) {
    samplesheet_ch.map { path ->
        def header = path.text.readLines()[0]
        def cols = header.split(/,|\t/)  // handle CSV or TSV

        def required = ['sample_name','pair_identifier','tumor_bam','normal_bam']
        def missing = required.findAll { it !in cols }
        if (missing) {
            error "Samplesheet is missing required columns: ${missing.join(', ')}"
        }

        // Optional: check BAM files exist
        path.text.readLines().tail().each { line ->
            def vals = line.split(/,|\t/)
            def tumor = file(vals[2])
            def normal = file(vals[3])

            if (!tumor.exists()) error "Tumor BAM missing: $tumor"
            if (!normal.exists()) error "Normal BAM missing: $normal"
        }
    }
}
    

workflow PARSE_SAMPLESHEET {

    take:
    ch_samplesheet // channel ["path-to-samplesheet"]

    main:
    
    validateSamplesheet(ch_samplesheet)
    log.info "[INFO] Samplesheet validated"

    def sep = ch_samplesheet_file.name.endsWith('.tsv') ? '\t' : ','
    ch_samplesheet
        .splitCsv(header: true, sep: sep)
        .map { row ->

            def tumorPath = row.tumor_bam.trim()
            def normalPath = row.normal_bam.trim()

            // get file object
            def tumorFile = file(tumorPath)
            def normalFile = file(normalPath)

            tuple(row.sample_name, row.pair_identifier, tumorFile, normalFile)
        }
        .set { sample_info_ch }

    
    emit:

    ch_samples = sample_info_ch

}
