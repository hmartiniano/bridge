import logging
from sklearn.model_selection import RandomizedSearchCV
import hdbscan
from sklearn.metrics import make_scorer
import pandas as pd


SEED = 42


df = pd.read_csv("TransR.csv.gz")
df = df[~df.label.str.contains(":")]
embedding = df.set_index("label")

#logging.captureWarnings(True)
hdb = hdbscan.HDBSCAN(gen_min_span_tree=True).fit(embedding)

# specify parameters and distributions to sample from
param_dist = {'min_samples': [10,30,50,60,100],
              'min_cluster_size':[100,200,300,400,500,600],  
              'cluster_selection_method' : ['eom','leaf'],
              'metric' : ['euclidean','manhattan'] 
             }

#validity_scroer = "hdbscan__hdbscan___HDBSCAN__validity_index"
#validity_scorer = make_scorer(hdbscan.validity.validity_index, greater_is_better=True)
def score_func(y_true, y_pred, **kwargs):
    return hdbscan.validity.validity_index(y_true)

validity_scorer = make_scorer(score_func, greater_is_better=True)


n_iter_search = 20
random_search = RandomizedSearchCV(hdb
                                   ,param_distributions=param_dist
                                   ,n_iter=n_iter_search
                                   ,scoring=validity_scorer 
                                   ,random_state=SEED
                                   ,verbose=3
                                   ,n_jobs=-1)

random_search.fit(embedding)


print(f"Best Parameters {random_search.best_params_}")
print(f"DBCV score :{random_search.best_estimator_.relative_validity_}")
