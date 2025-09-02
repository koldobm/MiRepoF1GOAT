import os, re, pathlib, json, textwrap, shutil, difflib

ROOT = pathlib.Path(".")
OUT = pathlib.Path("/tmp/jolpica2")
ORIG = OUT/"orig"; NEW = OUT/"new"; PATCH = OUT/"patches"
for p in (ORIG, NEW, PATCH): p.mkdir(parents=True, exist_ok=True)

def rd(p): return pathlib.Path(p).read_text(encoding="utf-8")
def wr(p, s): 
    pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(p).write_text(s, encoding="utf-8")
def cp(src, dst):
    dst = pathlib.Path(dst); dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def udiff(label_a, a, label_b, b):
    return "".join(difflib.unified_diff(
        a.splitlines(True), b.splitlines(True),
        fromfile=label_a, tofile=label_b, n=3
    ))

# ---------- http.py (f1goat/http.py) ----------
http_path = ROOT/"f1goat/http.py"
if not http_path.exists():
    # archivo nuevo (mínimo viable)
    base_http = textwrap.dedent('''\
        import json, os, sys, time, urllib.request, urllib.error
        from urllib.parse import urljoin

        _JOLPICA_DEFAULT = "https://api.jolpi.ca/ergast"
        _printed_base = False
        _rate_last = []
        _RATE = float(os.getenv("F1GOAT_ERGAST_RATE", "3"))  # req/seg aprox

        def _env_bool(name: str, default: bool=False) -> bool:
            v = os.getenv(name, "")
            if not v: return default
            return v.lower() in ("1","true","yes","on")

        def _print_once_base(base: str):
            global _printed_base
            if not _printed_base:
                print(f"[F1GOAT] Using Jolpica-F1: {base}", file=sys.stderr)
                _printed_base = True

        def _rate_limit():
            if _RATE <= 0: return
            now = time.monotonic(); window = 1.0
            global _rate_last
            _rate_last = [t for t in _rate_last if now - t < window]
            if len(_rate_last) >= _RATE:
                delay = window - (now - _rate_last[0])
                if delay > 0: time.sleep(delay)
            _rate_last.append(time.monotonic())

        def _upgrade(url: str) -> str:
            # fuerza https (requisito)
            return url.replace("http://","https://",1) if url.startswith("http://") else url

        def _http_json(url: str, timeout: float=15.0, max_redirects: int=3):
            # backoff sencillo + follow redirects (máx 3)
            url = _upgrade(url)
            headers = {
                "User-Agent": f"F1GOAT/{os.getenv('F1GOAT_VERSION','dev')}",
                "Accept": "application/json",
            }
            tries = 0
            while True:
                _rate_limit()
                req = urllib.request.Request(url, headers=headers)
                try:
                    with urllib.request.urlopen(req, timeout=timeout) as r:
                        ct = r.headers.get("Content-Type","")
                        data = r.read().decode("utf-8","replace")
                        # urllib sigue redirects por defecto, pero limitamos manualmente si el server usa 30x con HTTPError
                        return json.loads(data)
                except urllib.error.HTTPError as e:
                    # redirecciones explícitas (p.ej. 301 desde reverse)
                    if e.code in (301,302,303,307,308) and max_redirects>0:
                        loc = e.headers.get("Location")
                        if loc:
                            url = _upgrade(urljoin(url, loc))
                            max_redirects -= 1
                            continue
                    # 429/5xx → backoff
                    if e.code in (429,500,502,503,504) and tries < 3:
                        time.sleep(0.5*(2**tries)); tries += 1; continue
                    raise
                except Exception as ex:
                    if tries < 3:
                        time.sleep(0.5*(2**tries)); tries += 1; continue
                    raise

        def ergast_json(path: str):
            """
            Descarga JSON de una ruta Ergast-compatible (Jolpica-F1).
            - BASE por defecto: https://api.jolpi.ca/ergast
            - Respeta F1GOAT_BLOCK_ERGAST SOLO para ergast.com (NO bloquea api.jolpi.ca)
            - Sigue redirects (máx 3), https forzado, rate-limit aproximado 3 req/s.
            """
            base = os.getenv("F1GOAT_ERGAST_BASE", _JOLPICA_DEFAULT).rstrip("/")
            _print_once_base(base)

            if _env_bool("F1GOAT_BLOCK_ERGAST", False) and ("ergast.com" in base):
                raise RuntimeError("F1GOAT_BLOCK_ERGAST=1: bloqueado ergast.com (no aplica a api.jolpi.ca)")

            p = (path or "").lstrip("/")
            if p.startswith("api/"):   # tolerar 'api/' inicial
                p = p[4:]
            url = f"{base}/{p}"
            return _http_json(url)
    ''')
    wr(NEW/"f1goat/http.py", base_http)
    wr(PATCH/"http.patch", udiff("/dev/null","", "f1goat/http.py", base_http))
else:
    src = rd(http_path)
    cp(http_path, ORIG/"f1goat/http.py")
    out = src

    # 1) default base → https
    out = re.sub(r'(_JOLPICA_DEFAULT\s*=\s*")[^"]+(")',
                 r'\1https://api.jolpi.ca/ergast\2', out, count=1)

    # 2) añade rate-limit helpers si no existen
    if "_RATE = float(os.getenv(\"F1GOAT_ERGAST_RATE\"" not in out:
        inject = textwrap.dedent('''

            _rate_last = []
            _RATE = float(os.getenv("F1GOAT_ERGAST_RATE", "3"))

            def _rate_limit():
                if _RATE <= 0: return
                import time
                now = time.monotonic(); window = 1.0
                global _rate_last
                _rate_last = [t for t in _rate_last if now - t < window]
                if len(_rate_last) >= _RATE:
                    delay = window - (now - _rate_last[0])
                    if delay > 0: time.sleep(delay)
                _rate_last.append(time.monotonic())

            def _upgrade(url: str) -> str:
                return url.replace("http://","https://",1) if url.startswith("http://") else url
        ''')
        out = out.replace("_printed_base = False", "_printed_base = False"+inject)

    # 3) endurecer _http_json: upgrade + backoff básico
    if "def _http_json(" in out:
        out = re.sub(
            r'def _http_json\([^)]*\):\n(.*?)\n(?=def |\Z)',
            lambda m: textwrap.dedent('''\
                def _http_json(url: str, timeout: float=15.0, max_redirects: int=3):
                    _rate_limit()
                    url = _upgrade(url)
                    headers = {
                        "User-Agent": f"F1GOAT/{os.getenv('F1GOAT_VERSION','dev')}",
                        "Accept": "application/json",
                    }
                    import urllib.request, urllib.error, json, time
                    tries = 0
                    while True:
                        req = urllib.request.Request(url, headers=headers)
                        try:
                            with urllib.request.urlopen(req, timeout=timeout) as r:
                                data = r.read().decode("utf-8","replace")
                                return json.loads(data)
                        except urllib.error.HTTPError as e:
                            if e.code in (301,302,303,307,308) and max_redirects>0:
                                loc = e.headers.get("Location")
                                if loc:
                                    from urllib.parse import urljoin
                                    url = _upgrade(urljoin(url, loc))
                                    max_redirects -= 1
                                    continue
                            if e.code in (429,500,502,503,504) and tries < 3:
                                time.sleep(0.5*(2**tries)); tries += 1; continue
                            raise
                        except Exception:
                            if tries < 3:
                                time.sleep(0.5*(2**tries)); tries += 1; continue
                            raise
            '''),
            out, flags=re.DOTALL, count=1
        )

    # 4) ergast_json: tolerar 'api/' y no bloquear api.jolpi.ca
    if "def ergast_json(" in out:
        out = re.sub(r'ergast_json\(path[^)]*\):\n(.*?)\n(?=def |\Z)',
                     textwrap.dedent('''\
                         def ergast_json(path: str):
                             base = os.getenv("F1GOAT_ERGAST_BASE", _JOLPICA_DEFAULT).rstrip("/")
                             _print_once_base(base)
                             if _env_bool("F1GOAT_BLOCK_ERGAST", False) and ("ergast.com" in base):
                                 raise RuntimeError("F1GOAT_BLOCK_ERGAST=1: bloqueado ergast.com (no aplica a api.jolpi.ca)")
                             p = (path or "").lstrip("/")
                             if p.startswith("api/"):
                                 p = p[4:]
                             url = f"{base}/{p}"
                             return _http_json(url)
                     '''),
                     out, flags=re.DOTALL, count=1)

    wr(NEW/"f1goat/http.py", out)
    wr(PATCH/"http.patch", udiff("f1goat/http.py", src, "f1goat/http.py", out))

# ---------- data_sources.py: enrutar a ergast_json sin reescribir todo ----------
ds = ROOT/"f1goat/data_sources.py"
if ds.exists():
    src = rd(ds); cp(ds, ORIG/"f1goat/data_sources.py"); out = src

    # Asegura import
    if "from .http import ergast_json" not in out:
        # Inserta tras el primer bloque de imports
        out = out.replace("\nimport pandas as pd", "\nimport pandas as pd\nfrom .http import ergast_json", 1)

    # Si existe helper _http_json_get, haz que use ergast_json para '/f1/'
    if "_http_json_get(" in out and "ergast_json(" not in out:
        out = out.replace(
            "def _http_json_get(url", 
            "def _http_json_get(url"
        )
        out = re.sub(
            r"def _http_json_get\(url:[^\)]*\):\n(.*?)\n(?=def |\Z)",
            textwrap.dedent('''\
                def _http_json_get(url: str, timeout: float=15.0):
                    try:
                        if '/f1/' in url:
                            path = 'f1/' + url.split('/f1/',1)[1]
                            return ergast_json(path)
                    except Exception:
                        pass
                    import urllib.request, json
                    req = urllib.request.Request(url, headers={"User-Agent":"F1GOAT/1.0","Accept":"application/json"})
                    with urllib.request.urlopen(req, timeout=timeout) as r:
                        return json.loads(r.read().decode("utf-8","replace"))
            '''),
            out, flags=re.DOTALL, count=1
        )
    else:
        # Si no existe, añadimos un helper seguro al final sin romper nada
        out = out.rstrip() + textwrap.dedent('''

            def _http_json_get(url: str, timeout: float=15.0):
                """Compat: si la URL es Ergast-compatible ('/f1/'), usa Jolpica; si no, urllib."""
                try:
                    if '/f1/' in url:
                        path = 'f1/' + url.split('/f1/',1)[1]
                        return ergast_json(path)
                except Exception:
                    pass
                import urllib.request, json
                req = urllib.request.Request(url, headers={"User-Agent":"F1GOAT/1.0","Accept":"application/json"})
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return json.loads(r.read().decode("utf-8","replace"))
        ''')

    wr(NEW/"f1goat/data_sources.py", out)
    wr(PATCH/"data_sources.patch", udiff("f1goat/data_sources.py", src, "f1goat/data_sources.py", out))

# ---------- cli.py: subcomando ingest (jolpica) sin romper backfill ----------
cli = ROOT/"f1goat/cli.py"
if cli.exists():
    src = rd(cli); cp(cli, ORIG/"f1goat/cli.py"); out = src
    # Asegurar import os
    if "import sys, argparse" in out and "import sys, argparse, os" not in out:
        out = out.replace("import sys, argparse", "import sys, argparse, os")

    # Añadir parser 'ingest' si no existe
    if '--source' not in out:
        out = re.sub(
            r'(p_back\s*=\s*sub\.add_parser\("backfill".*?\)\n(?:.*\n){0,30})',
            r'\1p_ing = sub.add_parser("ingest", help="Ingesta dirigida por fuente")\n'
            r'p_ing.add_argument("--seasons", required=True, help="Ej: 1950-1952 o 1950,1952")\n'
            r'p_ing.add_argument("--source", choices=["jolpica","fastf1","auto"], default="jolpica")\n'
            r'p_ing.add_argument("--rate", type=float, default=float(os.getenv("F1GOAT_ERGAST_RATE","3")))\n'
            r'p_ing.add_argument("--resume", action="store_true")\n',
            out, flags=re.DOTALL
        )

    # Añadir handler 'ingest'
    if 'args.cmd == "ingest"' not in out:
        out = re.sub(
            r'(if\s+args\.cmd\s*==\s*"backfill":\s*\n(?:.*\n)+?)\n',
            r'\1\n'
            r'    if args.cmd == "ingest":\n'
            r'        src = args.source\n'
            r'        os.environ.setdefault("F1GOAT_ERGAST_RATE", str(args.rate))\n'
            r'        txt = args.seasons.replace(" ","")\n'
            r'        years = []\n'
            r'        for part in txt.split(","):\n'
            r'            if "-" in part:\n'
            r'                a,b = part.split("-",1)\n'
            r'                years.extend(range(int(a), int(b)+1))\n'
            r'            elif part:\n'
            r'                years.append(int(part))\n'
            r'        y1, y2 = min(years), max(years)\n'
            r'        erg_only = (src == "jolpica")\n'
            r'        f1_only  = (src == "fastf1")\n'
            r'        return ingest_range(y1, y2, erg_only, f1_only)\n\n',
            out, flags=re.DOTALL
        )

    wr(NEW/"f1goat/cli.py", out)
    wr(PATCH/"cli.patch", udiff("f1goat/cli.py", src, "f1goat/cli.py", out))

print("[OK] Parches generados en:", PATCH)
