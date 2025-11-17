import copy
import pandas as pd
import pysam

from filter_candidates.constants import SAVE_COLUMNS, CELL_LINES


def get_all_dfs(
        samples,
        replicates,
        cands_template,
        cands_public_template,
        labels_template,
        features,
        for_indel
):
    all_cands = []
    all_labels = []
    for sample in samples:
        if sample in CELL_LINES:
            for rep in replicates:
                all_cands.append(
                    get_df(
                        (sample, rep),
                        cands_template,
                        features,
                        for_indel=for_indel
                    )
                )
        else:
            tmpl = cands_template
            if sample == 'AML31':
                tmpl = cands_public_template
            all_cands.append(
                get_df(
                    sample,
                    tmpl,
                    features,
                    for_indel=for_indel
                )
            )
        if labels_template:
            all_labels.append(
                parse_df(
                    sample,
                    labels_template.format(sample),
                    for_indel
                )
            )

    cands_df = pd.concat(all_cands)

    if len(all_labels) > 0:
        labels_df = pd.concat(all_labels)
        df = pd.merge(labels_df, cands_df, on='ID', how='right')
    else:
        df = cands_df
        df['FILTER'] = 'unknown'
        df['LABEL'] = 0
    df = df.drop_duplicates().reset_index(drop=True)
    df.loc[df.FILTER.isna(), 'FILTER'] = 'unknown'
    df.LABEL = 0
    df.loc[df.FILTER.isin(['somatic', 'consensus']), 'LABEL'] = 1

    return df


def get_df(sample, tmpl, features, for_indel):
    # read in
    if type(sample) == tuple:
        sample_rep = '_'.join(sample)
        cands_df = parse_df(
            sample[0],
            tmpl.format(sample_rep, sample_rep),
            for_indel
        )
        cands_df['REP'] = sample[1]
    else:
        cands_df = parse_df(
            sample,
            tmpl.format(sample, sample),
            for_indel
        )
        cands_df['REP'] = '1'

    # return df
    cands_df = cands_df.reset_index()
    cols = ['ID']
    if 'REP' in cands_df.columns:
        cols.append('REP')
    cols.extend(features)
    return cands_df[cols]


def parse_df(sample, path, for_indel):
    cands_df = pd.read_csv(path, sep='\t', dtype={'CHROM': str})
    cands_df['ID'] = sample + \
                     '-' + \
                     cands_df.CHROM + \
                     '-' + \
                     cands_df.POS.astype(str) + \
                     '-' + \
                     cands_df.REF + \
                     '-' + \
                     cands_df.ALT

    # fill in NA values (represented by ".")
    for col in cands_df.columns:
        cands_df.loc[cands_df[col] == '.', col] = -100

    # select snvs or indels
    if for_indel:
        cands_df = cands_df[cands_df.REF.str.len() != cands_df.ALT.str.len()]
    else:
        cands_df = cands_df[cands_df.REF.str.len() == cands_df.ALT.str.len()]

    return cands_df.reset_index()


def save_results(df, tmpl, model_name, samples, muttype, w_label):
    tmp = df['ID'].str.split('-', expand=True)
    df['SAMPLE'] = tmp[0]
    df['CHROM'] = tmp[1]
    df['POS'] = tmp[2]
    df['REF'] = tmp[3]
    df['ALT'] = tmp[4]
    save_cols = copy.deepcopy(SAVE_COLUMNS)
    if w_label:
        df = df[save_cols]
    else:
        save_cols.remove('FILTER')
        save_cols.remove('LABEL')
    for sample in samples:
        df_sample = df[df['SAMPLE'] == sample].reset_index(drop=True)
        df_sample = df_sample[df_sample['EXTRATREES_CALL'] == 1]
        if model_name:
            df_sample.to_csv(
                tmpl.format(model_name, sample, muttype),
                sep='\t',
                index=False
            )
        else:
            df_sample.to_csv(
                tmpl.format(sample, muttype),
                sep='\t',
                index=False
            )


# Define a function that mimics bcftools query -f and writes output to a TSV file
def query_vcf_to_tsv(vcf_file, tsv_file):
    query_format = '%CHROM\t%POS\t%REF\t%ALT\t%FILTER\t%primary_af\t%primary_dp\t%primary_ac\t%primary_pu\t%primary_pw\t%primary_k\t%primary_rsmq\t%primary_rsmq_pv\t%primary_rsbq\t%primary_rsbq_pv\t%primary_rspos\t%primary_rspos_pv\t%normal_af\t%normal_dp\t%normal_ac\t%normal_pu\t%normal_pw\t%normal_k\t%normal_rsmq\t%normal_rsmq_pv\t%normal_rsbq\t%normal_rsbq_pv\t%normal_rspos\t%normal_rspos_pv\n'

    # Open the VCF file
    vcf = pysam.VariantFile(vcf_file, "r")

    # Open the output file for writing (TSV format)
    with open(tsv_file, "w") as f:
        # Write header to the TSV file based on the query format
        header = query_format.replace("%", "").replace("\t", "\t").strip()
        f.write(header + "\n")

        # Go through each record in the VCF
        for record in vcf.fetch():
            # Prepare the output string based on the provided format
            output = query_format

            # Replace placeholders in the query_format string with the relevant fields from the VCF record
            output = output.replace("%CHROM", record.chrom)
            output = output.replace("%POS", str(record.pos))
            output = output.replace("%REF", record.ref)
            output = output.replace("%ALT", ",".join(
                str(alt) for alt in record.alts))
            output = output.replace("%FILTER", ",".join(record.filter.keys()))

            # Custom handling for INFO fields (e.g., AC, AF)
            fields = query_format.replace(
                '%CHROM\t%POS\t%REF\t%ALT\t%FILTER\t', ''
            )
            fields = fields.replace('\n', '')
            fields = fields.split('\t')
            for key in fields:
                val = record.info.get(key.replace('%', ''), ['.'])
                try:
                    val = val[0]
                except:
                    pass
                try:
                    val = round(val, 5)
                except:
                    pass

                if key == "%normal_rspos_pv":  # hard coding..
                    output = output.replace(
                        '\t{}\n'.format(key), '\t{}\n'.format(val)
                    )
                else:
                    output = output.replace(
                        '\t{}\t'.format(key), '\t{}\t'.format(val)
                    )

            # Write the formatted record to the TSV file
            f.write(output)
