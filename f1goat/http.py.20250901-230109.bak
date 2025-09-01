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
