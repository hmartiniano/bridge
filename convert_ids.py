from gprofiler import GProfiler

gp = GProfiler(return_dataframe=True)
r = gp.convert(organism='hsapiens',
            query=['NR1H4','TRIP12','UBC','FCRL3','PLXNA3','GDNF','VPS11'],
            target_namespace='ENTREZGENE_ACC')
print(r)
r = gp.convert(organism='hsapiens',
            query=['NR1H4','TRIP12','UBC','FCRL3','PLXNA3','GDNF','VPS11'],
            target_namespace='UNIPROT')
print(r)
