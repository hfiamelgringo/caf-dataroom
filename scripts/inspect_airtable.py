"""Ad-hoc Airtable schema inspector. Run via: conda run -n caf python scripts/inspect_airtable.py"""
import os
import sys
from pathlib import Path

# Load keys.env
env_path = Path(__file__).resolve().parent.parent / "keys.env"
for line in env_path.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

from pyairtable import Api

api = Api(os.environ["AIRTABLE_PAT"])
base = api.base("appVMgNUokH0882lO")
schema = base.schema()

targets = sys.argv[1:] or ["Meeting Notes", "People", "Countries"]

for tname in targets:
    try:
        t = next(x for x in schema.tables if x.name == tname)
    except StopIteration:
        print(f"!! Table not found: {tname}")
        continue
    print(f"=== {t.name} ({t.id}) ===")
    for f in t.fields:
        print(f"  {f.name:35s} {f.type}")
    print()
