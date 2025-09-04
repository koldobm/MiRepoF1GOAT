from f1goat.storage import _connect
import sys
con=_connect()
sql = sys.stdin.read() if len(sys.argv)==1 else " ".join(sys.argv[1:])
cur = con.execute(sql)
try:
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    if cols:
        print("\t".join(cols))
        for r in rows:
            print("\t".join("" if v is None else f"{v}" for v in r))
except Exception:
    pass
