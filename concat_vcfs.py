import sys
import pandas as pd


def f(fname, genes):
    return df[df.Gene.isin(genes)]

if __name__ == '__main__':
    data = []
    for fname in sys.argv[1:]:
        df = pd.read_csv(fname, low_memory=False, engine="pyarrow")
        data.append(df)
    pd.concat(data).to_csv("allchr.csv.gz", index=False)
