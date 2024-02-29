import sys
import pandas as pd


def f(fname, genes):
    df = pd.read_csv(fname, low_memory=False)
    return df[df.Gene.isin(genes)]

if __name__ == '__main__':
    genes = pd.read_csv("sfari_ensg.csv", header=None)[0].tolist()
    data = []
    for fname in sys.argv[1:]:
        data.append(f(fname, genes))
    pd.concat(data).to_csv("sfari_s12_filtered.csv.gz", index=False)
