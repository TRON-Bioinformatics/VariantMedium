CELL_LINES = ['COLO_829', 'MZ_PC_1', 'MZ_PC_2', 'HCC_1187', 'HCC_1937',
              'HCC_1954', 'MZ_2_Mel_43', 'MZ_7_Mel_1', 'NCI_H_1770',
              'NCI_H_2171', 'SK_MEL_29']
CELL_LINES_W_DEEPSEQ = ['COLO_829', 'MZ_PC_1', 'MZ_PC_2', 'HCC_1937',
                        'HCC_1954']
CELL_LINES_WO_DEEPSEQ = ['HCC_1187', 'MZ_2_Mel_43', 'MZ_7_Mel_1', 'NCI_H_1770',
                         'NCI_H_2171', 'SK_MEL_29']
REPS = ['11', '12', '21', '22']
REPLICATES_REST = ['1']
REPLICATES = {'CL': REPS, 'REST': REPLICATES_REST}

PCAWG = ['DO10900', 'DO11441', 'DO15110', 'DO15870', 'DO15911', 'DO18988',
         'DO19048', 'DO220172', 'DO22117', 'DO23651', 'DO26769', 'DO26971',
         'DO2783', 'DO29850', 'DO32237', 'DO3482', 'DO36356', 'DO36945',
         'DO37474', 'DO37758', 'DO38847', 'DO38871', 'DO40167', 'DO42240',
         'DO43506', 'DO44285', 'DO44469', 'DO4557', 'DO479', 'DO48977',
         'DO49659', 'DO51600', 'DO52171', 'DO52172', 'DO555', 'DO7822',
         'DO804', 'DO8264']


ESSENTIAL_COLUMNS = ['ID', 'FILTER', 'LABEL', 'primary_af', 'primary_dp',
                     'primary_ac', 'normal_af', 'normal_dp', 'normal_ac']
SAVE_COLUMNS = ['SAMPLE', 'CHROM', 'POS', 'REF', 'ALT', 'REP',
                'EXTRATREES_SCORE',
                'EXTRATREES_CALL', 'FILTER', 'LABEL', 'primary_af',
                'primary_dp', 'primary_ac', 'normal_af', 'normal_dp',
                'normal_ac']
