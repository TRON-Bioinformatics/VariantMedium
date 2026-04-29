// -------------------------------------------------------
// Samplesheet validation
// -------------------------------------------------------
def validateSamplesheet(samplesheet_ch) {
    samplesheet_ch.map { path ->
        def sep = path.name.endsWith('.tsv') ? '\t' : ','

        def lines = path.text.readLines()
        if (!lines) error "Samplesheet is empty: ${path}"

        def header = lines[0].split(sep).collect { colname -> colname.trim() }
        def required = ['sample_name','pair_identifier','tumor_bam','normal_bam']
        def missing = required.findAll { colname -> colname !in header }
        if (missing) {
            error "Samplesheet is missing required columns: ${missing.join(', ')}"
        }

        // Optional: check BAM files exist
        lines.tail().eachWithIndex { line, idx ->
            def vals = line.split(sep).collect { val -> val.trim() }
            if (vals.size() < 4) error "Line ${idx + 2} is malformed: ${line}"

            def tumor = file(vals[2])
            def normal = file(vals[3])

            if (!tumor.exists()) error "Tumor BAM missing: ${tumor}"
            if (!normal.exists()) error "Normal BAM missing: ${normal}"
        }

        return [path, sep]  // pass separator for downstream use
    }
}


workflow PARSE_SAMPLESHEET {

    take:
    ch_samplesheet  // channel ["path-to-samplesheet"]

    main:
    
    validateSamplesheet(ch_samplesheet)
    log.info "[INFO] Samplesheet validated"

    def sep = params.samplesheet.endsWith('.tsv') ? '\t' : ','
    ch_samplesheet
        .splitCsv(header: true, sep: sep)
        .map { row ->

    // Validate samplesheet
    def validated_ch = validateSamplesheet(ch_samplesheet)
    log.info "[INFO] Samplesheet validated"

    // Split samplesheet into sample info
    validated_ch
        .map { path, sep ->
            path.text.readLines().tail().collect { line ->
                def vals = line.split(sep).collect { val -> val.trim() }

                tuple(
                    vals[0],                     // sample_name
                    vals[1],                     // pair_identifier
                    file(vals[2]),               // tumor_bam
                    file(vals[3])                // normal_bam
                )
            }
        }
        .flatten()
        .set { sample_info_ch }

    
    emit:

    emit:
    ch_samples = sample_info_ch

}
