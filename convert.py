import pandas as pd



mappings = pd.read_csv("HUMAN_9606_idmapping.dat.gz", sep="\t", header=None)
mappings.columns = ["iid", "db", "oid"]


ensembl_prot = mappings[mappings["db"] == "Ensembl"]
ensembl_prot["new_oid"] = ensembl_prot["oid"].str.split(".").str.get(0)
ensembl_prot = ensembl_prot.set_index("new_oid")["iid"]
ensembl_prot = ensembl_prot[~ensembl_prot.index.duplicated(keep='first')]

print(ensembl_prot)

sfari = pd.read_csv("sfari_genes_23_11_23.csv")
#status,gene-symbol,gene-name,ensembl-id,chromosome,genetic-category,gene-score,syndromic,eagle,number-of-reports

sfari["uniprot"] = sfari["ensembl-id"].map(ensembl_prot)

print(sfari.head())

sfari["syndromic"] = sfari["syndromic"].astype(bool)
print(sfari["gene-score"].unique())
print(sfari.shape[0])
sfari = sfari[(sfari["gene-score"] <= 2) | sfari["syndromic"]]
print(sfari["gene-score"].unique())
print(sfari.shape[0])

sfari["ensembl-id"] = "ENSEMBL:" + sfari["ensembl-id"]
sfari["ensembl-id"].dropna().to_csv("sfari_gene_ids.txt", index=False, header=False)

sfari["uniprot"] = "UNIPROTKB:" + sfari["uniprot"]
sfari["uniprot"].dropna().to_csv("sfari_protein_ids.txt", index=False, header=False)
