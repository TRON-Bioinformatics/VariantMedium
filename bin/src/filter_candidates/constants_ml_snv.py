from filter_candidates.constants import PCAWG

SETS_SNV = {
    'COLO_829_Model': {
        'train': ['HCC_1187', 'HCC_1937', 'HCC_1954', 'MZ_2_Mel_43',
                  'MZ_7_Mel_1', 'NCI_H_1770', 'NCI_H_2171', 'SK_MEL_29'],
        'valid': ['MZ_PC_1'],
        'test': ['COLO_829']
    },
    'MZ_PC_1_Model': {
        'train': ['HCC_1187', 'HCC_1937', 'HCC_1954', 'MZ_2_Mel_43',
                  'MZ_7_Mel_1', 'NCI_H_1770', 'NCI_H_2171', 'SK_MEL_29'],
        'valid': ['COLO_829'],
        'test': ['MZ_PC_1']
    },
    'MZ_PC_2_Model': {
        'train': ['MZ_PC_1', 'HCC_1187', 'HCC_1937', 'HCC_1954', 'MZ_2_Mel_43',
                  'MZ_7_Mel_1', 'NCI_H_1770', 'NCI_H_2171', 'SK_MEL_29'],
        'valid': ['COLO_829'],
        'test': ['MZ_PC_2']
    },
    'Production_Model': {
        'train': ['AML31', 'COLO_829', 'HCC_1187', 'HCC_1937',
                  'HCC_1954', 'MZ_2_Mel_43', 'MZ_7_Mel_1', 'NCI_H_1770',
                  'NCI_H_2171', 'SK_MEL_29'],
        'valid': ['MZ_PC_1'],
        'test': PCAWG
    }
}

THRESHOLDS_SNV = {
    'COLO_829_Model': 0.014,
    'MZ_PC_1_Model': 0.037,
    'MZ_PC_2_Model': 0.034,
    'Production_Model': 0.027,
}

FEATURES_SNV = [
    'primary_af', 'primary_dp', 'primary_ac', 'primary_pu', 'primary_pw',
    'primary_k', 'primary_rsmq', 'primary_rsmq_pv', 'primary_rsbq',
    'primary_rsbq_pv', 'primary_rspos', 'primary_rspos_pv', 'normal_af',
    'normal_dp', 'normal_ac', 'normal_pu', 'normal_pw', 'normal_k',
    'normal_rsmq', 'normal_rsmq_pv', 'normal_rsbq', 'normal_rsbq_pv',
    'normal_rspos', 'normal_rspos_pv'
]
LABEL = 'LABEL'

TUNED_PARAMS_SNV = [
    {
        'n_estimators': [500, 600],
        'max_depth': [20, 25],
        'criterion': ['entropy'],
        'max_features': ['sqrt', 'log2'],
        'bootstrap': [True, False]
    },
    {
        'n_estimators': [700, 800],
        'max_depth': [30, 35],
        'criterion': ['entropy'],
        'max_features': ['sqrt', 'log2'],
        'bootstrap': [True, False]
    }
]
