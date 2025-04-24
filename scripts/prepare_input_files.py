#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import pandas as pd


def make_input(inpath, folder, out_folder_vm, skip_preprocessing):
    prepath = os.path.join(folder, 'preproc.tsv')
    bampath = os.path.join(folder, 'bams.tsv')
    vcfpath = os.path.join(folder, 'vcfs.tsv')
    paipath = os.path.join(folder, 'pairs_wo_reps.tsv')
    b2tpath = os.path.join(folder, 'pairs_w_cands.tsv')
    etrpath = os.path.join(folder, 'samples_w_cands.tsv')

    df = pd.read_csv(inpath, sep='\t', header=None)

    prefile = open(prepath, 'w+')
    bamfile = open(bampath, 'w+')
    vcffile = open(vcfpath, 'w+')
    paifile = open(paipath, 'w+')
    b2tfile = open(b2tpath, 'w+')
    etrfile = open(etrpath, 'w+')

    for r in df.iterrows():
        # print(r)
        # TODO: handle replicates
        sample = r[1][0]
        reppair = r[1][1]
        tumor = r[1][2]
        normal = r[1][3]
        sample_rep = '{}_{}'.format(sample, reppair)
        if skip_preprocessing != "True":
            print(
                '{}_tumor\ttumor\t{}'.format(sample_rep, tumor), file=prefile
            )
            print(
                '{}_normal\tnormal\t{}'.format(sample_rep, normal), file=prefile
            )

            tumor = os.path.join(
                out_folder_vm,
                'output_01_01_preprocessed_bams',
                '{}_tumor'.format(sample_rep),
                '{}_tumor.preprocessed.bam'.format(sample_rep)
            )
            normal = os.path.join(
                out_folder_vm,
                'output_01_01_preprocessed_bams',
                '{}_normal'.format(sample_rep),
                '{}_normal.preprocessed.bam'.format(sample_rep)
            )

        print('{}\tprimary:{}'.format(sample_rep, tumor), file=bamfile)
        print('{}\tnormal:{}'.format(sample_rep, normal), file=bamfile)

        print('{}_{}\t{}'.format(
            sample,
            reppair,
            os.path.join(
                out_folder_vm,
                'output_01_02_candidates_strelka2',
                '{}'.format(sample_rep),
                '{}.strelka2.somatic.vcf.gz'.format(sample_rep)
            )
        ), file=vcffile)

        print(
            '{}_{}'.format(sample, reppair),
            tumor,
            normal,
            file=paifile,
            sep='\t'
        )

        print(
            sample,
            'call',
            reppair,
            os.path.join(
                out_folder_vm, 'output_01_03_vcf_postprocessing', sample_rep,
                '{}.vaf.vcf'.format(sample_rep)
            ),
            file=etrfile,
            sep='\t'
        )

        print(
            sample,
            'call',
            reppair,
            tumor,
            tumor[:-3] + 'bai',
            normal,
            normal[:-3] + 'bai',
            os.path.join(
                out_folder_vm,
                'output_01_04_candidates_extratrees',
                'Production_Model',
                '{}.tsv'.format(sample)
            ),
            file=b2tfile,
            sep='\t'
        )

    prefile.close()
    bamfile.close()
    vcffile.close()
    paifile.close()
    etrfile.close()
    b2tfile.close()


def validate_paths(inpath, folder, out_folder_vm):
    if not os.path.exists(inpath):
        raise FileNotFoundError(
            'The input file was not found in specified location: {}'.format(
                inpath
            )
        )
    if not os.path.exists(folder):
        raise FileNotFoundError(
            'The output folder for TSVs was not found in specified location: {}'.format(
                folder
            )
        )
    if not os.path.exists(out_folder_vm):
        raise FileNotFoundError(
            'The output folder for the pipeline was not found in specified location: {}'.format(
                out_folder_vm
            )
        )

    df = pd.read_csv(inpath, sep='\t', header=None)
    for r in df.iterrows():
        tumor = r[1][2]
        normal = r[1][3]
        if not os.path.exists(tumor):
            raise FileNotFoundError(
                'The tumor BAM was not found in specified location: {}'.format(
                    tumor
                )
            )
        if not os.path.exists(normal):
            raise FileNotFoundError(
                'The normal BAM was not found in specified location: {}'.format(
                    normal
                )
            )
        if not os.path.exists(tumor[:-3] + 'bai'):
            raise FileNotFoundError(
                'The tumor BAM index was not found in specified location: {}'.format(
                    tumor[:-3] + 'bai'
                )
            )
        ,
        if not os.path.exists(normal[:-3] + 'bai'):
            raise FileNotFoundError(
                'The normal BAM index was not found in specified location: {}'.format(
                    normal[:-3] + 'bai'
                )
            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Prepares necessary input files')
    parser.add_argument('-i', '--input_file', type=str)
    parser.add_argument('-o', '--out_folder', type=str)
    parser.add_argument('-O', '--out_folder_vm', type=str)
    parser.add_argument('-s', '--skip_preprocessing', type=str)

    args = parser.parse_args()
    validate_paths(args.input_file, args.out_folder, args.out_folder_vm)
    make_input(args.input_file, args.out_folder, args.out_folder_vm, args.skip_preprocessing)
