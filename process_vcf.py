#!/usr/bin/env python
# -*- coding: utf-8 -*-

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import cyvcf2
import pyarrow as pa
import pyarrow.csv as csv


def find_annotations(vcf):
    result = []
    # default to the VEP CSQ key
    annotation_key = "CSQ"
    for record in vcf.header_iter():
        #if record["HeaderType"] == "INFO" and "Functional annotations:" in record["Description"]:
        #    result = record["Description"][:-1].split(":")[-1].strip()[1:-1]
        #    result = [item.strip().replace(" ", "") for item in result.split("|")]
        #    annotation_key = "ANN"
        if record["HeaderType"] == "INFO" and "Consequence annotations from Ensembl VEP" in record["Description"]:
            result = record["Description"][:-1].split(":")[-1].strip()
            result = [item.strip().replace(" ", "") for item in result.split("|")]
    return annotation_key, result


def parse_header(vcf):
    annotation_key, annotations = find_annotations(vcf)
    info_keys = [record for record in vcf.header_iter() if record["HeaderType"] == "INFO"]
    return info_keys, annotation_key, annotations


def get_biomart_data(): 
    dataset = Dataset(name='hsapiens_gene_ensembl',
                  host='http://www.ensembl.org')
    df = dataset.query(attributes=['ensembl_gene_id', 'external_gene_name', 'ensembl_transcript_id', 'transcript_is_canonical'],
                       use_attr_names=True)
    return df


def main(fname, output="out.csv.gz"):
    vcf = cyvcf2.VCF(fname, lazy=True, gts012=True, threads=4)
    all_info_keys, annotation_key, annotations = parse_header(vcf)
    info_keys = ["csq." + k["ID"] for k in all_info_keys if k["ID"] not in (annotation_key, "ANN")]
    samples = vcf.samples
    schema = pa.schema([
        ("sample", pa.string()),
        ("gt", pa.int8()),
        ("chrom", pa.string()),
        ("pos", pa.int64()),
        ("id", pa.string()),
        ("ref", pa.string()), 
        ("alt", pa.string()),
        ("call_rate", pa.float64()), 
        ("num_called", pa.int32()),
        ("num_hom_ref", pa.int32()),
        ("num_het", pa.int32()),
        ("num_hom_alt", pa.int32()),
        *((key, pa.string()) for key in info_keys),
        *((annotation, pa.string()) for annotation in annotations)])
    print(schema)
    if output.endswith(".gz"):
        output = pa.CompressedOutputStream(output, "gzip")
    with csv.CSVWriter(output, schema=schema) as writer:
        n = 0
        for v in vcf:
            if v.call_rate < 0.9:
                continue
            #samples = pa.array(samples)
            genotypes = v.gt_types
            info = [v.INFO.get(field, None) for field in info_keys]
            data = {name: [] for name in schema.names}
            for consequence in v.INFO.get(annotation_key, "").split(","):
                keep = True
                annotation_data = consequence.split("|")
                csq = {k: v for k, v in zip(annotations, annotation_data)}
                #print(csq["IMPACT"], csq["SIFT"], csq["PolyPhen"])
                """
                if csq.get("IMPACT", None) is None:
                    continue
                    #print("######## FAIL filter IMPACT", csq["IMPACT"])
                if (csq["IMPACT"] == "HIGH"):
                    keep = True
                    #print("######## PASS filter IMPACT:", csq["IMPACT"])
                elif (csq["IMPACT"] == "MODERATE"): 
                    keep = True
                    #print("######## PASS filter IMPACT:", csq["IMPACT"])
                elif (csq["CADD_PHRED"] != "" and  float(csq["CADD_PHRED"]) >= 30): 
                    keep = True
                    #print("######## PASS filter CADD_PHRED:", csq["CADD_PHRED"])
                if ((csq["IMPACT"] == "MODERATE") and csq["SIFT"].startswith("deleterious(") and csq["PolyPhen"].startswith("probably_damaging") and (csq["CANONICAL"] == "YES")): 
                    keep = True
                if csq["gnomAD_AF"] != '' and float(csq["gnomAD_AF"]) > 0.01:
                    keep = False
                    #print("######## FAIL filter gnomAD_AF", csq["gnomAD_AF"])
                """
                if keep:
                    #annotation_data = pa.array(consequence.split("|"))
                    annotation_data = consequence.split("|")
                    #print(annotation_data)
                    for sample, genotype in zip(samples, genotypes):
                        #print(sample, genotype)
                        if (genotype == 1) or (genotype == 2):
                            for name, val in zip(schema.names, (sample, genotype, v.CHROM, v.POS, v.ID, v.REF, v.ALT[0], 
                                         v.call_rate, v.num_called, v.num_hom_ref, v.num_het, v.num_hom_alt, *info, *annotation_data)):
                                if val == "":
                                    val = None
                                data[name].append(val)
            if data["sample"]:
                for n, name in enumerate(data):
                    data[name] = pa.array(data[name]).cast(schema[n].type)
                    #if len(data[name]) == 32:
                    #    print("####################################################")
                    #print(name, schema[n], data[name], len(data[name]))
                #table = pa.table(data, schema=schema)
                table = pa.Table.from_pydict(data, schema=schema)
                writer.write(table)
        n += 1
        if n % 1000 == 0:
            print(n)

if __name__ == '__main__':
    import sys
    main(sys.argv[1], sys.argv[2])
