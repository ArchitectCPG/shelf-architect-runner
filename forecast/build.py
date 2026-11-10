"""Generic Forecast & Budget workbook builder (SOP v85 build 4).

Usage: python3 forecast/build.py clients/<id>.forecast.json out_dir
Writes <out_dir>/<Client>_Forecast_and_Budget_<version>.xlsx and refs.json (cell addresses extract.py reads).
Every client value comes from the config; nothing client-specific lives in this file.
"""
import json, sys, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

INK, BODY, BROWN, GOLD, GREIGE, CARD = "212121", "595959", "5D3523", "F7BF1D", "D6D4C6", "F4F3F1"
F = lambda **k: Font(name="Arial", size=k.pop("size", 10), **k)
fill = lambda c: PatternFill("solid", start_color=c)
thin = Side(style="thin", color=GREIGE)
BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
USD = '$#,##0;($#,##0);"-"'
PCT = '0.0%;(0.0%);"-"'
NUM = '#,##0;(#,##0);"-"'
DEC = '#,##0.00;(#,##0.00);"-"'
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def month_labels(y, m):
    out = []
    for i in range(12):
        mm = (m - 1 + i) % 12
        yy = y + (m - 1 + i) // 12
        out.append(f"{MON[mm]}-{str(yy)[-2:]}")
    return out


def build(cfg, out_dir):
    fr = cfg["frame"]
    MONTHS = month_labels(fr["start_year"], fr.get("start_month", 1))
    YL = fr.get("year_label", str(fr["start_year"]))
    CN = cfg["client_name"]
    VER = cfg.get("version", "v1")
    LOVE = cfg.get("love_label", "Pack Love")  # Steve 2026-11-10: always Pack Love; Can Love only for canned beverage clients
    wb = Workbook(); wb.remove(wb.active)

    def sheet(name, title, sub=None, widths=None):
        ws = wb.create_sheet(name[:31])
        ws.sheet_view.showGridLines = False
        ws["B2"] = title; ws["B2"].font = F(size=14, bold=True, color=INK)
        if sub:
            ws["B3"] = sub; ws["B3"].font = F(italic=True, color=BODY); ws["B3"].alignment = Alignment(wrap_text=False)
        for i, w in (widths or {}).items():
            ws.column_dimensions[i].width = w
        ws.column_dimensions["A"].width = 2
        return ws

    def bar(ws, r, text, c1=2, c2=12):
        for c in range(c1, c2 + 1):
            ws.cell(r, c).fill = fill(BROWN)
        ws.cell(r, c1, text).font = F(bold=True, color="FFFFFF")

    def hdr(ws, r, vals, c1=2):
        for i, v in enumerate(vals):
            c = ws.cell(r, c1 + i, v)
            c.font = F(bold=True, color=INK); c.fill = fill(GREIGE)
            c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center" if i else "left")
            c.border = BOX
        ws.row_dimensions[r].height = 30

    def put(ws, ref, v, fmt=None, kind="calc", bold=False, note=None):
        c = ws[ref]; c.value = v
        color = {"input": "0000FF", "calc": "000000", "link": "008000", "text": INK, "note": BODY}[kind]
        c.font = F(color=color, bold=bold, italic=(kind == "note"))
        if fmt: c.number_format = fmt
        if kind == "input" and note == "gold": c.fill = fill(GOLD)
        c.border = BOX if kind != "note" else Border()
        return c

    q = lambda s: "'" + s.replace("'", "''") + "'"   # sheet name for formulas
    refs = {"months": MONTHS, "year_label": YL}

    # ------------------------------------------------ Read Me
    rm = sheet("Read Me", f"{cfg.get('client_full_name', CN)}: Forecast & Budget {VER} ({fr['label']})", widths={"B": 26, "C": 110})
    for i, (x, y) in enumerate(cfg.get("readme", [])):
        r = 4 + i
        rm.cell(r, 2, x).font = F(bold=True, color=INK); rm.cell(r, 3, y).font = F(color=BODY)
        rm.cell(r, 3).alignment = Alignment(wrap_text=True, vertical="top"); rm.cell(r, 2).alignment = Alignment(vertical="top")
        rm.row_dimensions[r].height = 42

    # ------------------------------------------------ Assumptions
    A = sheet("Assumptions", f"{CN}: Forecast & Budget {VER}: Assumptions (control panel)",
              "Change a gold cell and every tab recomputes. Nothing downstream is typed.",
              widths={"B": 46, "C": 13, "D": 13, "E": 11, "F": 12, "G": 12, "H": 70})
    a = {}
    AS = "Assumptions"
    r = 5
    bar(A, r, cfg.get("tiers_title", "RETAILER TIER ASSUMPTIONS"), 2, 8); r += 1
    hdr(A, r, ["Tier (code on Retailer Expansion)", "Trade % of gross sales", "Marketing % of gross sales", "Hit rate", f"Gate month # (1 = {MONTHS[0]})", "SKUs placed per new door", "What the tier is"]); r += 1
    t0 = r
    for t in cfg["tiers"]:
        put(A, f"B{r}", t["code"], kind="text")
        for col, k in zip("CDE", ("trade", "mkt", "hit")):
            put(A, f"{col}{r}", t[k], PCT, "input", note="gold")
        put(A, f"F{r}", t["gate"], NUM, "input"); put(A, f"G{r}", t["skus"], NUM, "input"); put(A, f"H{r}", t.get("note", ""), kind="note")
        r += 1
    t1 = r - 1
    for k, col in (("tier", "B"), ("trade", "C"), ("mkt", "D"), ("hit", "E"), ("gate", "F"), ("skus", "G")):
        a[k] = f"{AS}!${col}${t0}:${col}${t1}"
    r += 1
    ex = cfg["existing_spend"]
    put(A, f"B{r}", ex["label"], kind="text")
    put(A, f"C{r}", ex["trade"], PCT, "input", note="gold"); put(A, f"D{r}", ex["mkt"], PCT, "input", note="gold")
    put(A, f"H{r}", ex.get("note", ""), kind="note")
    a["ex_trade"], a["ex_mkt"] = f"{AS}!$C${r}", f"{AS}!$D${r}"
    r += 2
    tm = cfg["timing"]
    bar(A, r, "TIMING: a review win is not a ship date", 2, 8); r += 1
    put(A, f"B{r}", "Ship lag after a review win (months)", kind="text"); put(A, f"C{r}", tm["lag"], NUM, "input"); put(A, f"H{r}", tm.get("lag_note", ""), kind="note")
    a["lag"] = f"{AS}!$C${r}"; r += 1
    put(A, f"B{r}", "Default pitch month # (open review)", kind="text"); put(A, f"C{r}", tm["pitch"], NUM, "input"); put(A, f"H{r}", tm.get("pitch_note", ""), kind="note")
    a["pitch"] = f"{AS}!$C${r}"; r += 2
    ss = cfg["sku_stairstep"]
    bar(A, r, "SKU STAIRSTEP (new items)", 2, 8); r += 1
    put(A, f"B{r}", "First new-item launch month #", kind="text"); put(A, f"C{r}", ss["first"], NUM, "input", note="gold"); put(A, f"H{r}", ss.get("first_note", ""), kind="note"); a["first"] = f"{AS}!$C${r}"; r += 1
    put(A, f"B{r}", "Cadence between new SKUs (months)", kind="text"); put(A, f"C{r}", ss["cadence"], NUM, "input"); a["cad"] = f"{AS}!$C${r}"; r += 1
    put(A, f"B{r}", "New-item trade / slotting % of gross sales", kind="text"); put(A, f"C{r}", ss["ni_trade"], PCT, "input", note="gold"); put(A, f"H{r}", ss.get("ni_trade_note", ""), kind="note"); a["ni_trade"] = f"{AS}!$C${r}"; r += 1
    put(A, f"B{r}", "New-item marketing % of gross sales", kind="text"); put(A, f"C{r}", ss["ni_mkt"], PCT, "input", note="gold"); a["ni_mkt"] = f"{AS}!$C${r}"; r += 2
    w = cfg["waterfall"]
    bar(A, r, f"MARGIN WATERFALL ({w['retailer']*100:.0f} / {w['distributor']*100:.0f} / {w['trade']*100:.0f}, {w['gross']*100:.0f}% brand gross)", 2, 8); r += 1
    wr = r
    for lab, v in [("Retailer margin", w["retailer"]), (w.get("distributor_label", "Distributor margin"), w["distributor"]), ("Trade", w["trade"]), ("Target brand gross margin", w["gross"])]:
        put(A, f"B{r}", lab, kind="text"); put(A, f"C{r}", v, PCT, "input"); r += 1
    put(A, f"B{r}", "COGS ceiling as % of SRP", kind="text"); put(A, f"C{r}", f"=(1-C{wr})*(1-C{wr+1})*(1-C{wr+2})*(1-C{wr+3})", PCT); put(A, f"H{r}", w.get("cogs_note", "A target, not a quote. Replace with real COGS per SKU."), kind="note")
    a["cogs"] = f"{AS}!$C${r}"; r += 1
    put(A, f"B{r}", "Brand revenue (gross sales) as % of retail $", kind="text"); put(A, f"C{r}", f"=(1-C{wr})*(1-C{wr+1})", PCT)
    a["brand"] = f"{AS}!$C${r}"; r += 2
    bar(A, r, "NEW-DOOR / NEW-SKU RAMP: % of mature run-rate by months since launch", 2, 8); r += 1
    hdr(A, r, ["", "Months 1 to 3", "Months 4 to 6", "Months 7+"]); r += 1
    put(A, f"B{r}", "Ramp", kind="text")
    for c, v in zip("CDE", cfg.get("ramp", [0.4, 0.7, 1.0])):
        put(A, f"{c}{r}", v, PCT, "input")
    a["r1"], a["r2"], a["r3"] = f"{AS}!$C${r}", f"{AS}!$D${r}", f"{AS}!$E${r}"; r += 2

    bar(A, r, "LINES: price, velocity and COGS (gold = placeholder until scans)", 2, 8); r += 1
    hdr(A, r, ["Line", "SRP", "Mature u/s/w per SKU", "COGS / unit", "Rate $/door/SKU/yr", "", "Basis"]); r += 1
    l0 = r
    lines = cfg["lines"]
    for ln in lines:
        put(A, f"B{r}", ln["name"], kind="text")
        put(A, f"C{r}", ln["srp"], '$#,##0.00', "input", note="gold")
        put(A, f"D{r}", ln["usw"], DEC, "input", note="gold")
        put(A, f"E{r}", ln["cogs"], '$#,##0.00', "input", note="gold")
        put(A, f"F{r}", f"=C{r}*D{r}*52", USD)
        put(A, f"H{r}", " | ".join(x for x in (ln.get("srp_note"), ln.get("usw_note"), ln.get("cogs_note")) if x), kind="note")
        a[f"line:{ln['name']}"] = r
        r += 1
    l1 = r - 1
    a["ln_name"], a["ln_srp"], a["ln_usw"], a["ln_cogs"], a["ln_rate"] = (f"{AS}!${c}${l0}:${c}${l1}" for c in "BCDEF")
    lref = lambda name, col: f"{AS}!${col}${a['line:' + name]}"
    r += 1
    put(A, f"B{r}", ss.get("usw_label", "New-item velocity, u/s/w (mature)"), kind="text"); put(A, f"C{r}", ss["usw"], DEC, "input", note="gold"); put(A, f"H{r}", ss.get("usw_note", ""), kind="note")
    a["newusw"] = f"{AS}!$C${r}"; r += 2

    bar(A, r, "EXISTING ACCOUNTS (doors)", 2, 8); r += 1
    for e in cfg["existing"]:
        if e.get("kind") == "flat":
            # Flat-dollar account (marketplace or wholesale with no door count): brand $ in, its own waterfall and spend rates.
            acct = e["account"]
            for key, lab, v, fm, nt in (("gross", e.get("gross_label", f"{acct}: brand $ per year (what the brand invoices)"), e["gross"], USD, e.get("gross_note", "")),
                                        ("bf", e.get("bf_label", f"{acct}: brand $ as % of retail $"), e["brand_factor"], PCT, e.get("bf_note", "")),
                                        ("tr", e.get("trade_label", f"{acct}: trade % of brand $"), e["trade"], PCT, e.get("trade_note", "")),
                                        ("mk", e.get("mkt_label", f"{acct}: marketing % of brand $"), e["mkt"], PCT, e.get("mkt_note", ""))):
                put(A, f"B{r}", lab, kind="text"); put(A, f"C{r}", v, fm, "input", note="gold"); put(A, f"H{r}", nt, kind="note")
                a[f"{key}:{acct}"] = f"{AS}!$C${r}"; r += 1
            continue
        put(A, f"B{r}", e.get("doors_label", e["account"] + " doors"), kind="text"); put(A, f"C{r}", e["doors"], NUM, "input", note="gold"); put(A, f"H{r}", e.get("doors_note", ""), kind="note")
        a["doors:" + e["account"]] = f"{AS}!$C${r}"; r += 1
    san = cfg.get("sanity")
    if san:
        put(A, f"B{r}", san["label"], kind="text"); put(A, f"C{r}", san["value"], USD, "input", note="gold"); put(A, f"H{r}", san.get("note", ""), kind="note")
        a["sanity"] = f"{AS}!$C${r}"; r += 1
    mr = cfg.get("marketing_return")
    if mr:
        # Steve 2026-11-10, SA default: marketing $ comes back as incremental retail $ at shelf (SRP basis), on top of the velocity base.
        r += 1; bar(A, r, "MARKETING RETURN", 2, 8); r += 1
        put(A, f"B{r}", mr.get("label", "Marketing return: retail $ at shelf per $1 of marketing"), kind="text"); put(A, f"C{r}", mr["ratio"], '0.00"x"', "input", note="gold")
        put(A, f"H{r}", mr.get("note", "Incremental to the velocity base. Spread by month in line with base revenue. Carries the same waterfall and blended COGS; no trade on top."), kind="note")
        a["mret"] = f"{AS}!$C${r}"; r += 1
    r += 1
    bar(A, r, f"{YL} CALENDAR", 2, 14); r += 1
    for i, m in enumerate(MONTHS):
        put(A, f"{L(3+i)}{r}", i + 1, NUM); put(A, f"{L(3+i)}{r+1}", m, kind="text")
    put(A, f"B{r}", "Month #", kind="text"); put(A, f"B{r+1}", "Month", kind="text"); r += 3

    ro = cfg.get("rollout")
    drops = []
    if ro:
        bar(A, r, ro.get("title", "ROLLOUT"), 2, 8); r += 1
        for d in ro["drops"]:
            put(A, f"B{r}", d["label"], kind="text"); put(A, f"C{r}", d["month"], NUM, "input", note="gold"); put(A, f"H{r}", d.get("note", ""), kind="note"); mref = f"{AS}!$C${r}"; r += 1
            put(A, f"B{r}", d["skus_label"], kind="text"); put(A, f"C{r}", d["skus"], NUM, "input", note="gold"); put(A, f"H{r}", d.get("skus_note", ""), kind="note"); sref = f"{AS}!$C${r}"; r += 1
            drops.append((mref, sref))
        put(A, f"B{r}", ro["others_label"], kind="text"); put(A, f"C{r}", ro["others"], NUM, "input", note="gold"); put(A, f"H{r}", ro.get("others_note", ""), kind="note")
        a["others"] = f"{AS}!$C${r}"; r += 2
    put(A, f"B{r}", "Trade and marketing % apply to gross sales (what the brand invoices), not retail $ at shelf.", kind="note")
    A.freeze_panes = "C5"

    # ------------------------------------------------ Existing account detail tabs
    ex_tabs = []
    for e in cfg["existing"]:
        tab = e.get("tab", e["account"])[:31]
        W = sheet(tab, e.get("title", f"{CN}: {e['account']} (Current State detail)"), e.get("sub"),
                  widths={"B": 30, "C": 9, "D": 11, "E": 10, "F": 9})
        for i in range(12): W.column_dimensions[L(7 + i)].width = 11
        for c in "STUVW": W.column_dimensions[c].width = 13
        flat = e.get("kind") == "flat"
        hdr(W, 5, ["SKU on shelf", "SRP", "U/S/W override", "U/S/W used", "Doors"] + MONTHS + [f"{YL} Total (retail $)", "Run-rate / yr", "Trade $", "Marketing $", "Gross sales (brand $)"])
        if flat:
            acct = e["account"]; g, bf, tr_, mk_ = (a[f"{k}:{acct}"] for k in ("gross", "bf", "tr", "mk"))
            rows = e.get("skus") or [e.get("row_label", acct)]
            share = 1 / len(rows)
            for i, b in enumerate(rows):
                rr = 6 + i
                put(W, f"B{rr}", b, kind="text")
                put(W, f"C{rr}", f"={lref(e['line'], 'C')}", '$#,##0.00', "link")
                for m in range(12):
                    put(W, f"{L(7+m)}{rr}", f"={g}/{bf}/12*{share}", USD)
                put(W, f"S{rr}", f"=SUM(G{rr}:R{rr})", USD)
                put(W, f"T{rr}", f"=S{rr}", USD)
                put(W, f"U{rr}", f"=S{rr}*{bf}*{tr_}", USD)
                put(W, f"V{rr}", f"=S{rr}*{bf}*{mk_}", USD)
                put(W, f"W{rr}", f"=S{rr}*{bf}", USD)
            TR = 6 + len(rows)
            put(W, f"B{TR}", "TOTAL", kind="text", bold=True)
            for c in [L(7 + m) for m in range(12)] + list("STUVW"):
                put(W, f"{c}{TR}", f"=SUM({c}6:{c}{TR-1})", USD, bold=True)
            for c in range(2, 24): W.cell(TR, c).fill = fill(CARD)
            if e.get("foot"): put(W, f"B{TR+2}", e["foot"], kind="note")
            W.freeze_panes = "C6"
            ex_tabs.append({"account": acct, "tab": tab, "tot": TR, "line": e["line"], "n": len(rows), "flat": True,
                            "trade_ref": tr_, "mkt_ref": mk_, "bf_ref": bf,
                            "trade_name": e.get("trade_card", "Trade $"), "mkt_name": e.get("mkt_card", "Marketing $")})
            continue
        srp = e.get("srp_override") or f"={lref(e['line'], 'C')}"
        for i, b in enumerate(e["skus"]):
            rr = 6 + i
            put(W, f"B{rr}", b, kind="text")
            put(W, f"C{rr}", f"={lref(e['line'], 'C')}", '$#,##0.00', "link")
            put(W, f"D{rr}", e.get("usw_overrides", {}).get(b), DEC, "input")
            put(W, f"E{rr}", f'=IF(D{rr}="",{lref(e["line"], "D")},D{rr})', DEC)
            put(W, f"F{rr}", f"={a['doors:' + e['account']]}", NUM, "link")
            for m in range(12):
                put(W, f"{L(7+m)}{rr}", f"=$F{rr}*$E{rr}*$C{rr}*52/12", USD)
            put(W, f"S{rr}", f"=SUM(G{rr}:R{rr})", USD)
            put(W, f"T{rr}", f"=F{rr}*E{rr}*C{rr}*52", USD)
            put(W, f"U{rr}", f"=S{rr}*{a['brand']}*{a['ex_trade']}", USD)
            put(W, f"V{rr}", f"=S{rr}*{a['brand']}*{a['ex_mkt']}", USD)
            put(W, f"W{rr}", f"=S{rr}*{a['brand']}", USD)
        TR = 6 + len(e["skus"])
        put(W, f"B{TR}", "TOTAL", kind="text", bold=True)
        put(W, f"F{TR}", f"=SUM(F6:F{TR-1})", NUM, bold=True)
        for c in [L(7 + m) for m in range(12)] + list("STUVW"):
            put(W, f"{c}{TR}", f"=SUM({c}6:{c}{TR-1})", USD, bold=True)
        for c in range(2, 24): W.cell(TR, c).fill = fill(CARD)
        if e.get("foot"): put(W, f"B{TR+2}", e["foot"], kind="note")
        W.freeze_panes = "C6"
        ex_tabs.append({"account": e["account"], "tab": tab, "tot": TR, "line": e["line"], "n": len(e["skus"]), "flat": False})

    # ------------------------------------------------ Current State
    C = sheet("Current State", cfg.get("current_state_title", f"{CN}: Current State (existing business)"), cfg.get("current_state_sub"),
              widths={"B": 18, "C": 11, "D": 9, "E": 8, "F": 10, "G": 16, "H": 13, "I": 16, "J": 13, "K": 13, "L": 70})
    hdr(C, 5, ["Retailer", "Channel", "Doors", "SKUs", "TDP", "Current Annual Revenue (retail $)", "Implied $/Door", "Implied $/Door/SKU/Yr", f"Trade $ ({YL})", f"Marketing $ ({YL})", "Source"])
    rr = 6
    for e, t in zip(cfg["existing"], ex_tabs):
        T = q(t["tab"])
        put(C, f"B{rr}", e["account"], kind="text"); put(C, f"C{rr}", e.get("channel", ""), kind="text")
        if t.get("flat"): put(C, f"D{rr}", 0, NUM)
        else: put(C, f"D{rr}", f"={a['doors:' + e['account']]}", NUM, "link")
        if t.get("flat"): put(C, f"E{rr}", 0, NUM)
        else: put(C, f"E{rr}", f"=COUNTA({T}!B6:B{t['tot']-1})", NUM, "link")
        put(C, f"F{rr}", f"=D{rr}*E{rr}", NUM)
        put(C, f"G{rr}", f"={T}!S{t['tot']}", USD, "link")
        put(C, f"H{rr}", f"=IFERROR(G{rr}/D{rr},0)", USD); put(C, f"I{rr}", f"=IFERROR(G{rr}/F{rr},0)", USD)
        put(C, f"J{rr}", f"={T}!U{t['tot']}", USD, "link"); put(C, f"K{rr}", f"={T}!V{t['tot']}", USD, "link")
        put(C, f"L{rr}", e.get("source", ""), kind="note"); rr += 1
    for x in cfg.get("current_state_extra", []):
        put(C, f"B{rr}", x["account"], kind="text"); put(C, f"C{rr}", x.get("channel", ""), kind="text"); put(C, f"L{rr}", x.get("note", ""), kind="note")
        for c in "DEFGHIJK": put(C, f"{c}{rr}", 0, NUM if c in "DEF" else USD, "input")
        rr += 1
    CS_T = rr
    put(C, f"B{rr}", "TOTAL", kind="text", bold=True)
    for c, fm in zip("DEFGJK", (NUM, NUM, NUM, USD, USD, USD)):
        put(C, f"{c}{rr}", f"=SUM({c}6:{c}{rr-1})", fm, bold=True)
    put(C, f"I{rr}", f"=IFERROR(SUMPRODUCT((F6:F{rr-1}>0)*G6:G{rr-1})/F{rr},0)", USD, bold=True)
    for c in range(2, 13): C.cell(rr, c).fill = fill(CARD)

    # ------------------------------------------------ Retailer Expansion
    rx = cfg["retailer_expansion"]
    R = sheet("Retailer Expansion", rx.get("title", f"{CN}: Retailer Expansion"), rx.get("sub"),
              widths={"B": 15, "C": 22, "D": 7, "E": 26, "F": 22, "G": 8, "H": 8, "I": 6, "J": 8, "K": 8, "L": 9, "M": 8, "N": 8, "O": 10, "P": 7, "Q": 8})
    for i in range(12): R.column_dimensions[L(18 + i)].width = 10
    for c in ("AD", "AE", "AF"): R.column_dimensions[c].width = 12
    put(R, "Q4", "month #", kind="note")
    for i in range(12): put(R, f"{L(18+i)}4", i + 1, NUM)
    hdr(R, 5, ["Tier code", "Retailer", "Line", "Access / status", "Review basis", "Review mo #", "Pitch offset (mo)", "Fit", "Hit rate", "Doors", "Expected doors", "SKU override", "SKUs placed", "Rate $/door/SKU/yr", "Gate mo #", "Launch mo #"] + MONTHS + [f"{YL} Total", "Trade $", "Marketing $"])
    r0 = 6
    rp = lambda x: f"IF({x}<=3,{a['r1']},IF({x}<=6,{a['r2']},{a['r3']}))"
    exp_rows = {}
    for i, x in enumerate(rx["accounts"]):
        rr = r0 + i
        tier, name, line, acc, basis, rev, off, fit, doors, ovr, note = x
        exp_rows[name] = rr
        put(R, f"B{rr}", tier, kind="input"); put(R, f"C{rr}", name, kind="text"); put(R, f"D{rr}", line, kind="input")
        put(R, f"E{rr}", acc, kind="note"); put(R, f"F{rr}", basis, kind="note")
        if rev is None: put(R, f"G{rr}", "=" + a["pitch"], NUM, "link")
        else: put(R, f"G{rr}", rev, NUM, "input")
        put(R, f"H{rr}", off, NUM, "input"); put(R, f"I{rr}", fit, '0.00', "input")
        put(R, f"J{rr}", f"=IFERROR(INDEX({a['hit']},MATCH(B{rr},{a['tier']},0)),0)", PCT, "link")
        if isinstance(doors, str) and doors.startswith("existing:"):
            put(R, f"K{rr}", "=" + a["doors:" + doors.split(":", 1)[1]], NUM, "link")
        else:
            put(R, f"K{rr}", doors, NUM, "input", note="gold")
        put(R, f"L{rr}", f"=K{rr}*J{rr}", '#,##0.0;(#,##0.0);"-"')
        put(R, f"M{rr}", ovr, NUM, "input")
        put(R, f"N{rr}", f'=IF(M{rr}="",IFERROR(INDEX({a["skus"]},MATCH(B{rr},{a["tier"]},0)),0),M{rr})', NUM)
        put(R, f"O{rr}", f"=IFERROR(INDEX({a['ln_rate']},MATCH(D{rr},{a['ln_name']},0)),0)", USD, "link")
        put(R, f"P{rr}", f"=IFERROR(INDEX({a['gate']},MATCH(B{rr},{a['tier']},0)),13)", NUM, "link")
        std = f"MAX(P{rr},G{rr}+H{rr}+{a['lag']})"
        if ro:
            first = ro.get("first_account")
            ro_q = f'IF(C{rr}="{first}",MAX(P{rr},{drops[0][0]}),MAX(P{rr},G{rr}+H{rr}+{a["lag"]},{a["others"]}))'
            put(R, f"Q{rr}", f'=IF(D{rr}="{ro["line"]}",{ro_q},{std})', NUM)
        else:
            put(R, f"Q{rr}", "=" + std, NUM)
        base = f"$L{rr}*$I{rr}*$O{rr}/12"
        for m in range(12):
            col = L(18 + m)
            single = f"IF({col}$4<$Q{rr},0,{base}*$N{rr}*{rp(f'{col}$4-$Q{rr}+1')})"
            if ro:
                parts, cum_prev = [], "0"
                for k, (mref, sref) in enumerate(drops):
                    cum = "+".join(s for _, s in drops[:k + 1])
                    cnt = f"(MIN($N{rr},{cum})-MIN($N{rr},{cum_prev}))" if k else f"MIN($N{rr},{cum})"
                    st = f"MAX($Q{rr},{mref})" if k else f"$Q{rr}"
                    parts.append(f"IF({col}$4<{st},0,{base}*{cnt}*{rp(f'{col}$4-{st}+1')})")
                    cum_prev = cum
                put(R, f"{col}{rr}", f'=IF($D{rr}="{ro["line"]}",{"+".join(parts)},{single})', USD)
            else:
                put(R, f"{col}{rr}", "=" + single, USD)
        put(R, f"AD{rr}", f"=SUM(R{rr}:AC{rr})", USD)
        put(R, f"AE{rr}", f"=AD{rr}*{a['brand']}*IFERROR(INDEX({a['trade']},MATCH(B{rr},{a['tier']},0)),0)", USD)
        put(R, f"AF{rr}", f"=AD{rr}*{a['brand']}*IFERROR(INDEX({a['mkt']},MATCH(B{rr},{a['tier']},0)),0)", USD)
        put(R, f"AG{rr}", note or "", kind="note")
    RT = r0 + len(rx["accounts"])
    R_FIRST, R_LAST = r0, RT - 1
    put(R, f"B{RT}", "TOTAL", kind="text", bold=True)
    put(R, f"K{RT}", f"=SUM(K{r0}:K{RT-1})", NUM, bold=True); put(R, f"L{RT}", f"=SUM(L{r0}:L{RT-1})", '#,##0.0', bold=True)
    for m in range(12):
        col = L(18 + m); put(R, f"{col}{RT}", f"=SUM({col}{r0}:{col}{RT-1})", USD, bold=True)
    for c in ("AD", "AE", "AF"): put(R, f"{c}{RT}", f"=SUM({c}{r0}:{c}{RT-1})", USD, bold=True)
    for c in range(2, 33): R.cell(RT, c).fill = fill(CARD)
    if rx.get("foot"): put(R, f"B{RT+2}", rx["foot"], kind="note")
    dv = DataValidation(type="list", formula1=f"={a['tier']}", allow_blank=False); R.add_data_validation(dv); dv.add(f"B{r0}:B{RT-1}")
    dv2 = DataValidation(type="list", formula1='"' + ",".join(l["name"] for l in lines) + '"'); R.add_data_validation(dv2); dv2.add(f"D{r0}:D{RT-1}")
    R.freeze_panes = "D6"

    # ------------------------------------------------ SKU Expansion
    sx = cfg["sku_expansion"]
    S = sheet("SKU Expansion", sx.get("title", f"{CN}: SKU / TDP Expansion"), sx.get("sub"),
              widths={"B": 9, "C": 30, "D": 18, "E": 8, "F": 9, "G": 50, "H": 6, "I": 8, "J": 10, "K": 11})
    for i in range(12): S.column_dimensions[L(12 + i)].width = 10
    for c in "XYZ": S.column_dimensions[c].width = 12
    for i in range(12): put(S, f"{L(12+i)}4", i + 1, NUM)
    hdr(S, 5, ["Priority", "SKU / flavor", "Type", "SRP", "COGS ceiling", "Why", "Seq #", "Launch mo #", "Doors it launches into", "Rate $/door/SKU/yr"] + MONTHS + [f"{YL} Total", "Trade $", "Marketing $"])
    s0 = 6
    rng = lambda c: f"'Retailer Expansion'!${c}${R_FIRST}:${c}${R_LAST}"
    for i, (pr, nm, ty, why) in enumerate(sx["skus"]):
        rr = s0 + i
        put(S, f"B{rr}", pr, kind="input"); put(S, f"C{rr}", nm, kind="text"); put(S, f"D{rr}", ty, kind="note")
        put(S, f"E{rr}", f"={lref(ss['line'], 'C')}", '$#,##0.00', "link")
        put(S, f"F{rr}", f"=E{rr}*{a['cogs']}", '$#,##0.00'); put(S, f"G{rr}", why, kind="note")
        put(S, f"H{rr}", i + 1, NUM, "input"); put(S, f"I{rr}", f"={a['first']}+(H{rr}-1)*{a['cad']}", NUM)
        put(S, f"J{rr}", f'=SUMIFS({rng("L")},{rng("B")},"{ss.get("into_tier", cfg["tiers"][0]["code"])}",{rng("D")},"{ss["line"]}",{rng("Q")},"<="&I{rr})', '#,##0.0', "link")
        put(S, f"K{rr}", f"=E{rr}*{a['newusw']}*52", USD)
        for m in range(12):
            col = L(12 + m)
            put(S, f"{col}{rr}", f"=IF({col}$4<$I{rr},0,$J{rr}*$K{rr}/12*IF({col}$4-$I{rr}+1<=3,{a['r1']},IF({col}$4-$I{rr}+1<=6,{a['r2']},{a['r3']})))", USD)
        put(S, f"X{rr}", f"=SUM(L{rr}:W{rr})", USD); put(S, f"Y{rr}", f"=X{rr}*{a['brand']}*{a['ni_trade']}", USD); put(S, f"Z{rr}", f"=X{rr}*{a['brand']}*{a['ni_mkt']}", USD)
    ST = s0 + len(sx["skus"])
    put(S, f"B{ST}", "TOTAL", kind="text", bold=True)
    for m in range(12):
        col = L(12 + m); put(S, f"{col}{ST}", f"=SUM({col}{s0}:{col}{ST-1})", USD, bold=True)
    for c in "XYZ": put(S, f"{c}{ST}", f"=SUM({c}{s0}:{c}{ST-1})", USD, bold=True)
    for c in range(2, 27): S.cell(ST, c).fill = fill(CARD)
    if sx.get("foot"): put(S, f"B{ST+2}", sx["foot"], kind="note")
    S.freeze_panes = "D6"

    # ------------------------------------------------ Overall
    ov = cfg.get("overall", {})
    O = sheet("Overall", ov.get("title", f"{CN}: Forecast & Budget {VER}: Overall"), ov.get("sub", "Everything here is a link or a sum."), widths={"B": 58, "C": 4, "D": 12})
    for i in range(13): O.column_dimensions[L(5 + i)].width = 12
    hdr(O, 5, ["", "", ""] + MONTHS + [f"{YL} Total"], c1=2)
    rr = 6
    ex_rows = []
    for t in ex_tabs:
        lab = ov.get("existing_label") if len(ex_tabs) == 1 and ov.get("existing_label") else f"Existing Business ({t['account']})"
        put(O, f"B{rr}", lab, kind="text")
        for m in range(12): put(O, f"{L(5+m)}{rr}", f"={q(t['tab'])}!{L(7+m)}{t['tot']}", USD, "link")
        put(O, f"Q{rr}", f"=SUM(E{rr}:P{rr})", USD); ex_rows.append(rr); rr += 1
    RX_ROW, SX_ROW = rr, rr + 1
    for row, lab, sh, tr, c0 in ((RX_ROW, ov.get("retailer_label", "Retailer Expansion (incremental)"), "'Retailer Expansion'", RT, 18),
                                 (SX_ROW, ov.get("sku_label", "SKU / TDP Expansion (incremental)"), "'SKU Expansion'", ST, 12)):
        put(O, f"B{row}", lab, kind="text")
        for m in range(12): put(O, f"{L(5+m)}{row}", f"={sh}!{L(c0+m)}{tr}", USD, "link")
        put(O, f"Q{row}", f"=SUM(E{row}:P{row})", USD)
    MR_ROW = None
    if mr:
        MR_ROW = SX_ROW + 1
        mkt_all = "+".join([f"{q(t['tab'])}!V{t['tot']}" for t in ex_tabs] + [f"'Retailer Expansion'!AF{RT}", f"'SKU Expansion'!Z{ST}"])
        put(O, f"B{MR_ROW}", ov.get("mret_label", f"Marketing return ({mr['ratio']:g}x marketing $, retail $, incremental)"), kind="text")
        for m in range(12):
            c = L(5 + m)
            put(O, f"{c}{MR_ROW}", f"=IFERROR({a['mret']}*({mkt_all})*SUM({c}6:{c}{SX_ROW})/SUM($Q$6:$Q${SX_ROW}),0)", USD)
        put(O, f"Q{MR_ROW}", f"=SUM(E{MR_ROW}:P{MR_ROW})", USD)
    TOT = (MR_ROW or SX_ROW) + 1; BR = TOT + 1
    put(O, f"B{TOT}", "TOTAL REVENUE (retail $ at shelf)", kind="text", bold=True)
    flat_rows = [(x, t) for x, t in zip(ex_rows, ex_tabs) if t.get("flat")]
    br_lab = f"Brand revenue (after {w['retailer']*100:.0f} retailer / {w['distributor']*100:.0f} distributor)"
    if flat_rows: br_lab += "; " + ", ".join(t["account"] for _, t in flat_rows) + " on its own waterfall"
    put(O, f"B{BR}", br_lab, kind="text")
    for m in range(13):
        c = L(5 + m)
        put(O, f"{c}{TOT}", f"=SUM({c}6:{c}{MR_ROW or SX_ROW})", USD, bold=True)
        if flat_rows:
            fr = "+".join(f"{c}{x}" for x, _ in flat_rows)
            fg = "+".join(f"{c}{x}*{t['bf_ref']}" for x, t in flat_rows)
            put(O, f"{c}{BR}", f"=({c}{TOT}-({fr}))*{a['brand']}+{fg}", USD)
        else:
            put(O, f"{c}{BR}", f"={c}{TOT}*{a['brand']}", USD)
    for c in range(2, 18): O.cell(TOT, c).fill = fill(CARD)
    r = BR + 2
    bar(O, r, f"BUDGET ({YL} Trade & Marketing, tier model)", 2, 19); r += 1
    hdr(O, r, ["", "", "", "Trade $", "Marketing $"], c1=2); r += 1
    b0 = r
    for t in ex_tabs:
        lab = ov.get("existing_budget_label") if len(ex_tabs) == 1 and ov.get("existing_budget_label") else f"Existing Business ({t['account']}, mature rates)"
        put(O, f"B{r}", lab, kind="text"); put(O, f"E{r}", f"={q(t['tab'])}!U{t['tot']}", USD, "link"); put(O, f"F{r}", f"={q(t['tab'])}!V{t['tot']}", USD, "link"); r += 1
    put(O, f"B{r}", "Retailer Expansion (tier rates)", kind="text"); put(O, f"E{r}", f"='Retailer Expansion'!AE{RT}", USD, "link"); put(O, f"F{r}", f"='Retailer Expansion'!AF{RT}", USD, "link"); r += 1
    put(O, f"B{r}", "SKU Expansion (new-item rates)", kind="text"); put(O, f"E{r}", f"='SKU Expansion'!Y{ST}", USD, "link"); put(O, f"F{r}", f"='SKU Expansion'!Z{ST}", USD, "link")
    b1 = r; r += 1
    TRADE = r; put(O, f"B{r}", f"Trade $ ({YL})", kind="text"); put(O, f"E{r}", f"=SUM(E{b0}:E{b1})", USD, bold=True); r += 1
    MKT = r; put(O, f"B{r}", f"Marketing $ ({YL})", kind="text"); put(O, f"F{r}", f"=SUM(F{b0}:F{b1})", USD, bold=True); r += 1
    SPEND = r; put(O, f"B{r}", "Total Spend (Trade + Marketing)", kind="text", bold=True); put(O, f"F{r}", f"=E{TRADE}+F{MKT}", USD, bold=True); r += 1
    CMLINK = r; put(O, f"B{r}", "Contribution margin (P&L below)", kind="text"); r += 1
    put(O, f"B{r}", "Total Spend as % of gross sales", kind="text"); put(O, f"F{r}", f"=IFERROR(F{SPEND}/Q{BR},0)", PCT); r += 2
    bar(O, r, "TDP GROWTH (SKUs x doors)", 2, 19); r += 1
    put(O, f"B{r}", ov.get("starting_tdp_label", "Starting TDP (existing business today)"), kind="text"); put(O, f"F{r}", f"='Current State'!F{CS_T}", NUM, "link"); tdp0 = r; r += 1
    rr_ = lambda c: f"'Retailer Expansion'!{c}{R_FIRST}:{c}{R_LAST}"
    put(O, f"B{r}", f"+ New retailer TDP in {YL} (expected doors x SKUs placed)", kind="text"); put(O, f"F{r}", f"=SUMPRODUCT(({rr_('Q')}<=12)*{rr_('L')}*{rr_('N')})", '#,##0.0', "link"); r += 1
    sk = lambda c: f"'SKU Expansion'!{c}{s0}:{c}{ST-1}"
    put(O, f"B{r}", f"+ New SKU TDP in {YL} (doors each new SKU launches into)", kind="text"); put(O, f"F{r}", f"=SUMPRODUCT(({sk('I')}<=12)*{sk('J')})", '#,##0.0', "link"); r += 1
    put(O, f"B{r}", f"Ending TDP ({YL} close)", kind="text", bold=True); put(O, f"F{r}", f"=SUM(F{tdp0}:F{r-1})", '#,##0.0', bold=True); TDP_END = r; r += 2
    SAN_PCT = None
    if san:
        bar(O, r, "SANITY CHECK vs. intake", 2, 19); r += 1
        exsum = "+".join(f"{q(t['tab'])}!W{t['tot']}" for t in ex_tabs)
        put(O, f"B{r}", san.get("existing_label", "Existing Business at brand $"), kind="text"); put(O, f"F{r}", f"={exsum}", USD); r += 1
        put(O, f"B{r}", san.get("overall_label", "Intake revenue (brand $)"), kind="text"); put(O, f"F{r}", f"={a['sanity']}", USD, "link"); r += 1
        put(O, f"B{r}", san.get("pct_label", "Existing as % of intake"), kind="text"); put(O, f"F{r}", f"=IFERROR(F{r-2}/F{r-1},0)", PCT); SAN_PCT = r; r += 1
        put(O, f"B{r}", san.get("explain", ""), kind="note"); r += 2
    bar(O, r, f"P&L SUMMARY ({YL})", 2, 19); r += 1
    hdr(O, r, ["", "", "", "", f"$ ({YL})", "% of gross sales"], c1=2); r += 1
    # retail $ by line, then units x COGS per line
    RXS = lambda col: f"'Retailer Expansion'!${col}${R_FIRST}:${col}${R_LAST}"
    cogs_terms = []
    for ln in lines:
        parts = [f"{q(t['tab'])}!S{t['tot']}" for t in ex_tabs if t["line"] == ln["name"]]
        parts.append(f'SUMIFS({RXS("AD")},{RXS("D")},"{ln["name"]}")')
        if ss["line"] == ln["name"]: parts.append(f"'SKU Expansion'!X{ST}")
        cogs_terms.append(f"({'+'.join(parts)})/{lref(ln['name'], 'C')}*{lref(ln['name'], 'E')}")
    p0 = r
    pl = [("Retail $ at shelf", f"=Q{TOT}", False),
          (ov.get("margin_label", f"Less retailer ({w['retailer']*100:.0f}%) and distributor ({w['distributor']*100:.0f}%) margin"), f"=Q{TOT}-Q{BR}", False),
          (ov.get("gross_label", "Gross sales (what the brand invoices)"), f"=Q{BR}", True),
          ("Less trade", f"=E{TRADE}", False),
          ("Net sales", f"=F{p0+2}-F{p0+3}", True),
          ("Less COGS (units x COGS per unit)", "=(" + "+".join(cogs_terms) + ")" + (f"*IFERROR(Q{TOT}/(Q{TOT}-Q{MR_ROW}),1)" if MR_ROW else ""), False),
          ("Gross profit", f"=F{p0+4}-F{p0+5}", True),
          ("Less marketing", f"=F{MKT}", False),
          ("Contribution margin (before overhead)", f"=F{p0+6}-F{p0+7}", True)]
    for i, (lab, f_, bold) in enumerate(pl):
        rr = p0 + i
        put(O, f"B{rr}", lab, kind="text", bold=bold); put(O, f"F{rr}", f_, USD, bold=bold)
        if i >= 2: put(O, f"G{rr}", f"=IFERROR(F{rr}/$F${p0+2},0)", PCT, bold=bold)
        if bold:
            for c in range(2, 8): O.cell(rr, c).fill = fill(CARD)
    CM = p0 + 8
    put(O, f"F{CMLINK}", f"=F{CM}", USD)
    if ov.get("pl_note"): put(O, f"B{CM+1}", ov["pl_note"], kind="note")
    O.freeze_panes = "C6"
    refs.update({"overall": {"tot": TOT, "brand": BR, "trade": f"E{TRADE}", "mkt": f"F{MKT}", "spend": f"F{SPEND}",
                             "gross": f"F{p0+2}", "net": f"F{p0+4}", "cogs": f"F{p0+5}", "gp": f"F{p0+6}", "cm": f"F{CM}",
                             "sanity_pct": f"F{SAN_PCT}" if SAN_PCT else None, "tdp_end": f"F{TDP_END}", "mret_row": MR_ROW},
                 "existing": ex_tabs, "rx_tot": RT, "sx_tot": ST, "rx_first": R_FIRST, "rx_last": R_LAST})

    # ------------------------------------------------ Plan / Vol templates (optional)
    pc = cfg.get("plan")
    order = ["Read Me", "Assumptions", "Overall", "Current State"] + [t["tab"] for t in ex_tabs] + ["Retailer Expansion", "SKU Expansion"]
    if pc:
        pt = next(t for t in ex_tabs if t["account"] == pc["account"])
        pe = next(e for e in cfg["existing"] if e["account"] == pc["account"])
        pname = f"{pc['account']} Plan"[:31]; vname = f"{pc['account']} Vol"[:31]
        PL = sheet(pname, f"Customer: {pc['account']}. {LOVE} in-store plan (TEMPLATE)", "Blue = type here. Black = formula. Green = pulled from the model. Build the program to the recommended spend row.", widths={"B": 44, "C": 30})
        for i in range(12): PL.column_dimensions[L(4 + i)].width = 10
        PL.column_dimensions["P"].width = 13; PL.column_dimensions["Q"].width = 14
        hdr(PL, 5, ["Line", "Comments"] + MONTHS + [f"TOTAL {YL}", "vs. recommended"])
        plan_skus = pe["skus"] + pc.get("extra_skus", [])
        r = 6; bar(PL, r, "VOLUMES (units by SKU)", 2, 17)
        for s_ in plan_skus:
            r += 1; put(PL, f"B{r}", s_, kind="text")
            for m in range(12): put(PL, f"{L(4+m)}{r}", None, NUM, "input")
            put(PL, f"P{r}", f"=SUM(D{r}:O{r})", NUM)
        r += 1; bar(PL, r, "REVENUE (retail $ by SKU)", 2, 17); rv0 = r + 1
        for s_ in plan_skus:
            r += 1; put(PL, f"B{r}", s_, kind="text")
            for m in range(12): put(PL, f"{L(4+m)}{r}", None, USD, "input")
            put(PL, f"P{r}", f"=SUM(D{r}:O{r})", USD)
        rv1 = r; r += 1; put(PL, f"B{r}", "Plan revenue", kind="text", bold=True)
        for m in range(13): put(PL, f"{L(4+m)}{r}", f"=SUM({L(4+m)}{rv0}:{L(4+m)}{rv1})", USD, bold=True)
        REVROW = r; r += 2; REC = r
        put(PL, f"B{r}", pc.get("rec_label", "RECOMMENDED SPEND (model, Trade + Marketing)"), kind="text", bold=True)
        xr = exp_rows.get(pc.get("expansion_account"))
        for m in range(12):
            f_ = f"={q(pt['tab'])}!{L(7+m)}{pt['tot']}*{a['brand']}*({a['ex_trade']}+{a['ex_mkt']})"
            if xr:
                f_ += (f"+'Retailer Expansion'!{L(18+m)}{xr}*{a['brand']}*(IFERROR(INDEX({a['trade']},MATCH('Retailer Expansion'!$B${xr},{a['tier']},0)),0)"
                       f"+IFERROR(INDEX({a['mkt']},MATCH('Retailer Expansion'!$B${xr},{a['tier']},0)),0))")
            put(PL, f"{L(4+m)}{r}", f_, USD, "link")
        put(PL, f"P{r}", f"=SUM(D{r}:O{r})", USD, bold=True)
        for c in range(2, 18): PL.cell(r, c).fill = fill(CARD)
        r += 2; sub_rows = []
        for title, items in pc.get("sections", []):
            bar(PL, r, title, 2, 17); first = r + 1
            for lab, cm in items:
                r += 1; put(PL, f"B{r}", lab, kind="text"); put(PL, f"C{r}", cm, kind="note")
                for m in range(12): put(PL, f"{L(4+m)}{r}", None, USD, "input")
                put(PL, f"P{r}", f"=SUM(D{r}:O{r})", USD)
            r += 1; put(PL, f"B{r}", f"{title} subtotal", kind="text", bold=True)
            for m in range(13): put(PL, f"{L(4+m)}{r}", f"=SUM({L(4+m)}{first}:{L(4+m)}{r-1})", USD, bold=True)
            sub_rows.append(r); r += 2
        bar(PL, r, "IN-STORE SAMPLING", 2, 17)
        r += 1; put(PL, f"B{r}", "Cost per demo", kind="text"); put(PL, f"C{r}", None, USD, "input"); DEMO = r
        r += 1; put(PL, f"B{r}", "# Demos", kind="text")
        for m in range(12): put(PL, f"{L(4+m)}{r}", None, NUM, "input")
        NDEM = r
        r += 1; put(PL, f"B{r}", "Demo activations $", kind="text")
        for m in range(12): put(PL, f"{L(4+m)}{r}", f"={L(4+m)}{NDEM}*$C${DEMO}", USD)
        put(PL, f"P{r}", f"=SUM(D{r}:O{r})", USD); DEMOS = r
        r += 1; put(PL, f"B{r}", "Demo logistics and stock (product used)", kind="text")
        for m in range(12): put(PL, f"{L(4+m)}{r}", None, USD, "input")
        put(PL, f"P{r}", f"=SUM(D{r}:O{r})", USD)
        r += 1; put(PL, f"B{r}", "SAMPLING subtotal", kind="text", bold=True)
        for m in range(13): put(PL, f"{L(4+m)}{r}", f"={L(4+m)}{DEMOS}+{L(4+m)}{DEMOS+1}", USD, bold=True)
        sub_rows.append(r); r += 2; TOTP = r
        put(PL, f"B{r}", f"TOTAL SPEND ({LOVE.upper()} IN STORE)", kind="text", bold=True)
        for m in range(13):
            c = L(4 + m); put(PL, f"{c}{r}", "=" + "+".join(f"{c}{x}" for x in sub_rows), USD, bold=True)
        put(PL, f"Q{r}", f"=P{r}-P{REC}", USD, bold=True)
        for c in range(2, 18): PL.cell(r, c).fill = fill(CARD)
        r += 1; put(PL, f"B{r}", "Spend % of plan revenue", kind="text")
        for m in range(13):
            c = L(4 + m); put(PL, f"{c}{r}", f"=IFERROR({c}{TOTP}/{c}{REVROW},0)", PCT)
        r += 1; put(PL, f"B{r}", "Budget status", kind="text", bold=True); put(PL, f"C{r}", f'=IF(P{TOTP}>P{REC},"OVER BUDGET","Within budget")', kind="calc", bold=True)
        r += 1; put(PL, f"B{r}", "Reason for any variance (required if over)", kind="text"); put(PL, f"C{r}", None, kind="input")
        PL.freeze_panes = "D6"

        V = sheet(vname, f"{pc['account']}: base volume and program lift (TEMPLATE)", "Type store count, retail and u/s/w in blue. Each program: lift %, weeks, fixed cost (or scan $/unit). Sales and summary calculate.",
                  widths={"B": 34, "C": 11, "D": 11, "E": 11, "F": 11, "G": 14, "H": 3, "I": 44, "J": 14})
        r = 5; hdr(V, r, ["Base volume: Item", "Store count", "Retail", "U/S/W", "$/S/W", "Annual sales"]); bb0 = r + 1
        for s_ in plan_skus:
            r += 1; put(V, f"B{r}", s_, kind="text")
            put(V, f"C{r}", None, NUM, "input"); put(V, f"D{r}", None, '$#,##0.00', "input"); put(V, f"E{r}", None, DEC, "input")
            put(V, f"F{r}", f"=D{r}*E{r}", '$#,##0.00'); put(V, f"G{r}", f"=C{r}*F{r}*52", USD)
        bb1 = r; r += 1; put(V, f"B{r}", "Base annual sales", kind="text", bold=True); put(V, f"G{r}", f"=SUM(G{bb0}:G{bb1})", USD, bold=True); BASE = r
        lift_cells, fixed_cells, scan_cells = [], [], []
        for name, tpr in pc.get("programs", []):
            r += 2; bar(V, r, name, 2, 7)
            r += 1; put(V, f"B{r}", "Lift over base (%)", kind="text"); put(V, f"C{r}", None, PCT, "input")
            put(V, f"D{r}", "Weeks", kind="text"); put(V, f"E{r}", None, NUM, "input")
            put(V, f"F{r}", "Scan $/unit" if tpr else "Fixed cost", kind="text"); put(V, f"G{r}", None, '$#,##0.00' if tpr else USD, "input")
            P_ = r
            r += 1; hdr(V, r, ["Item", "Store count", "Promo retail", "Add'l U/S/W", "$/S/W", "Program sales"]); pp0 = r + 1
            for j, s_ in enumerate(plan_skus):
                r += 1; br = bb0 + j
                put(V, f"B{r}", s_, kind="text"); put(V, f"C{r}", f"=C{br}", NUM); put(V, f"D{r}", None, '$#,##0.00', "input")
                put(V, f"E{r}", f"=E{br}*$C${P_}", DEC); put(V, f"F{r}", f"=D{r}*E{r}", '$#,##0.00'); put(V, f"G{r}", f"=C{r}*F{r}*$E${P_}", USD)
            pp1 = r
            r += 1; put(V, f"B{r}", "Program lift (retail $)", kind="text", bold=True); put(V, f"G{r}", f"=SUM(G{pp0}:G{pp1})", USD, bold=True); lift_cells.append(f"G{r}")
            if tpr:
                r += 1; put(V, f"B{r}", "Variable scan cost", kind="text"); put(V, f"G{r}", f"=SUMPRODUCT(C{pp0}:C{pp1},E{pp0}:E{pp1})*$E${P_}*$G${P_}", USD); scan_cells.append(f"G{r}")
            else:
                fixed_cells.append(f"G{P_}")
        j = lambda cells: "=" + ("+".join(cells) if cells else "0")
        sm = [("Program lift, retail $ (all programs)", j(lift_cells), USD), ("Fixed costs", j(fixed_cells), USD), ("Variable scan costs", j(scan_cells), USD),
              ("Total program cost", "=J8+J9", USD), ("Lift $ per program $ (retail)", "=IFERROR(J7/J10,0)", '0.00x'),
              ("Program lift as % of base annual sales", f"=IFERROR(J7/G{BASE},0)", PCT),
              (f"Total program cost vs. recommended ({pname})", f"=J10-{q(pname)}!P{REC}", USD)]
        put(V, "I5", "Summary", kind="text", bold=True); put(V, "J5", "Value", kind="text", bold=True)
        for i, (lab, f_, fm) in enumerate(sm):
            put(V, f"I{7+i}", lab, kind="text"); put(V, f"J{7+i}", f_, fm)
        put(V, "I15", "Lift is retail $ at shelf. Back out retailer and distributor margin before comparing to brand cost.", kind="note")
        V.freeze_panes = "C6"
        order += [pname, vname]

    wb._sheets = [wb[n] for n in order]
    for ws in wb.worksheets:
        ws.sheet_properties.tabColor = BROWN if ws.title in ("Overall", "Assumptions") else GREIGE
    os.makedirs(out_dir, exist_ok=True)
    fname = f"{CN.replace(' ', '_')}_Forecast_and_Budget_{VER}.xlsx"
    path = os.path.join(out_dir, fname)
    wb.save(path)
    refs["file"] = fname
    json.dump(refs, open(os.path.join(out_dir, "refs.json"), "w"), indent=1)
    return path, refs


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    p, _ = build(cfg, sys.argv[2])
    print("saved", p)
