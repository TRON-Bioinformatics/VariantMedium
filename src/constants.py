# How often to print loss and calculate perf. on val set.(based on steps)
PRINT_FREQ = 100
VALIDATION_FREQ = 1000

# SNV and small INDEL related constants
NO_LABEL = -1
NO_MUT = 0
GERMLINE = 1
SOMATIC = 2
ALL = 3

CLASSES_DICT = {
    'NO MUTATION': NO_MUT,
    'GERMLINE': GERMLINE,
    'SOMATIC': SOMATIC,
}

# The prediction modes, and different options for each mode.
GERMLINE_MODES = ['germline_snp', 'germline_indel']
SOMATIC_MODES = ['somatic_snv', 'somatic_indel']
SNP_MODES = ['germline_snp', 'somatic_snv']
INDEL_MODES = ['germline_indel', 'somatic_indel']

# the information contained in the input tensor file names.
FILE_NAME_COLUMNS = ['FULL_PATH', 'CHROM', 'POS', 'TYPE', 'LENGTH',
                     'REPLICATE', 'TIMESTAMP']
FILE_NAME_COLUMNS_NO_REP = ['FULL_PATH', 'CHROM', 'POS', 'TYPE', 'LENGTH',
                            'TIMESTAMP']
# The accepted "filter"s for labels.
SOMATIC_LABELS = ['somatic', 'consensus']
GERMLINE_LABELS = ['SNP', 'MNP', 'deepvariant']
GERMLINE_LABELS_LQ = ['deepvariant']
NO_MUT_LABELS = ['no mutation', 'no_mutation']

# The positions of different feature matrices in 3D tensors.
CHANNELS = {
    'ref': [(0, 0)],
    'pos': [(1, 0)],
    'tum': [(-1, 1)],
    'nor': [(-1, 2)],
    'nuc': [(0, 1), (0, 2)],
    'bse': [(1, 1), (1, 2)],
    'map': [(2, 1), (2, 2)],
    'covn': [(3, 1), (3, 2)],
    'nucn': [(4, 1), (4, 2)],
    'covp': [(5, 1), (5, 2)],
    'nucp': [(6, 1), (6, 2)],
    'edit': [(7, 1), (7, 2)],
    'unq': [(8, 1), (8, 2)],
    'nucc': [(9, 1), (9, 2)],
    'covc': [(10, 1), (10, 2)],
}

BEST_MODEL_FNAME = 'best_model.pt'

UNKNOWN_STRATEGIES = ['discard', 'keep_as_false']

DATASETS = ['train', 'valid', 'call']

IND_CHR = 0
IND_POS = 1
IND_REF = 2
IND_ALT = 3
IND_SAMPLE = 4
IND_REPLICATE = 5
IND_CLIPPING = 6
HEADER = ['CHROM', 'POS', 'REF', 'ALT', 'SAMPLE', 'REPLICATE', 'CLIPPING']

SNV_THRESHOLD = 0.01
INS_THRESHOLD = -0.75
DEL_THRESHOLD = -0.67
