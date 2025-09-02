import json, os, sys, urllib.request, urllib.error, urllib.parse

_JOLPICA_DEFAULT = "https://api.jolpi.ca/ergast"
_printed_base = False

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
def _http_json_no_redirect(url: str, timeout: float=15.0):
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent":"F1GOAT/1.0 (+local)","Accept":"application/json"})
    try:
        with opener.open(req, timeout=timeout) as r:
            data = r.read().decode("utf-8","replace")
            return json.loads(data)
    except urllib.error.HTTPError as he:
        # Propagamos para que ergast_json maneje 301/302
        raise he

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
def _rewrite_to_api_jolpi(location: str) -> str:
    try:
        u = urllib.parse.urlparse(location)
        path = u.path or ""
        qs = ("?"+u.query) if u.query else ""
        # normaliza /api/xxx → /ergast/xxx
        if "/api/" in path:
            path = path.split("/api/",1)[1]
        path = path.lstrip("/")
        return f"http://api.jolpi.ca/ergast/{path}{qs}"
    except Exception:
        loc = location
        if loc.startswith("/api/"):
            loc = loc[5:]
        return "http://api.jolpi.ca/ergast/" + loc.lstrip("/")
