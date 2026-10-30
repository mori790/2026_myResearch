import csv, random
random.seed(7)
rows=[]
for i in range(240):
    g = "A" if i % 2 == 0 else "B"
    rt = random.gauss(520 if g=="A" else 545, 70)
    if i % 41 == 0: rt += 420      # clear outliers (all rules agree)
    if i % 29 == 0: rt += 190      # borderline: rules disagree
    rows.append({"id": i, "group": g, "rt": round(rt, 1)})
with open("data.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["id", "group", "rt"]); w.writeheader(); w.writerows(rows)
