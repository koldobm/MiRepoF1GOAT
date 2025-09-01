import sys, pandas as pd, pathlib as p

if len(sys.argv) < 2:
    print("Uso: python tools/offline_csv_prep.py <input.csv> [output.csv]")
    sys.exit(1)

inp = p.Path(sys.argv[1])
out = p.Path(sys.argv[2]) if len(sys.argv) >= 3 else p.Path("data/ergast_offline_norm.csv")

df = pd.read_csv(inp)

cols = {c.lower(): c for c in df.columns}
def col(*cands):
    for c in cands:
        if c.lower() in cols: return cols[c.lower()]
    return None

c_season = col("season","Year")
c_round  = col("round","Race","Rnd")
c_gname  = col("givenName","GivenName","forename")
c_fname  = col("familyName","FamilyName","surname")
c_driver = col("driver","Driver","DriverName","Driver Full Name")
c_team   = col("constructor","Constructor","Team","ConstructorName","TeamName")
c_grid   = col("grid","GridPosition")
c_pos    = col("position","Position","ResultPosition","Final","RacePosition")

need = [c_season, c_round, c_team, (c_driver or (c_gname and c_fname)), c_grid, c_pos]
if not all(need):
    print("Faltan columnas mínimas: season, round, (driver || given/family), constructor/team, grid, position")
    sys.exit(2)

out_df = pd.DataFrame()
out_df["season"] = df[c_season]
out_df["round"]  = df[c_round]

if c_driver:
    out_df["driver"] = df[c_driver].astype(str)
else:
    out_df["driver"] = (df[c_gname].astype(str).str.strip() + " " + df[c_fname].astype(str).str.strip())

out_df["constructor"] = df[c_team].astype(str)
out_df["grid"]        = pd.to_numeric(df[c_grid], errors="coerce")
out_df["position"]    = pd.to_numeric(df[c_pos], errors="coerce")

out.parent.mkdir(parents=True, exist_ok=True)
out_df.to_csv(out, index=False)
print(f"[OK] Normalizado -> {out}")
