import sys
import os
from typing import List, Optional
from argparse import ArgumentParser

def update(season: Optional[int] = None) -> bool:
    from .data_sources import ingest_latest
    try:
        y, r, name = ingest_latest(season_hint=season or 2025)
        print(f"[F1GOAT] Ingestado: {name} (temporada {y}, ronda {r}).")
        return True
    except Exception as e:
        print("[F1GOAT] Error en actualización:", e)
        return False

def backfill(season: Optional[int], start: Optional[int], end: Optional[int], ergast_only: bool, fastf1_only: bool) -> int:
    from .data_sources import ingest_season, ingest_range
    pref = "auto"
    if ergast_only and fastf1_only:
        print("No puedes usar --ergast-only y --fastf1-only a la vez.")
        return 2
    if ergast_only:
        pref = "ergast"
    if fastf1_only:
        pref = "fastf1"

    if season:
        ok = ingest_season(season, preference=pref)  # type: ignore
        return 0 if ok >= 0 else 1
    if start and end:
        ok = ingest_range(start, end, preference=pref)  # type: ignore
        return 0 if ok >= 0 else 1
    print("Uso: python -m f1goat backfill --season 2025 [--ergast-only|--fastf1-only]\n"
          "     python -m f1goat backfill --from 2018 --to 2025 [--ergast-only|--fastf1-only]")
    return 1

def validate() -> int:
    from .validations import validate_latest_event, format_report, quick_summary
    rows = validate_latest_event()
    print("[F1GOAT] Resumen tablas:", quick_summary())
    print("[F1GOAT] Validaciones:")
    print(format_report(rows))
    failed = any(r[2] == "FAIL" for r in rows)
    return 1 if failed else 0

def coverage() -> int:
    from .coverage import coverage_report
    print("[F1GOAT] Cobertura por temporada:")
    print(coverage_report())
    return 0

def main(argv: List[str] | None = None) -> int:
    parser = ArgumentParser(prog="f1goat", description="F1GOAT CLI")
    sub = parser.add_subparsers(dest="command")
    p_up = sub.add_parser("update", help="Actualizar datos (último GP disponible)")
    p_up.add_argument("--season", type=int, default=None, help="Temporada preferida (hint).")

    p_bf = sub.add_parser("backfill", help="Ingesta de temporada completa o rango")
    p_bf.add_argument("--season", type=int, default=None, help="Temporada única (ej. 2025)")
    p_bf.add_argument("--from", dest="from_year", type=int, default=None, help="Año inicio")
    p_bf.add_argument("--to", dest="to_year", type=int, default=None, help="Año fin")
    p_bf.add_argument("--ergast-only", action="store_true", help="Forzar Ergast (ignora FastF1)")
    p_bf.add_argument("--fastf1-only", action="store_true", help="Forzar FastF1 (sin Ergast)")

    # Nuevo: ingest --source jolpica --seasons A-B(,C)
    p_ing = sub.add_parser("ingest", help="Ingesta dirigida por fuente")
    p_ing.add_argument("--seasons", required=True, help="Ej: 1950-1952 o lista 1950,1952")
    p_ing.add_argument("--source", choices=["jolpica","ergast","fastf1","auto"], default="auto")
    p_ing.add_argument("--rate", type=float, default=float(os.getenv("F1GOAT_ERGAST_RATE","3")), help="req/s (por defecto 3)")
    p_ing.add_argument("--resume", action="store_true", help="reanudar donde falte (si aplica)")

    sub.add_parser("validate", help="Validar último GP en la base de datos")
    sub.add_parser("coverage", help="Mostrar cobertura (qué temporadas y rondas faltan)")
    args = parser.parse_args(argv)

    if args.command == "update":
        ok = update(args.season)
        return 0 if ok else 1
    if args.command == "backfill":
        return backfill(args.season, args.from_year, args.to_year, args.ergast_only, args.fastf1_only)
    if args.command == "ingest":
        # Parseo flexible de años: rangos A-B y/o lista separada por comas
        years = []
        for chunk in (args.seasons or "").split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            if "-" in chunk:
                a,b = chunk.split("-",1)
                years.extend(range(int(a), int(b)+1))
            else:
                years.append(int(chunk))
        if not years:
            print("[F1GOAT] ingest: sin años válidos", file=sys.stderr)
            return 2
        erg_only    = args.source in ("jolpica","ergast")
        fastf1_only = (args.source == "fastf1")
        if args.source == "jolpica":
            os.environ.setdefault("F1GOAT_ERGAST_BASE", "https://api.jolpi.ca/ergast")
            print(f"[F1GOAT] Ingest (jolpica): base={os.getenv('F1GOAT_ERGAST_BASE')}", file=sys.stderr)
        # Reutiliza backfill min..max
        return backfill(None, min(years), max(years), erg_only, fastf1_only)

    if args.command == "validate":
        return validate()
    if args.command == "coverage":
        return coverage()

    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())
