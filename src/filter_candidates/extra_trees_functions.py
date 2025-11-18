import copy
import pandas as pd

from sklearn import metrics
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV

from filter_candidates.constants import ESSENTIAL_COLUMNS
from filter_candidates.extra_trees_io import get_all_dfs

pd.options.mode.chained_assignment = None


def read_and_fit(
        train_samples,
        replicates,
        cands_template,
        cands_public_template,
        labels_template,
        features,
        label,
        tuned_params,
        for_indel
):
    # read in the data
    train_df = get_all_dfs(
        train_samples,
        replicates,
        cands_template,
        cands_public_template,
        labels_template,
        features,
        for_indel
    )
    print('Number of training candidates: ', len(train_df))

    # find best hyperparams and fit the model
    X = train_df[features].astype(float).values
    y = train_df[label].astype(bool).values.ravel()

    clf = fit_model(X, y, tuned_params)

    # print feature importances
    print('Feature importances: ')
    for k, v in zip(features, clf.best_estimator_.feature_importances_):
        print('{:12}: {:.3}'.format(k, v))
    print()

    return clf, train_df


def fit_model(X, y, tuned_params):
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.4,
        random_state=0
    )

    clf = GridSearchCV(
        ExtraTreesClassifier(random_state=4832),
        tuned_params,
        scoring='recall',
        n_jobs=-1,
        verbose=1
    )
    clf.fit(X_train, y_train)

    print("Best parameters set found on development set:")
    print(clf.best_params_)
    print()
    print("Detailed classification report:")
    print()
    y_true, y_pred = y_test, clf.predict(X_test)
    print(classification_report(y_true, y_pred))
    print()

    return clf


def apply_threshold(clf, df, threshold, features, label):
    X = df[features].values
    if label:
        labels = df[label].values.ravel()
    scores = clf.predict_proba(X)
    preds = clf.predict(X)

    essential_cols = copy.deepcopy(ESSENTIAL_COLUMNS)
    if not label:
        essential_cols.remove('FILTER')
        essential_cols.remove('LABEL')
    if 'REP' in df.columns:
        df = df[essential_cols + ['REP']]
    else:
        df = df[essential_cols]


    df['EXTRATREES_PRED'] = preds
    if label:
        df['EXTRATREES_LABEL'] = labels
    df['EXTRATREES_SCORE'] = scores[:, 1]
    df['EXTRATREES_CALL'] = 0
    df.loc[df['EXTRATREES_SCORE'] > threshold, 'EXTRATREES_CALL'] = 1
    df = df.drop_duplicates().reset_index(drop=True)
    return df


def compute_metrics(df, th):
    print(
        '{:7.4} {:7} {:7} {:6} {:6} {:6} {:5.3} {:5.3} {:5.3} {:8.6}'.format(
            th / 1000,
            len(df),
            len(df[df['EXTRATREES_CALL'] == 1]),
            len(df[df['EXTRATREES_LABEL'] == 1]),
            len(
                df[(df['EXTRATREES_CALL'] == 1)
                   & (df['EXTRATREES_LABEL'] == 1)]
            ),
            len(
                df[(df['EXTRATREES_CALL'] == 0)
                   & (df['EXTRATREES_LABEL'] == 1)]
            ),
            metrics.precision_score(
                df['EXTRATREES_LABEL'], df['EXTRATREES_CALL']
            ),
            metrics.recall_score(
                df['EXTRATREES_LABEL'], df['EXTRATREES_CALL']
            ),
            metrics.f1_score(
                df['EXTRATREES_LABEL'], df['EXTRATREES_CALL']
            ),
            metrics.fbeta_score(
                df['EXTRATREES_LABEL'], df['EXTRATREES_CALL'], beta=5
            )
        )
    )
    return metrics.fbeta_score(
        df['EXTRATREES_LABEL'], df['EXTRATREES_CALL'], beta=5
    )
