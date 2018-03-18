import os
from processing import build_data
import pandas as pd
from sklearn.feature_extraction import DictVectorizer
import lightgbm as lgb


# use this to change language pair trained on
lang = 'all'
# lightgbm parameters for each model. Different ones might be better for
# different language pairs
params = {
    'fr_en': {
        'application': 'binary',
        'metric': 'auc',
        'learning_rate': .1,
        'num_leaves': 128,
        'min_data_in_leaf': 20,
        'num_boost_round': 800
    },
    'en_es': {
        'application': 'binary',
        'metric': 'auc',
        'learning_rate': .1,
        'num_leaves': 128,
        'min_data_in_leaf': 20,
        'num_boost_round': 1000
    },
    'es_en': {
        'application': 'binary',
        'metric': 'auc',
        'learning_rate': .1,
        'num_leaves': 128,
        'min_data_in_leaf': 20,
        'num_boost_round': 900
    },
    'all': {
        'application': 'binary',
        'metric': 'auc',
        'learning_rate': .1,
        'num_leaves': 256,
        'min_data_in_leaf': 20,
        'num_boost_round': 1400
    }
}


# load data
if lang == 'all':
    data = build_data(
        'all',
        [
            'data/data_{0}/{0}.slam.20171218.train.new'.format('en_es'),
            'data/data_{0}/{0}.slam.20171218.dev.new'.format('en_es'),
            'data/data_{0}/{0}.slam.20171218.train.new'.format('fr_en'),
            'data/data_{0}/{0}.slam.20171218.dev.new'.format('fr_en'),
            'data/data_{0}/{0}.slam.20171218.train.new'.format('es_en'),
            'data/data_{0}/{0}.slam.20171218.dev.new'.format('es_en')
        ],
        [
            'data/data_{0}/test.{0}.new'.format('en_es'),
            'data/data_{0}/test.{0}.new'.format('fr_en'),
            'data/data_{0}/test.{0}.new'.format('es_en')
        ],
        labelfiles=[
            'data/data_{0}/{0}.slam.20171218.dev.key'.format('en_es'),
            'data/data_{0}/{0}.slam.20171218.dev.key'.format('fr_en'),
            'data/data_{0}/{0}.slam.20171218.dev.key'.format('es_en')
        ],
        n_users=None)
else:
    data = build_data(lang[:2],
                      ['data/data_{0}/{0}.slam.20171218.train.new'.format(lang),
                       'data/data_{0}/{0}.slam.20171218.dev.new'.format(lang)],
                      ['data/data_{0}/test.{0}.new'.format(lang)],
                      labelfiles=['data/data_{0}/{0}.slam.20171218.dev.key'.format(lang)],
    n_users=None)
train_x, train_ids, train_y, test_x, test_ids, test_y = data

cat_features = ['token', 'root', 'user',
                'prev_token', 'next_token', 'parseroot_token']
for key in cat_features:
    val_dict = {}
    val_idx = 0
    for d in train_x + test_x:
        t = d[key]
        if t in val_dict:
            d[key] = val_dict[t]
        else:
            val_dict[t] = val_idx
            d[key] = val_idx
            val_idx += 1


# put data in scipy sparse matrix
dv = DictVectorizer()
train_x_sparse = dv.fit_transform(train_x)
test_x_sparse = dv.transform(test_x)

names = dv.feature_names_

# train light gradient boosting machine model
d_train = lgb.Dataset(train_x_sparse, label=train_y)

bst = lgb.train(params[lang], d_train, valid_sets=[d_train],
                valid_names=['train', 'valid'],
                feature_name=names,
                categorical_feature=cat_features,
                num_boost_round=params[lang]['num_boost_round'],
                verbose_eval=10)

if not os.path.exists('models'):
    os.makedirs('models')
bst.save_model('models/test.{}.bst'.format(lang))
test_predicted = bst.predict(test_x_sparse)
test_predicted = bst.predict(test_x_sparse)
test_predictions_df = pd.DataFrame({
    'instance': test_ids,
    'prediction': test_predicted
})
test_predictions_df.to_csv('test.{}.pred'.format(lang), header=False,
                           index=False, sep=" ")
