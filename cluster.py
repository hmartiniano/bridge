#!/usr/bin/env python3
import collections
import logging
from sklearn.model_selection import RandomizedSearchCV
import hdbscan
from sklearn.metrics import make_scorer
import pandas as pd
import os
import json
import subprocess
import argparse
import numpy as np
import umap
import optuna
from optuna.trial import TrialState
from optuna.integration.mlflow import MLflowCallback
import joblib

SEED = 42
METHODS = ["hdbscan"]



def create_parser():
    parser = argparse.ArgumentParser()
    #parser.add_argument("-d", "--data", nargs='+', help="Train, validation and test files")
    parser.add_argument("-m", "--args.method", default="hdbscan", choices=METHODS, help="Method to use")
    parser.add_argument("-n", "--n_trials", default=100, type=int, help="Number of optuna trials")
    parser.add_argument("-o", "--outliers", default=None, type=str, help="IDs of outliers")
    return parser


def remove_outliers(data, fname):
    df = pd.read_csv(fname, header=None)
    return data[~data.index.isin(df[0].tolist())]


def run_experiment(data, min_samples, min_cluster_size, cluster_selection_method, metric, n_neighbors, min_dist, n_components):
        #logging.captureWarnings(True)
        hdb = hdbscan.HDBSCAN(gen_min_span_tree=True, min_samples=min_samples, min_cluster_size=min_cluster_size,
                cluster_selection_method=cluster_selection_method, metric=metric)

        #validity_scroer = "hdbscan__hdbscan___HDBSCAN__validity_index"
        #validity_scorer = make_scorer(hdbscan.validity.validity_index, greater_is_better=True)
        embedding = umap.UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=n_components,
            random_state=SEED,
        ).fit_transform(data)
        labels = hdb.fit_predict(embedding.data)
        clustered = (labels >= 0)
        frac_clustered = np.sum(clustered) / data.shape[0]
        print(f"Fraction clustered: {frac_clustered}")
        print(f"Number of clusters: {collections.Counter(labels)}")
        return embedding, hdb, labels


class Objective:

    def __init__(self, data):
        self.data = data 

    def __call__(self, trial):
        min_samples = trial.suggest_int("min_samples", 2, 20, 1)
        min_cluster_size = trial.suggest_int("min_cluster_size", 2, 20, 1)
        #hidden_dim = trial.suggest_int("hidden_dim", 10, 501)
        #batch_size = trial.suggest_int("batch_size", list(range(1000, 11000, 1000)))
        #args.method = trial.suggest_categorical("args.emthod", ["TransE_l2"])
        cluster_selection_method = trial.suggest_categorical('cluster_selection_method', ['eom','leaf'])
        metric = trial.suggest_categorical('metric', ['euclidean','manhattan'])

        #UMAP

        n_neighbors = trial.suggest_int("n_neighbors", 30, 100, 1)
        n_components = trial.suggest_int("n_components", 2, 50, 1)
        min_dist = trial.suggest_float("min_dist", 0.0, 1.0)

        embedding, hdb, labels = run_experiment(self.data, min_samples, min_cluster_size,
            cluster_selection_method, metric, n_neighbors, min_dist, n_components)
    
        return hdb.relative_validity_


def main():
    #run_experiment("go", "ComplEx", "1000", "128", "16", "32", 0.1)
    parser = create_parser()
    args = parser.parse_args()
    args.method = "hdbscan"
    study_name = f"{args.method}.study"
    study = optuna.create_study(
                direction="maximize", 
                study_name=study_name, 
                storage=f'sqlite:///{args.method}.db', 
                load_if_exists=True,
                )
    data = pd.read_csv("TransR_samples.csv.gz", index_col=0)
    if args.outliers is not None:
        data = remove_outliers(data, args.outliers)
    objective = Objective(data)
    try:
        n_complete_trials = len([trial for trial in study.get_trials() if trial.state == TrialState.COMPLETE])
    except:
        n_complete_trials = 0
    print(f"Study {study_name} has {n_complete_trials} complete trials.")
    if n_complete_trials < args.n_trials:
        study.optimize(objective, n_trials=args.n_trials)
    joblib.dump(study, study_name)
    df = study.trials_dataframe()
    df = df.sort_values(by="value", ascending=False)
    df.to_csv("hdbscan_trials.csv")
    print(df.head())
    best = df[[col for col in df.columns if col.startswith("params")]].to_dict(orient="records")[0]
    best = {k.replace("params_", ""): v for k, v in best.items()} 
    print(f"Best params: {best}")
    embedding, hdb, labels = run_experiment(data, **best)
    df = pd.DataFrame(embedding) 
    df.index = data.index
    df["label"] = labels
    df.to_csv("hdbscan_study_results.csv")


if __name__ == '__main__':
    main()
