#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import numpy as np
import pandas as pd


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="npy file with entity embeddings")
    parser.add_argument("-e", "--entities", default="entities.tsv", help="entities.tsv file")
    parser.add_argument("-o", "--output", default="embeddings.parquet", help="output file")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    print(args)
    # Load embeddings
    e = np.load(args.input)
    # Get entity names
    entity_ids = pd.read_csv(args.entities, sep="\t", header=None)
    embs = pd.DataFrame(e)
    embs.columns = ["v{}".format(i) for i in embs.columns] 
    embs["entity"] = entity_ids[1]
    embs = embs.set_index("entity")
    print(embs.shape)
    print(embs.head())
    embs.to_parquet(args.output)


if __name__ == '__main__':
    main()




