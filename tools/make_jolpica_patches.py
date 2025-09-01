import os, re, pathlib

ROOT = pathlib.Path(".")
ORIG = pathlib.Path("/tmp/jolpica/orig")
NEW  = pathlib.Path("/tmp/jolpica/new")
PATCHES = pathlib.Path("/tmp/jolpica/patches")
ORIG.mkdir(parents=True, exist_ok=True)
NEW.mkdir(parents=True, exist_ok=True)
PATCHES.mkdir(parents=True, exist_ok=True)

def read(p): return pathlib.Path(p).read_text(encoding="utf-8")
def write_tmp(relpath, content):
    dst = NEW / relpath
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")

def copy_orig(relpath):
    src = ROOT / relpath
    dst = ORIG / relpath
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

# --- http.py (nuevo) ---
HTTP_NEW = r'''\
import json, os, sys, urllib.request

_JOLPICA_DEFAULT = "http://api.jolpi.ca/ergast"
_printed_base = False

def _env_bool(name: str, default: bool=False) -> bool:
    v = os.getenv(name, "")
    if not v:
        return default
    return v.lower() in ("1","true","yes","on")

def _print_once_base(base: str):
    global _printed_base
    if not _printed_base:
        print(f"[F1GOAT] Usando Jolpica-F1: {base}", file=sys.stderr)
        _printed_base = True

def _toggle_scheme(url: str) -> str:
    if url.startswith("https://"):
        return "http://" + url[len("https://"):]
    if url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url

def _http_json(url: str, timeout: float=15.0):
    req = urllib.request.Request(
        url,
        headers={"User-Agent":"F1GOAT/1.0 (+local)","Accept":"application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8","replace"))

def ergast_json(path: str):
    """
    Descarga JSON de una ruta Ergast-compatible usando una base configurable.
    - base por defecto: http://api.jolpi.ca/ergast
    - respeta F1GOAT_BLOCK_ERGAST
    - fallback https<->http si el primer intento falla.
    """
    base = os.getenv("F1GOAT_ERGAST_BASE", _JOLPICA_DEFAULT).rstrip("/")
    _print_once_base(base)

    if os.getenv("F1GOAT_BLOCK_ERGAST","").lower() in ("1","true","yes") and "ergast.com" in base:
        raise RuntimeError("F1GOAT_BLOCK_ERGAST=1: bloqueado acceso a ergast.com")

    path = path.lstrip("/")
    url = f"{base}/{path}"
    try:
        return _http_json(url)
    except Exception as e1:
        alt = _toggle_scheme(url)
        if alt != url:
            try:
                return _http_json(alt)
            except Exception as e2:
                raise RuntimeError(f"HTTP fail for {url} and {alt}: {e1} // {e2}")
        raise RuntimeError(f"HTTP fail for {url}: {e1}")
'''

# Guardar http.py (nuevo) solo en NEW
write_tmp("f1goat/http.py", HTTP_NEW)

# --- data_sources.py (ajuste mínimo y seguro) ---
ds_path = "f1goat/data_sources.py"
copy_orig(ds_path)
s = read(ds_path)

# asegurar import os
if "import os" not in s:
    s = s.replace("from typing", "import os\nfrom typing")

# asegurar import ergast_json
if "from .http import ergast_json" not in s:
    # intenta insertar tras el primer bloque de imports
    m = re.search(r"^(?:import .*\n|from .+ import .*\n)+", s, flags=re.MULTILINE)
    if m:
        s = s[:m.end()] + "from .http import ergast_json\n" + s[m.end():]
    else:
        s = "from .http import ergast_json\n" + s

# Si existe _http_json_get, sustituimos su CUERPO por un wrapper a ergast_json
m = re.search(r"def\s+_http_json_get\s*\([^)]*\):\s*\n", s)
if m:
    start = m.end()
    # Buscar fin de función por dedent (otra def o EOF)
    m2 = re.search(r"\ndef\s+\w", s[start:])
    end = start + (m2.start() if m2 else len(s) - start)
    new_body = (
        "    \"\"\"Wrapper: redirige URLs Ergast a la base configurada y usa ergast_json.\"\"\"\n"
        "    url = args[0] if (args:=()) or True else None  # compat\n"
        "    # Extraer la parte '/f1/...' si es Ergast-compatible\n"
        "    try:\n"
        "        u = url\n"
        "        p = None\n"
        "        if '/f1/' in u:\n"
        "            p = 'f1/' + u.split('/f1/',1)[1]\n"
        "        elif u.rstrip('/').ends_with('/f1'):\n"
        "            p = 'f1'\n"
        "        if p:\n"
        "            return ergast_json(p)\n"
        "    except Exception:\n"
        "        pass\n"
        "    # Si no parece Ergast, intenta fetch directo (conmutando esquema si falla)\n"
        "    from urllib.error import URLError\n"
        "    try:\n"
        "        return __orig_http_json_get(url)\n"
        "    except Exception:\n"
        "        alt = 'http://' + url[len('https://'):] if url.startswith('https://') else 'https://' + url[len('http://'):] if url.startswith('http://') else url\n"
        "        if alt != url:\n"
        "            return __orig_http_json_get(alt)\n"
        "        raise\n"
    )
    # conservar la firma original y crear respaldo del original si no existe
    if "__orig_http_json_get" not in s:
        s = s.replace("def _http_json_get", "def __orig_http_json_get", 1)
        # reintroducimos el wrapper con el nombre original
        insert_at = s.find("def __orig_http_json_get")
        # tras la función original, añadimos el wrapper
        m3 = re.search(r"\ndef\s+\w", s[insert_at+1:])
        inspos = insert_at + 1 + (m3.start() if m3 else len(s)-(insert_at+1))
        s = s[:inspos] + "\n\ndef _http_json_get(url: str, timeout: float=15.0):\n" + new_body + s[inspos:]
else:
    # No existe _http_json_get: añadimos helper minimalista sin tocar llamadas
    s += (
        "\n\ndef _http_json_get(url: str, timeout: float=15.0):\n"
        "    \"\"\"Helper de compatibilidad: usa Jolpica si la URL es Ergast-compatible.\"\"\"\n"
        "    try:\n"
        "        if '/f1/' in url:\n"
        "            path = 'f1/' + url.split('/f1/',1)[1]\n"
        "            return ergast_json(path)\n"
        "    except Exception:\n"
        "        pass\n"
        "    # fallback genérico\n"
        "    import urllib.request, json\n"
        "    req = urllib.request.Request(url, headers={'User-Agent':'F1GOAT/1.0','Accept':'application/json'})\n"
        "    with urllib.request.urlopen(req, timeout=timeout) as r:\n"
        "        return json.loads(r.read().decode('utf-8','replace'))\n"
    )

write_tmp(ds_path, s)

# --- cli.py (añadir subcomando ingest) ---
cli_path = "f1goat/cli.py"
copy_orig(cli_path)
c = read(cli_path)

# asegurar imports os
if "import os" not in c:
    c = c.replace("import sys, argparse", "import sys, argparse, os")

# añadir parser ingest tras parser backfill (si no existe ya)
if "--source" not in c:
    c = re.sub(
        r'(p_back\s*=\s*sub\.add_parser\("backfill".*?\)\n(?:.*\n){0,40})',
        r'\1p_ing = sub.add_parser("ingest", help="Ingesta dirigida por fuente")\n'
        r'p_ing.add_argument("--seasons", required=True, help="Ej: 1950-1952 o 1950")\n'
        r'p_ing.add_argument("--source", choices=["jolpica","ergast","fastf1","auto"], default="auto")\n',
        c, flags=re.DOTALL
    )

# añadir handler ingest (si no existe)
if 'args.cmd == "ingest"' not in c:
    c = re.sub(
        r'(if\s+args\.cmd\s*==\s*"backfill":\s*\n(?:.*\n)+?)\n',
        r'\1\n'
        r'    if args.cmd == "ingest":\n'
        r'        src = args.source\n'
        r'        txt = args.seasons.strip()\n'
        r'        if "-" in txt:\n'
        r'            a,b = txt.split("-",1)\n'
        r'            y1, y2 = int(a), int(b)\n'
        r'        else:\n'
        r'            y1 = y2 = int(txt)\n'
        r'        erg_only = (src in ("jolpica","ergast"))\n'
        r'        f1_only  = (src == "fastf1")\n'
        r'        if src == "jolpica":\n'
        r'            base = os.getenv("F1GOAT_ERGAST_BASE", "http://api.jolpi.ca/ergast")\n'
        r'            os.environ.setdefault("F1GOAT_ERGAST_BASE", base)\n'
        r'            print(f"[F1GOAT] Ingest (jolpica): usando base {base}", file=sys.stderr)\n'
        r'        from .data_sources import ingest_range\n'
        r'        return ingest_range(y1, y2, erg_only, f1_only)\n\n',
        c, flags=re.DOTALL
    )

write_tmp(cli_path, c)

print("[MAKE] NEW listo en /tmp/jolpica/new y ORIG en /tmp/jolpica/orig")
