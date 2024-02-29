import sys
import pandas as pd

def _filter(df):
    #df = df[["biolink:Case", "Gene", "RNACENTRAL", "SWISSPROT"]]
    df["subject"] = df["sample"]
    #df = df.set_index("subject").replace("", pd.NA)
    df = df.replace("", pd.NA)
    # Sample - gene
    df2 = df[~df["Gene"].isnull()].copy()
    df2["predicate"] = "biolink:Case-has_variant_affecting-biolink:Gene"
    df2["object"] = "ENSEMBL:" + df2["Gene"]
    df2[["subject", "predicate", "object"]].replace("", pd.NA).dropna().drop_duplicates().to_csv("gene.csv", index=False)

    # Sample - protein
    df2 = df[~df["SWISSPROT"].isnull()].copy()
    df2["predicate"] = "biolink:Case-has_variant_affecting-biolink:Protein"
    df2["object"] = "UNIPROTKB:" + df2["SWISSPROT"].str.split(".").str.get(0)
    df2[["subject", "predicate", "object"]].replace("", pd.NA).dropna().drop_duplicates().to_csv("protein.csv", index=False)

    # Sample - ncRNA
    df2 = df[~df["RNACENTRAL"].isnull()].copy()
    df2["RNACENTRAL"] = df2["RNACENTRAL"].str.split("&")
    df2 = df2.explode("RNACENTRAL").replace("", pd.NA)
    df2 = df2[df2.SWISSPROT.isna()]
    df2["predicate"] = "biolink:Case-has_variant_affecting-biolink:RNAProduct"
    df2["object"] = "RNACENTRAL:" + df2["RNACENTRAL"].str.split("_").str.get(0)
    df2[["subject", "predicate", "object"]].replace("", pd.NA).dropna().drop_duplicates().to_csv("rnacentral.csv", index=False)


def f(fname, genes):
    return df[df.Gene.isin(genes)]

if __name__ == '__main__':
    data = []
    for fname in sys.argv[1:]:
        df = pd.read_csv(fname, engine="pyarrow", usecols=["sample", "Gene", "RNACENTRAL", "SWISSPROT"])
        data.append(df)
    _filter(pd.concat(data)) #.to_csv("allchr.csv.gz", index=False)
