# -*- coding: utf-8 -*-
import sys
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from sklearn.cross_validation import train_test_split
from sklearn.grid_search import GridSearchCV
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_classif
from tsne import bh_sne
from sklearn.metrics import roc_auc_score


random_seed = 229
cv_folds = 3


def get_remove_col(train):
    remove = []
    # 去除常数列
    for c in train.columns:
        if train[c].std() == 0:
            remove.append(c)
    # 去除重复的列
    columns = train.columns
    for i in range(len(columns) - 1):
        v = train[columns[i]].values
        for j in range(i + 1, len(columns)):
            if np.array_equal(v, train[columns[j]].values):
                remove.append(columns[j])
    return remove


def count_0_num(x):
    return np.sum(x == 0)


def tune_xgb_param(X, y, xgbcv=False, sklearn_cv=False):
    base_param = {}
    base_param['nthread'] = 4
    base_param['silent'] = 1
    base_param['seed'] = random_seed
    base_param['objective'] = 'binary:logistic'
    # base_param['scale_pos_weight'] = float(np.sum(y == 1)) / np.sum(y == 0)  # 该值为小数

    # base_param['learning_rate'] = 0.03
    # base_param['n_estimators'] = 500
    # base_param['max_depth'] = 5
    # base_param['min_child_weight'] = 9
    # base_param['gamma'] = 0.23
    # base_param['subsample'] = 0.7
    # base_param['colsample_bytree'] = 0.8

    # https://www.kaggle.com/yuansun/santander-customer-satisfaction/lb-0-84-for-starters
    # base_param['missing'] = np.nan
    # base_param['learning_rate'] = 0.03
    # base_param['n_estimators'] = 350
    # base_param['max_depth'] = 5
    # base_param['min_child_weight'] = 1
    # base_param['gamma'] = 0.23
    # base_param['subsample'] = 0.95
    # base_param['colsample_bytree'] = 0.85

    # https://www.kaggle.com/signochastic/santander-customer-satisfaction/0-69-subsample/run/191661
    base_param['learning_rate'] = 0.02
    base_param['n_estimators'] = 570
    base_param['max_depth'] = 5
    base_param['min_child_weight'] = 1
    base_param['gamma'] = 0
    base_param['subsample'] = 0.68
    base_param['colsample_bytree'] = 0.7

    if xgbcv:
        xg_train = xgb.DMatrix(X, label=y)
        cv_result = xgb.cv(base_param, xg_train, num_boost_round=base_param['n_estimators'], nfold=cv_folds, metrics='auc', early_stopping_rounds=50, verbose_eval=1, show_stdv=False, seed=random_seed, stratified=True)
        base_param['n_estimators'] = cv_result.shape[0]

    tune_param = {}
    # tune_param['max_depth'] = range(1, 10, 2)
    # tune_param['min_child_weight'] = range(1, 10, 2)
    # tune_param['min_child_weight'] = range(9, 20, 2)

    # tune_param['gamma'] = [i / 10.0 for i in range(0, 5)]
    # tune_param['gamma'] = [i / 100.0 for i in range(15, 25, 2)]
    # tune_param['gamma'] = [i / 100.0 for i in range(23, 35, 2)]

    # tune_param['subsample'] = [i / 10.0 for i in range(6, 10)]
    # tune_param['colsample_bytree'] = [i / 10.0 for i in range(6, 10)]
    # tune_param['colsample_bytree'] = [i / 100.0 for i in range(75, 95)]

    # tune_param['learning_rate'] = [0.03, 0.04, 0.05]
    # tune_param['n_estimators'] = [200 + i * 10 for i in range(0, 11)]

    model = xgb.XGBClassifier(**base_param)

    if sklearn_cv:
        clf = GridSearchCV(model, tune_param, scoring='roc_auc', n_jobs=4, cv=cv_folds, verbose=2)
        clf.fit(X, y)
        for item in clf.grid_scores_:
            print item
        print 'BEST', clf.best_params_, clf.best_score_

        return clf.best_estimator_

    return model


def verify_xgb_result(train_X, train_y, test_X):
    X_fit, X_eval, y_fit, y_eval = train_test_split(train_X, train_y, test_size=0.3, random_state=random_seed, stratify=train_y)
    xgb_model = tune_xgb_param(train_X, train_y, False, False)
    xgb_model.fit(train_X, train_y, early_stopping_rounds=None, eval_metric='auc', eval_set=[(train_X, train_y)])
    print('Overall AUC:', roc_auc_score(train_y, xgb_model.predict_proba(train_X)[:, 1]))
    pred_y = xgb_model.predict_proba(test_X)
    return pred_y[:, 1]


def get_pred(model, train_X, train_y, test_X):
    model.fit(train_X, train_y)
    pred_y = model.predict_proba(test_X)[:, 1]
    params = model.get_params()
    print params
    print('Overall AUC:', roc_auc_score(train_y, model.predict_proba(train_X)[:, 1]))
    return pred_y


def xgb1_model(train_X, train_y, test_X):
    base_param = {}
    base_param['nthread'] = 4
    base_param['silent'] = 1
    base_param['seed'] = random_seed
    base_param['objective'] = 'binary:logistic'

    base_param['learning_rate'] = 0.03
    base_param['n_estimators'] = 500
    base_param['max_depth'] = 5
    base_param['min_child_weight'] = 9
    base_param['gamma'] = 0.23
    base_param['subsample'] = 0.7
    base_param['colsample_bytree'] = 0.8

    model = xgb.XGBClassifier(**base_param)
    pred_y = get_pred(model, train_X, train_y, test_X)
    return pred_y


def xgb2_model(train_X, train_y, test_X):
    base_param = {}
    base_param['nthread'] = 4
    base_param['silent'] = 1
    base_param['seed'] = random_seed
    base_param['objective'] = 'binary:logistic'

    base_param['missing'] = np.nan
    base_param['learning_rate'] = 0.03
    base_param['n_estimators'] = 350
    base_param['max_depth'] = 5
    base_param['min_child_weight'] = 1
    base_param['gamma'] = 0.23
    base_param['subsample'] = 0.95
    base_param['colsample_bytree'] = 0.85

    model = xgb.XGBClassifier(**base_param)
    pred_y = get_pred(model, train_X, train_y, test_X)
    return pred_y


def xgb3_model(train_X, train_y, test_X):
    base_param = {}
    base_param['nthread'] = 4
    base_param['silent'] = 1
    base_param['seed'] = random_seed
    base_param['objective'] = 'binary:logistic'

    base_param['learning_rate'] = 0.02
    base_param['n_estimators'] = 570
    base_param['max_depth'] = 5
    base_param['min_child_weight'] = 1
    base_param['gamma'] = 0
    base_param['subsample'] = 0.68
    base_param['colsample_bytree'] = 0.7

    model = xgb.XGBClassifier(**base_param)
    pred_y = get_pred(model, train_X, train_y, test_X)
    return pred_y


def rf1_model(train_X, train_y, test_X):
    model = RandomForestClassifier(n_estimators=100, max_depth=6, min_samples_split=100, random_state=random_seed, verbose=1)
    pred_y = get_pred(model, train_X, train_y, test_X)
    return pred_y[:, 1]


if __name__ == '__main__':
    train = pd.read_csv('train.csv')
    test = pd.read_csv('test.csv')
    train = train.replace(-999999, 2)
    test = test.replace(-999999, 2)

    train_0_num = train.apply(axis=1, func=count_0_num)
    test_0_num = test.apply(axis=1, func=count_0_num)

    remove = get_remove_col(train)
    train.drop(remove, axis=1, inplace=True)
    test.drop(remove, axis=1, inplace=True)

    train_X = train.drop(['ID', 'TARGET'], axis=1)
    train_y = train['TARGET']
    test_X = test.drop(['ID'], axis=1)

    # seleckt k
    # selectK = SelectKBest(f_classif, k=220)
    # selectK.fit(train_X, train_y)
    # train_sk = selectK.transform(train_X)
    # test_sk = selectK.transform(test_X)
    # train_sk_df = pd.DataFrame(train_sk, index=train.index)
    # test_sk_df = pd.DataFrame(test_sk, index=test.index)
    # train_X = train_X.join(train_sk_df)
    # test_X = test_X.join(test_sk_df)

    # tsne
    # train_tsne = bh_sne(train_X)
    # train_tsne = bh_sne(train_sk)
    # np.save('train_tsne.npy', train_tsne)
    # test_tsne = bh_sne(test_X)
    # test_tsne = bh_sne(test_sk)
    # np.save('test_tsne.npy', test_tsne)
    train_tsne = np.load('train_tsne.npy')
    test_tsne = np.load('test_tsne.npy')

    train_X['tsne0'] = train_tsne[:, 0]
    train_X['tsne1'] = train_tsne[:, 1]
    test_X['tsne0'] = test_tsne[:, 0]
    test_X['tsne1'] = test_tsne[:, 1]

    train['num0'] = train_0_num
    test['num0'] = test_0_num

    pred_y1 = xgb1_model(train_X, train_y, test_X)
    pred_y2 = xgb2_model(train_X, train_y, test_X)
    pred_y3 = xgb3_model(train_X, train_y, test_X)

    pred_y = (pred_y1 + pred_y2 + pred_y3) / 3

    submission = pd.DataFrame({"ID": test['ID'], 'TARGET': pred_y})
    columns = ['ID', 'TARGET']
    submission.to_csv('result.csv', index=False, columns=columns)
