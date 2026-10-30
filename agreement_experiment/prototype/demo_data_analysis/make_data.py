import csv, random
random.seed(0)
rows=[]
for i in range(200):
    rt=random.gauss(500,60)
    if i%37==0: rt+=400          # extreme values
    if i%53==0: rt+=150          # mild values: IQR rule and 3SD rule disagree here
    rows.append({"id":i,"rt":round(rt,1)})
with open("data.csv","w",newline="") as f:
    w=csv.DictWriter(f,["id","rt"]); w.writeheader(); w.writerows(rows)
