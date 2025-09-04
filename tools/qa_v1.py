import json
import sys, pathlib
import hashlib
from pathlib import Path

ROOT = pathlib.Path(__file__).resolve().parents[1]  # raíz del repo
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from f1goat.storage import _connect

OK = "OK"; FAIL = "FAIL"

def sha256(path: Path) -> str:
    b = Path(path).read_bytes()
    return hashlib.sha256(b).hexdigest()

def check_manifest(manifest_path="exports/manifest_v1.json") -> int:
    """
    Valida el manifest:
      - Soporta formato con files = list[{"path","sha256"}] o dict[path->sha256]
      - Permite marcar {"missing": true} en snapshots antiguos
    Devuelve 0 si OK, 1 si hay discrepancias.
    """
    try:
        man = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("[manifest] FAIL manifest file missing")
        return 1
    except Exception as e:
        print("[manifest] FAIL could not parse manifest:", repr(e))
        return 1

    files = man.get("files", [])
    mismatches = []

    # Compatibilidad: dict o lista
    if isinstance(files, dict):
        items = [{"path": k, "sha256": v} for k, v in files.items()]
    elif isinstance(files, list):
        items = files
    else:
        print("[manifest] FAIL invalid 'files' field (must be list or dict)")
        return 1

    for rec in items:
        path = rec.get("path")
        expected = rec.get("sha256")
        was_marked_missing = rec.get("missing", False)

        if not path:
            mismatches.append(("<no-path>", "invalid_entry"))
            continue

        p = Path(path)

        if was_marked_missing:
            # El snapshot decía "missing": si ahora existe, el manifest está desactualizado
            if p.exists():
                mismatches.append((path, "was_missing_in_manifest_but_exists_now"))
            continue

        if expected is None:
            mismatches.append((path, "no_expected_hash"))
            continue

        if not p.exists():
            mismatches.append((path, "not_found"))
            continue

        actual = sha256(p)
        if str(actual).lower() != str(expected).lower():
            mismatches.append((path, "hash_mismatch", expected, actual))

    if mismatches:
        print("[manifest] FAIL", mismatches)
        return 1
    else:
        print("[manifest] OK")
        return 0

def main():
    con = _connect()
    bad = 0

    # 1) Existencia y tamaños básicos
    exist = {
      "per_gp_core_for_ui": False,
      "season_driver_points_100": False,
      "season_team_points_100": False,
      "gp_quality": False,
    }
    for t in list(exist.keys()):
        try:
            con.execute(f"SELECT 1 FROM {t} LIMIT 1")
            exist[t] = True
        except Exception:
            pass
    print("[exist]", exist)
    if not all(exist.values()):
        bad += 1

    # 2) Rangos 0..10 per-GP
    if exist["per_gp_core_for_ui"]:
        lo, hi = con.execute("""
          SELECT
            SUM(CASE WHEN "Puntos F1GOAT (GP)"<0 THEN 1 ELSE 0 END),
            SUM(CASE WHEN "Puntos F1GOAT (GP)">10 THEN 1 ELSE 0 END)
          FROM per_gp_core_for_ui
        """).fetchone()
        print("[range per-GP] <0,>10:", (lo or 0, hi or 0))
        if (lo or 0)>0 or (hi or 0)>0:
            bad += 1

    # 3) Unicidad por temporada
    if exist["season_driver_points_100"]:
        dup = con.execute("""
          SELECT COUNT(*) FROM (
            SELECT season,"Piloto", COUNT(*) c
            FROM season_driver_points_100
            GROUP BY 1,2 HAVING COUNT(*)>1
          )
        """).fetchone()[0]
        print("[uniq drivers/season]", OK if dup==0 else FAIL, "dup=", dup)
        if dup>0: bad += 1
    if exist["season_team_points_100"]:
        dup = con.execute("""
          SELECT COUNT(*) FROM (
            SELECT season,"Equipo", COUNT(*) c
            FROM season_team_points_100
            GROUP BY 1,2 HAVING COUNT(*)>1
          )
        """).fetchone()[0]
        print("[uniq teams/season]", OK if dup==0 else FAIL, "dup=", dup)
        if dup>0: bad += 1

    # 4) Factores de temporada (sanidad)
    if exist["season_driver_points_100"]:
        y = con.execute("""
          SELECT MIN(factor), MAX(factor)
          FROM season_driver_points_100
        """).fetchone()
        print("[factor drivers] min..max:", y)
        mn, mx = y
        if mn is None or mx is None or mn<=0 or mx>10:
            bad += 1

    # 5) Consistencia pilotos: suma por temporada ~ puntos_total
    if exist["per_gp_core_for_ui"] and exist["season_driver_points_100"]:
        r = con.execute("""
          WITH sum_gp AS (
            SELECT CAST(split_part(event_key,'_',1) AS INT) season,
                   "Piloto",
                   SUM("Puntos F1GOAT (GP)") AS s
            FROM per_gp_core_for_ui
            GROUP BY 1,2
          )
          SELECT COUNT(*)
          FROM (
            SELECT d.season, d."Piloto",
                   ABS(d.puntos_total - COALESCE(s.s,0)) AS diff
            FROM season_driver_points_100 d
            LEFT JOIN sum_gp s
              ON s.season=d.season AND s."Piloto"=d."Piloto"
            WHERE diff>1e-6
          )
        """).fetchone()[0]
        print("[consistency drivers season vs sum per-GP]", OK if r==0 else FAIL, "rows_diff=", r)
        if r>0: bad += 1

    # 6) Consistencia equipos (v1: puntos_gp ya usado en vista UI)
    if exist["season_team_points_100"]:
        cnt = con.execute("SELECT COUNT(*) FROM season_team_points_100").fetchone()[0]
        print("[teams season rows]", cnt, OK if cnt>0 else FAIL)
        if cnt==0: bad += 1

    # 7) Calidad u_real
    if exist["gp_quality"]:
        umin, uavg, umax = con.execute("""
          SELECT MIN(u_real), AVG(u_real), MAX(u_real) FROM gp_quality
        """).fetchone()
        print(f"[quality u_real] min={umin} avg={float(uavg):.3f} max={umax}")
        if umin is None or umax is None:
            bad += 1

    # 8) Manifest y hashes
    bad += check_manifest("exports/manifest_v1.json")

    print("\n== QA RESULT:", OK if bad==0 else FAIL, "==")
    sys.exit(0 if bad==0 else 1)

if __name__ == "__main__":
    main()
