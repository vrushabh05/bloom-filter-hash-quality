import csv, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
rows = list(csv.DictReader(open("results/summary.csv")))
labels = [r["hash"] for r in rows]; vals = [float(r["mean_fpr"]) for r in rows]; err = [float(r["std_fpr"]) for r in rows]
colors = ["#2a7f62" if "good" in l else "#c2410c" for l in labels]
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=160)
ax.barh(labels[::-1], vals[::-1], xerr=err[::-1], color=colors[::-1], height=0.6, ecolor="#555")
ax.axvline(0.1378, color="#1d4ed8", ls="--", lw=1.4, label="Theoretical FPR (0.1378)")
for i, v in enumerate(vals[::-1]): ax.text(v + 0.015, i, f"{v:.3f}", va="center", fontsize=9)
ax.set_xlim(0, 1.12); ax.set_xlabel("False-positive rate (mean of 6 seeds, 20,000 queries each)")
ax.set_title("Bloom filter (m=10,000, k=7, n=2,000): hash quality vs FPR", fontsize=11)
ax.legend(loc="lower right", frameon=False); [ax.spines[s].set_visible(False) for s in ("top", "right")]
plt.tight_layout(); plt.savefig("assets/fpr_by_hash.png")
