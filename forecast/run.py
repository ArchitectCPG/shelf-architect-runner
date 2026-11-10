"""One command: forecast.json -> workbook, dashboard docs, download parts, write batches (SOP v85 build 4).

Usage: python3 forecast/run.py clients/<id>.forecast.json [out_dir]
Default out_dir: forecast/out/<client_id>/. Stops on any formula error. Prints the headline and the batch list.
Then a session (Sonnet) sends out_dir/batches/*.json in order with db_write on the client instance, and runs
tools/numbers_audit.py on any copy that quotes forecast figures before writing it (numbers_audit_gate).
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import build, extract, emit

cfg_path = sys.argv[1]
cfg = json.load(open(cfg_path))
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "out", cfg["client_id"])
path, refs = build.build(cfg, out)
dash, _ = extract.extract(cfg, out)
man = emit.emit(cfg, out)
c = dash["dashboard"]["company"]
print(f"workbook {path}: 0 formula errors")
print(f"revenue {c['total_revenue']:,.0f} | spend {c['total_spend']:,.0f} ({c['spend_pct_of_revenue']*100:.1f}% of gross) | contribution {c['net_revenue']:,.0f}")
for m in man: print(f"  {m['batch']}: {m['bytes']:,} bytes -> {', '.join(m['paths'])}")
