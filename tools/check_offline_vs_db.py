import os, sys, duckdb, pandas as pd

csv_path = os.getenv("F1GOAT_ERGAST_CSV", "data/ergast_offline_norm.csv")
db_path  = "data/f1goat.duckdb"

if not os.path.exists(csv_path):
    print(f"CSV no encontrado: {csv_path}")
    sys.exit(2)
if not os.path.exists(db_path):
    print(f"BD no encontrada: {db_path}")
    sys.exit(2)

csv = pd.read_csv(csv_path)
csv_counts = (csv.groupby(["season","round"]).size()
                 .reset_index(name="csv_drivers")
                 .sort_values(["season","round"]))

con = duckdb.connect(db_path)
db = con.sql("""
SELECT e.season, e.round, COUNT(*) AS db_drivers
FROM gp_driver_results d
JOIN gp_events e ON d.event_key = e.event_key
GROUP BY 1,2
ORDER BY 1,2
""").df()

check = pd.merge(csv_counts, db, on=["season","round"], how="outer").fillna(0)
check["delta"] = check["db_drivers"] - check["csv_drivers"]
print("Comparativa (csv vs db):")
print(check.to_string(index=False))

mismatch = check[check["delta"] != 0]
print("\nMismatches:", len(mismatch))
if len(mismatch) > 0:
    print(mismatch.to_string(index=False))
