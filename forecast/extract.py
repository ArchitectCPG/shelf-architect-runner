"""Recalculate a built workbook and turn it into the instance's forecast docs (SOP v85 build 4).

Usage: python3 forecast/extract.py clients/<id>.forecast.json out_dir
Reads <out_dir>/<file>.xlsx and refs.json from build.py. Recalculates with LibreOffice headless, counts formula
errors (any error stops the run), then writes dash_doc.json and sheets_doc.json in the shape the page renders.
"""
import json, sys, os, subprocess, shutil, tempfile
from openpyxl import load_workbook

ERRS = ("#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#N/A", "#NUM!", "#NULL!", "Err:")


def recalc(path):
    tmp = tempfile.mkdtemp()
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", tmp, path],
                   check=True, capture_output=True, timeout=180)
    out = os.path.join(tmp, os.path.basename(path))
    return out


def fmt(v, nf):
    nf = (nf or "").replace("\\", "").replace('"', "")
    pos = nf.split(";")[0]
    if v is None or v == "": return ""
    if isinstance(v, str): return v
    if isinstance(v, bool): return str(v)
    if isinstance(v, (int, float)):
        if v == 0 and nf.endswith(";-"): return "-"
        neg = v < 0; a = abs(v)
        if "%" in pos: s = f"{a*100:.1f}%"
        elif "$" in pos and "0.00" in pos: s = f"${a:,.2f}"
        elif "$" in pos: s = f"${a:,.0f}"
        elif "0.00x" in pos: s = f"{a:.2f}x"
        elif "0.00" in pos: s = f"{a:,.2f}"
        elif "0.0" in pos: s = f"{a:,.1f}"
        else: s = f"{a:,.0f}" if float(a).is_integer() else f"{a:,.2f}"
        return f"({s})" if neg else s
    return str(v)


def sheet_rows(V, name, freezeR, freezeC):
    ws = V[name]; maxc = ws.max_column; rows = []
    for r in range(1, ws.max_row + 1):
        rows.append([fmt(ws.cell(r, c).value, ws.cell(r, c).number_format) for c in range(1, maxc + 1)])
    while rows and not any(rows[-1]): rows.pop()
    align = []
    for c in range(1, maxc + 1):
        nums = sum(1 for r in range(1, ws.max_row + 1) if isinstance(ws.cell(r, c).value, (int, float)))
        align.append("r" if nums >= 2 and c > 3 else "l")
    return {"name": name, "rows": rows, "align": align, "freezeR": freezeR, "freezeC": freezeC}


def extract(cfg, out_dir):
    refs = json.load(open(os.path.join(out_dir, "refs.json")))
    src = os.path.join(out_dir, refs["file"])
    calc = recalc(src)
    V = load_workbook(calc, data_only=True)
    errors = []
    for ws in V.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith(ERRS):
                    errors.append(f"{ws.title}!{c.coordinate} {c.value}")
    if errors:
        raise SystemExit("formula errors: " + "; ".join(errors[:20]))
    shutil.copy(calc, src)   # keep the recalculated file as the download, so it opens with values

    O = V["Overall"]; R = V["Retailer Expansion"]; S = V["SKU Expansion"]; A = V["Assumptions"]
    ov = refs["overall"]; val = lambda ws, ref: ws[ref].value or 0
    tot = val(O, f"Q{ov['tot']}"); gross = val(O, ov["gross"])
    trade, mkt, spend = val(O, ov["trade"]), val(O, ov["mkt"]), val(O, ov["spend"])
    mon = lambda ws, row, c0: [round(ws.cell(row, c0 + i).value or 0, 2) for i in range(12)]
    brand_pct = gross / tot if tot else 0
    sanity_pct = round((val(O, ov["sanity_pct"]) or 0) * 100) if ov.get("sanity_pct") else None
    d = cfg["dashboard"]
    fill_note = lambda s: (s or "").replace("{sanity_pct}", str(sanity_pct))

    ex_trade = next(c for c in A.iter_rows(min_col=2, max_col=4) if c[0].value == cfg["existing_spend"]["label"])
    et, em = ex_trade[1].value, ex_trade[2].value
    cards = []
    for t, card in zip(refs["existing"], d.get("existing_cards", [])):
        W = V[t["tab"]]; tt = t["tot"]
        S_, U_, V_, G_ = (val(W, f"{c}{tt}") for c in "SUVW")
        tr_r, mk_r = (U_ / G_, V_ / G_) if G_ else (et, em)
        sp_r = (U_ + V_) / S_ if S_ else 0
        tl = card.get("trade_name", "Trade $"); ml = card.get("mkt_name", "Marketing $")
        cards.append({"key": card["key"], "label": card["label"], "current_revenue": round(S_, 2), "incremental_lift": 0,
                      "projected_revenue": round(S_, 2),
                      "categories": [{"name": f"{tl} ({refs['year_label']}, {tr_r*100:.0f}% of brand $)", "fy27_total": round(U_, 2)},
                                     {"name": f"{ml} ({refs['year_label']}, {mk_r*100:.0f}% of brand $)", "fy27_total": round(V_, 2)}],
                      "monthly_spend": [round(x * sp_r, 2) for x in mon(W, tt, 7)],
                      "total_spend": round(val(W, f"U{tt}") + val(W, f"V{tt}"), 2),
                      "spark_label": "Trade + Marketing / mo (flat, mature rates)", "budget": None, "no_zero_note": True,
                      "no_budget_note": fill_note(card.get("note"))})
    rt, st = refs["rx_tot"], refs["sx_tot"]
    ss = cfg["sku_stairstep"]
    rc, sc = d["retailer_card"], d["sku_card"]
    cards.append({"key": rc["key"], "label": rc["label"], "current_revenue": 0, "incremental_lift": round(val(R, f"AD{rt}"), 2), "projected_revenue": round(val(R, f"AD{rt}"), 2),
                  "categories": [{"name": f"Trade $ ({refs['year_label']}, tier model)", "fy27_total": round(val(R, f"AE{rt}"), 2)},
                                 {"name": f"Marketing $ ({refs['year_label']}, tier model)", "fy27_total": round(val(R, f"AF{rt}"), 2)}],
                  "monthly_spend": mon(R, rt, 18), "total_spend": round(val(R, f"AE{rt}") + val(R, f"AF{rt}"), 2),
                  "spark_label": f"Monthly incremental revenue ({refs['months'][0][:3]}-{refs['months'][-1][:3]}), ramp not spend", "budget": None, "no_zero_note": True, "no_budget_note": fill_note(rc.get("note"))})
    cards.append({"key": sc["key"], "label": sc["label"], "current_revenue": 0, "incremental_lift": round(val(S, f"X{st}"), 2), "projected_revenue": round(val(S, f"X{st}"), 2),
                  "categories": [{"name": f"Trade $ ({refs['year_label']}, new-item {ss['ni_trade']*100:.0f}%)", "fy27_total": round(val(S, f"Y{st}"), 2)},
                                 {"name": f"Marketing $ ({refs['year_label']}, new-item {ss['ni_mkt']*100:.0f}%)", "fy27_total": round(val(S, f"Z{st}"), 2)}],
                  "monthly_spend": mon(S, st, 12), "total_spend": round(val(S, f"Y{st}") + val(S, f"Z{st}"), 2),
                  "spark_label": f"Monthly incremental revenue ({refs['months'][0][:3]}-{refs['months'][-1][:3]}), ramp not spend", "budget": None, "no_zero_note": True, "no_budget_note": fill_note(sc.get("note"))})

    dash = {"as_of": cfg.get("as_of"), "revenue_label": d.get("revenue_label", f"{refs['year_label']} Total Revenue (retail $ at shelf)"),
            "revenue_subs": [{"label": d.get("gross_label", "Gross sales"), "value": round(gross, 2), "label2": "Net sales", "value2": round(val(O, ov["net"]), 2)},
                             {"label": "COGS", "value": round(val(O, ov["cogs"]), 2), "label2": "Gross profit", "value2": round(val(O, ov["gp"]), 2)}],
            "net_label": "Contribution Margin", "spend_pct_label": "Spend % of Gross Sales",
            "company": {"total_revenue": round(tot, 2), "total_trade": round(trade, 2), "total_marketing": round(mkt, 2), "total_spend": round(spend, 2),
                        "net_revenue": round(val(O, ov["cm"]), 2), "spend_pct_of_revenue": round(spend / gross, 4) if gross else 0, "total_brand_love": 0},
            "flags": [], "footer_note": fill_note(d.get("footer_note")), "retailers": cards}
    names = ["Overall", "Assumptions", "Current State"] + [t["tab"] for t in refs["existing"]] + ["Retailer Expansion", "SKU Expansion"]
    sheets = [sheet_rows(V, n, 5 if n != "Assumptions" else 4, 3 if n in ("Retailer Expansion", "SKU Expansion") else 2) for n in names]
    cid, fk = cfg["client_id"], cfg.get("file_key", "fc_v1")
    lab = f"Forecast & Budget {cfg.get('version', 'v1')}"
    dash_doc = {"client_id": cid, "file_key": fk, "label": lab, "order": 1, "dashboard": dash}
    sheets_doc = {"client_id": cid, "file_key": fk + "_sheets", "label": "Model tabs", "order": 2, "sheets": sheets}
    json.dump(dash_doc, open(os.path.join(out_dir, "dash_doc.json"), "w"), separators=(",", ":"))
    json.dump(sheets_doc, open(os.path.join(out_dir, "sheets_doc.json"), "w"), separators=(",", ":"))
    return dash_doc, sheets_doc


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    dd, _ = extract(cfg, sys.argv[2])
    print(json.dumps(dd["dashboard"]["company"]))
