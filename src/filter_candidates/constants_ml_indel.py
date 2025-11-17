from filter_candidates.constants_ml_snv import SETS_SNV

SETS_INDEL = {
    'COLO_829_Model': SETS_SNV['COLO_829_Model'],
    'MZ_PC_1_Model': SETS_SNV['MZ_PC_1_Model'],
    'MZ_PC_2_Model': SETS_SNV['MZ_PC_2_Model'],
    'Production_Model': {
        'train': ['COLO_829', 'HCC_1187', 'HCC_1937', 'HCC_1954',
                  'MZ_2_Mel_43', 'MZ_7_Mel_1', 'NCI_H_1770', 'NCI_H_2171',
                  'SK_MEL_29'],
        'valid': SETS_SNV['Production_Model']['valid'],
        'test': SETS_SNV['Production_Model']['test']
    }
}

THRESHOLDS_INDEL = {
    'COLO_829_Model': 0.016,
    'MZ_PC_1_Model': 0.013,
    'MZ_PC_2_Model': 0.013,
    'Production_Model': 0.014,
}

FEATURES_INDEL = [
    'primary_af', 'primary_dp', 'primary_ac', 'primary_pu', 'primary_pw',
    'primary_k', 'primary_rsmq', 'primary_rsmq_pv', 'primary_rspos',
    'primary_rspos_pv', 'normal_af', 'normal_dp', 'normal_ac', 'normal_pu',
    'normal_pw', 'normal_k', 'normal_rsmq', 'normal_rsmq_pv', 'normal_rspos',
    'normal_rspos_pv'
]
LABEL = ['LABEL']

TUNED_PARAMS_INDEL = [
    {
        'n_estimators': [100, 200],
        'max_depth': [5, 10],
        'criterion': ['entropy'],
        'max_features': ['sqrt', 'log2'],
        'bootstrap': [True, False]
    },
    {
        'n_estimators': [300, 400],
        'max_depth': [10, 15],
        'criterion': ['entropy'],
        'max_features': ['sqrt', 'log2'],
        'bootstrap': [True, False]
    },
    # {
    #     'n_estimators': [300],
    #     'max_depth': [15],
    #     'criterion': ['entropy'],
    #     'max_features': ['sqrt'],
    #     'bootstrap': [False]
    # },
]
