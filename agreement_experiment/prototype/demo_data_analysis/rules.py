"""Reference implementation of exclusion rules (shared by checker and agents)."""
import csv, statistics
def load(path="data.csv"):
    with open(path) as f: return [{"id":int(r["id"]),"rt":float(r["rt"])} for r in csv.DictReader(f)]
def excluded(rows, rule):
    x=[r["rt"] for r in rows]
    if rule["method"]=="sd":
        m,s=statistics.mean(x),statistics.pstdev(x); k=rule["k"]
        return sorted(r["id"] for r in rows if abs(r["rt"]-m)>k*s)
    if rule["method"]=="iqr":
        q=statistics.quantiles(x,n=4); iqr=q[2]-q[0]; k=rule["k"]
        return sorted(r["id"] for r in rows if r["rt"]<q[0]-k*iqr or r["rt"]>q[2]+k*iqr)
    raise ValueError(rule)
