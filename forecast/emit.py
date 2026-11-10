"""Turn a built forecast into db_write batches for the client instance (SOP v85 build 4).

Usage: python3 forecast/emit.py clients/<id>.forecast.json out_dir
Writes <out_dir>/batches/NN_<what>.json, each a list of db_write ops under the ~100 KB request ceiling, and
<out_dir>/manifest.json listing them. The session sends each batch with db_write on the client's instance; an op
on a doc that already exists needs ifVersion from a db_get first (the write is refused otherwise, nothing lost).
"""
import json, sys, os, base64

PART = 90_000   # base64 chars per forecast_files part; keeps one op per request under the write ceiling


def emit(cfg, out_dir):
    refs = json.load(open(os.path.join(out_dir, "refs.json")))
    cid, fk = cfg["client_id"], cfg.get("file_key", "fc_v1")
    dash = json.load(open(os.path.join(out_dir, "dash_doc.json")))
    sheets = json.load(open(os.path.join(out_dir, "sheets_doc.json")))
    b64 = base64.b64encode(open(os.path.join(out_dir, refs["file"]), "rb").read()).decode()
    parts = [b64[i:i + PART] for i in range(0, len(b64), PART)]
    tabs = cfg.get("tabs", {})
    fc_block = {"forecast": {
        "tab_order": [fk, fk + "_sheets", "retail-marketing"],
        "files": [
            {"key": fk, "kind": "dashboard", "tab_label": tabs.get("dashboard", "Forecast and Budget"), "note": tabs.get("dashboard_note", ""),
             "dl_name": refs["file"], "dl_parts": len(parts)},
            {"key": fk + "_sheets", "kind": "sheet", "tab_label": tabs.get("sheets", "Model tabs"), "note": tabs.get("sheets_note", "")},
            {"key": "retail-marketing", "kind": "image", "tab_label": tabs.get("image", "Retail Marketing"), "img_doc": "retail-marketing-framework",
             "note": tabs.get("image_note", "")}],
        "built_by": "forecast runner (shelf-architect-runner/forecast), " + str(cfg.get("as_of"))}}
    batches = [
        ("01_dashboard", [{"op": "set", "path": f"forecast_sheets/{cid}__{fk}", "data": dash}]),
        ("02_sheets", [{"op": "set", "path": f"forecast_sheets/{cid}__{fk}_sheets", "data": sheets}]),
    ]
    for i, p in enumerate(parts):
        batches.append((f"{3+i:02d}_file_part{i}", [{"op": "set", "path": f"forecast_files/{cid}__{fk}__{i}",
                        "data": {"client_id": cid, "file_key": fk, "part": i, "parts": len(parts), "b64": p, "file_name": refs["file"]}}]))
    batches.append((f"{3+len(parts):02d}_client_config", [{"op": "merge", "path": f"client_config/{cid}", "data": fc_block}]))
    bdir = os.path.join(out_dir, "batches"); os.makedirs(bdir, exist_ok=True)
    man = []
    for name, ops in batches:
        s = json.dumps(ops, separators=(",", ":"))
        if len(s) > 120_000:
            raise SystemExit(f"{name} is {len(s)} bytes, over the write ceiling; split it")
        open(os.path.join(bdir, name + ".json"), "w").write(s)
        man.append({"batch": name, "bytes": len(s), "paths": [o["path"] for o in ops]})
    json.dump({"client_id": cid, "file_key": fk, "workbook": refs["file"], "parts": len(parts), "batches": man},
              open(os.path.join(out_dir, "manifest.json"), "w"), indent=1)
    return man


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    for m in emit(cfg, sys.argv[2]): print(m["batch"], m["bytes"], m["paths"])
