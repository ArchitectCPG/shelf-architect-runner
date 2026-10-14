// Shelf Architect runner: drives Bright Data's Scraping Browser (remote Chromium over CDP) through a
// per-banner RECIPE (blocks/<block>.json) to walk one block: set a store, search a neighborhood, capture houses.
// Usage: node src/pull.mjs blocks/<block>.json
import { chromium } from "playwright-core";
import fs from "node:fs";
import path from "node:path";

const blockFile = process.argv[2];
if (!blockFile) { console.error("usage: node src/pull.mjs blocks/<block>.json"); process.exit(2); }
const block = JSON.parse(fs.readFileSync(blockFile, "utf8"));
const vars = { store_zip: block.store_zip || "", term: block.neighborhood || block.search_term || "", ...(block.vars || {}) };
const sub = (s) => String(s).replace(/\{\{(\w+)\}\}/g, (_, k) => vars[k] ?? "");


// ---- API lane: Bright Data prebuilt scrapers (dataset trigger), no browser ----
if (block.kroger_api) { // Kroger Developer API: client_credentials -> locations near zip -> products at that location
  const id = process.env.KROGER_CLIENT_ID, sec = process.env.KROGER_CLIENT_SECRET; if (!id || !sec) { console.error("missing KROGER_CLIENT_ID/SECRET"); process.exit(2); }
  const k = block.kroger_api; const day = new Date().toISOString().slice(0, 10);
  const outDir = path.join("data", block.retailer, block.block_id.replace(/[^a-z0-9@_.-]/gi, "_")); fs.mkdirSync(outDir, { recursive: true });
  const o = { block_id: block.block_id, retailer: block.retailer, zip: block.zip || null, neighborhood: block.neighborhood, pulled_at: new Date().toISOString(), runner: "github-actions+kroger-api", store_requested_zip: block.store_zip, store_set: null, houses: [], steps: [], error: null };
  const lg = m => { o.steps.push(`${new Date().toISOString().slice(11, 19)} ${m}`); console.log(m); };
  try {
    const tok = await (await fetch("https://api.kroger.com/v1/connect/oauth2/token", { method: "POST", headers: { Authorization: "Basic " + Buffer.from(`${id}:${sec}`).toString("base64"), "content-type": "application/x-www-form-urlencoded" }, body: "grant_type=client_credentials&scope=product.compact" })).json();
    if (!tok.access_token) throw new Error("token: " + JSON.stringify(tok).slice(0, 200));
    const H = { Authorization: `Bearer ${tok.access_token}` };
    const chainQ = k.chain ? `&filter.chain=${encodeURIComponent(k.chain)}` : "";
    const locs = await (await fetch(`https://api.kroger.com/v1/locations?filter.zipCode.near=${block.store_zip}&filter.limit=5${chainQ}`, { headers: H })).json();
    const loc = (locs.data || [])[0]; if (!loc) throw new Error("no location: " + JSON.stringify(locs).slice(0, 300));
    o.store_set = `${loc.chain} ${loc.name} (${loc.locationId}) ${loc.address?.addressLine1 || ""} ${loc.address?.city || ""} ${loc.address?.zipCode || ""}`.trim(); lg(`store ${o.store_set}`);
    const term = encodeURIComponent(block.term); let all = [];
    for (let start = 0; start < (k.max || 150); start += 50) {
      const r = await (await fetch(`https://api.kroger.com/v1/products?filter.term=${term}&filter.locationId=${loc.locationId}&filter.limit=50&filter.start=${start}`, { headers: H })).json();
      const items = r.data || []; all = all.concat(items); lg(`products start=${start}: ${items.length}`); if (items.length < 50) break;
    }
    o.houses = all.map(p => { const it = (p.items || [])[0] || {}; const pr = it.price || {}; return { name: p.description, brand: p.brand || null, upc: p.upc, product_id: p.productId, size: it.size || null, price: pr.promo && pr.promo > 0 ? `$${pr.promo}` : (pr.regular != null ? `$${pr.regular}` : null), regular_price: pr.regular ?? null, promo_price: pr.promo ?? null, availability: it.fulfillment ? Object.entries(it.fulfillment).filter(([, v]) => v).map(([k2]) => k2).join(",") : null, stock: it.inventory?.stockLevel || null, categories: p.categories || [], img: (p.images || []).find(i => i.perspective === "front")?.sizes?.find(s2 => s2.size === "medium")?.url || null, link: p.productPageURI ? "https://www.kroger.com" + p.productPageURI : null }; });
    lg(`extracted ${o.houses.length} houses`);
  } catch (e) { o.error = String(e).slice(0, 400); lg(`ERROR ${o.error}`); }
  fs.writeFileSync(path.join(outDir, `${day}.json`), JSON.stringify(o, null, 1));
  console.log(`\nRESULT block=${o.block_id} store=${o.store_set} houses=${o.houses.length} error=${o.error}`); process.exit(o.error ? 1 : 0);
}
if (block.api_unlock) { // Bright Data Web Unlocker: fetch a URL through the unlocker zone (no browser), save body
  const tok = process.env.BRD_API_TOKEN; if (!tok) { console.error("missing BRD_API_TOKEN"); process.exit(2); }
  const u = block.api_unlock; const dir = path.join("data", block.retailer, block.block_id.replace(/[^a-z0-9@_.-]/gi, "_")); fs.mkdirSync(dir, { recursive: true }); const res = {};
  for (const url of u.urls) { const r = await fetch("https://api.brightdata.com/request", { method: "POST", headers: { Authorization: `Bearer ${tok}`, "content-type": "application/json" }, body: JSON.stringify({ zone: u.zone || "mcp_unlocker", url: url.replace("{{term}}", encodeURIComponent(block.term || "")), format: "raw", country: "us" }) }); const t = await r.text(); res[url] = { status: r.status, len: t.length, body: t.slice(0, 120000) }; console.log("unlock", r.status, t.length, url); }
  fs.writeFileSync(path.join(dir, new Date().toISOString().slice(0, 10) + ".json"), JSON.stringify(res)); process.exit(0);
}
if (block.api_get) {
  const tok = process.env.BRD_API_TOKEN; if (!tok) { console.error("missing BRD_API_TOKEN"); process.exit(2); }
  const res = {}; for (const pth of block.api_get) { const r = await fetch("https://api.brightdata.com/" + pth, { headers: { Authorization: `Bearer ${tok}` } }); res[pth] = { status: r.status, body: (await r.text()).slice(0, 60000) }; }
  const dir = path.join("data", block.retailer, block.block_id.replace(/[^a-z0-9@_.-]/gi, "_")); fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, new Date().toISOString().slice(0,10) + ".json"), JSON.stringify(res)); console.log("api_get done"); process.exit(0);
}
if (block.api_list) {
  const tok = process.env.BRD_API_TOKEN; if (!tok) { console.error("missing BRD_API_TOKEN"); process.exit(2); }
  const r = await fetch("https://api.brightdata.com/datasets/list", { headers: { Authorization: `Bearer ${tok}` } });
  const txt = await r.text(); const dir = path.join("data", block.retailer, block.block_id.replace(/[^a-z0-9@_.-]/gi, "_")); fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, new Date().toISOString().slice(0,10) + ".json"), JSON.stringify({ status: r.status, body: txt.slice(0, 900000) }));
  console.log("api_list status", r.status, txt.length); process.exit(r.ok ? 0 : 1);
}
if (block.api) {
  const tok = process.env.BRD_API_TOKEN;
  if (!tok) { console.error("missing BRD_API_TOKEN"); process.exit(2); }
  const stamp2 = new Date().toISOString(); const day2 = stamp2.slice(0, 10);
  const outDir2 = path.join("data", block.retailer, block.block_id.replace(/[^a-z0-9@_.-]/gi, "_"));
  fs.mkdirSync(outDir2, { recursive: true });
  const o = { block_id: block.block_id, retailer: block.retailer, zip: block.zip || null,
    neighborhood: block.neighborhood || null, pulled_at: stamp2, runner: "github-actions+brightdata-dataset-api",
    store_requested_zip: block.store_zip || null, store_set: null, houses: [], steps: [], error: null };
  const lg = (m) => { console.log(m); o.steps.push(`${new Date().toISOString().slice(11,19)} ${m}`); };
  try {
    const a = block.api;
    const input = JSON.parse(sub(JSON.stringify(a.input)));
    const qs = new URLSearchParams({ dataset_id: a.dataset_id, include_errors: "true",
      type: "discover_new", discover_by: a.discover_by, limit_per_input: String(a.limit || 48) });
    const trig = await fetch(`https://api.brightdata.com/datasets/v3/trigger?${qs}`, {
      method: "POST", headers: { Authorization: `Bearer ${tok}`, "Content-Type": "application/json" },
      body: JSON.stringify([input]) });
    const tj = await trig.json();
    if (!tj.snapshot_id) throw new Error(`trigger failed: ${JSON.stringify(tj).slice(0,300)}`);
    lg(`snapshot ${tj.snapshot_id}`);
    let recs = null;
    for (let i = 0; i < 90; i++) {
      await new Promise(r => setTimeout(r, 20000));
      const pr = await fetch(`https://api.brightdata.com/datasets/v3/progress/${tj.snapshot_id}`, { headers: { Authorization: `Bearer ${tok}` } });
      const pj = await pr.json();
      if (i % 3 === 0) lg(`poll ${i}: ${pj.status}`);
      if (pj.status === "ready") {
        const dl = await fetch(`https://api.brightdata.com/datasets/v3/snapshot/${tj.snapshot_id}?format=json`, { headers: { Authorization: `Bearer ${tok}` } });
        recs = await dl.json(); break;
      }
      if (pj.status === "failed") throw new Error(`snapshot failed: ${JSON.stringify(pj).slice(0,300)}`);
    }
    if (!recs) throw new Error("timed out waiting for snapshot (30 min)");
    if (!Array.isArray(recs)) throw new Error(`unexpected snapshot shape: ${JSON.stringify(recs).slice(0,200)}`);
    o.houses = recs.filter(r => !r.error).map(r => ({
      name: r.title || r.product_name || r.name || null,
      brand: r.product_brand || r.brand || null,
      price: (r.final_price ?? r.price) != null ? `$${r.final_price ?? r.price}` : null,
      size: r.unit || r.size || "",
      img: r.image_url || (Array.isArray(r.images) ? r.images[0] : null) || null,
      link: r.url || null,
      upc: r.item_number || r.upc || null,
      availability: r.availability || r.availability_text || null,
      initial_price: r.initial_price ?? null, rating: r.rating ?? null, reviews: r.reviews_count ?? null,
    })).filter(h => h.name && h.price);
    const errs = recs.filter(r => r.error); if (errs.length) lg(`${errs.length} errored inputs: ${String(errs[0].error).slice(0,120)}`);
    const sid = recs.find(r => r.store_id)?.store_id;
    o.store_set = `API zip ${block.store_zip}${sid ? ` store_id ${sid}` : ""} (dataset ${a.dataset_id})`;
    lg(`extracted ${o.houses.length} houses from ${recs.length} records`);
  } catch (e) { o.error = String(e).slice(0, 500); lg(`ERROR ${o.error}`); }
  fs.writeFileSync(path.join(outDir2, `${day2}.json`), JSON.stringify(o, null, 2));
  console.log(`\nRESULT block=${o.block_id} store=${o.store_set} houses=${o.houses.length} error=${o.error}`);
  process.exit(o.error ? 1 : 0);
}

const baseUser = process.env.BRD_BROWSER_USER;
const pass = process.env.BRD_BROWSER_PASSWORD;
if (!baseUser || !pass) { console.error("missing BRD_BROWSER_USER / BRD_BROWSER_PASSWORD"); process.exit(2); }
const country = (block.country || process.env.BRD_COUNTRY || "us").toLowerCase();
const user = `${baseUser}-country-${country}`;
const wsEndpoint = `wss://${user}:${pass}@brd.superproxy.io:9222`;

const stamp = new Date().toISOString(); const day = stamp.slice(0, 10);
const outDir = path.join("data", block.retailer, block.block_id.replace(/[^a-z0-9@_.-]/gi, "_"));
fs.mkdirSync(outDir, { recursive: true });
const out = { block_id: block.block_id, retailer: block.retailer, zip: block.zip || null, neighborhood: block.neighborhood || block.search_term || null,
  pulled_at: stamp, runner: "github-actions+brightdata-scraping-browser", country, store_requested_zip: block.store_zip || null,
  store_set: null, url_final: null, houses: [], raw_text_chars: 0, steps: [], error: null };
const log = (m) => { console.log(m); out.steps.push(`${new Date().toISOString().slice(11, 19)} ${m}`); };
const rx = (t) => new RegExp(t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i");

async function firstVisible(locs, timeout) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    for (const l of locs) { try { if (await l.first().isVisible()) return l.first(); } catch {} }
    await new Promise(r => setTimeout(r, 300));
  }
  return null;
}
const rxExact = (t) => new RegExp("^\\s*" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\s*$", "i");
// exact: whole-label match on buttons/links first (prevents "Select" matching a "25% off Select ..." promo), then exact text.
const byText = (page, t, exact = true) => exact
  ? [page.getByRole("button", { name: rxExact(t) }), page.getByRole("link", { name: rxExact(t) }), page.getByText(rxExact(t))]
  : [page.getByRole("button", { name: rx(t) }), page.getByRole("link", { name: rx(t) }), page.getByText(rx(t))];

async function runStep(page, step) {
  const kind = Object.keys(step).find(k => !["note", "optional", "timeout"].includes(k));
  const v = step[kind]; const to = step.timeout ?? 8000;
  try {
    switch (kind) {
      case "goto": { for (let a = 1; a <= 4; a++) { try { await page.goto(sub(v), { waitUntil: "domcontentloaded", timeout: 120000 }); break; } catch (e) { if (a === 4 || !/rate limit|bucket_rate|no_peer|502|No Peer/i.test(String(e))) throw e; log(`rate limited, retry ${a}`); await page.waitForTimeout(8000 * a); } } log(`goto ${sub(v)}`); break; }
      case "wait": await page.waitForTimeout(v); break;
      case "dismiss": { // click any of these if visible; never fails
        const l = await firstVisible([].concat(...v.map(t => byText(page, t, false))), Math.min(to, 5000));
        if (l) { await l.click({ timeout: 3000 }).catch(() => {}); log(`dismissed "${(await l.textContent().catch(() => v[0]))?.trim().slice(0, 30)}"`); } else log("dismiss: nothing to close"); break; }
      case "click": { const l = await firstVisible(byText(page, sub(v)), to); if (!l) throw new Error(`click: "${v}" not found`); await l.click(); log(`click "${v}"`); break; }
      case "click_any": { const l = await firstVisible([].concat(...v.map(t => byText(page, sub(t)))), to); if (!l) throw new Error(`click_any: none of ${JSON.stringify(v)}`); await l.click(); log(`click_any -> "${(await l.textContent().catch(() => ""))?.trim().slice(0, 40)}"`); break; }
      case "fill": { // {fill:{placeholder|label|role, value}}
        const cands = []; if (v.placeholder) cands.push(page.getByPlaceholder(rx(v.placeholder))); if (v.label) cands.push(page.getByLabel(rx(v.label)));
        cands.push(page.getByRole(v.role || "textbox")); const l = await firstVisible(cands, to); if (!l) throw new Error("fill: no input found");
        await l.fill(sub(v.value)); log(`fill "${sub(v.value)}"`); if (v.enter !== false) { await l.press("Enter"); log("press Enter"); } break; }
      case "search": { const cands = [page.getByRole("searchbox")]; if (v.placeholder) cands.unshift(page.getByPlaceholder(rx(v.placeholder)));
        cands.push(page.getByRole("textbox", { name: /search/i }), page.locator("input[type=search]"), page.locator("input[name*=search i], input[id*=search i]"));
        const l = await firstVisible(cands, to); if (!l) throw new Error("search: no search box"); await page.keyboard.press("Escape").catch(() => {}); await l.fill(sub(v.term || "{{term}}"), { force: true }); await l.press("Enter"); log(`search "${sub(v.term || "{{term}}")}"`); break; }
      case "scroll": for (let i = 0; i < (v || 3); i++) { await page.mouse.wheel(0, 2500); await page.waitForTimeout(1000); } log(`scrolled x${v || 3}`); break;
      case "dump": { const ctl = await page.evaluate(() => Array.from(document.querySelectorAll("button,a,input,select,textarea,[role=button],[role=combobox],[role=radio],[role=option]")).map(e => ({ tag: e.tagName.toLowerCase(), type: e.getAttribute("type"), name: e.getAttribute("name"), vis: !!(e.offsetWidth || e.offsetHeight), text: (e.innerText || e.value || "").trim().slice(0, 60), aria: e.getAttribute("aria-label"), ph: e.getAttribute("placeholder"), tid: e.getAttribute("data-testid"), id: e.id || null, cls: (e.className && String(e.className).slice(0,50)) || null, href: e.getAttribute("href")?.slice(0, 80) || null })).filter(c => c.text || c.aria || c.ph || c.tag === "input" || c.tag === "textarea").slice(0, 600)); const txt = await page.evaluate(() => { const dlg = document.querySelector("[role=dialog], [aria-modal=true], .modal, [class*=modal i], [class*=flyout i], [class*=drawer i]"); return ("DIALOG: " + ((dlg && dlg.innerText) || "").slice(0, 2500) + "\nBODY: " + document.body.innerText.slice(0, 3500)); }); out.controls = (out.controls || []).concat([{ at: v, text: txt, controls: ctl }]); log(`dump ${v}: ${ctl.length} controls`); break; }
      case "click_re": { const re = new RegExp(v, "i"); const ok = await page.evaluate((src) => { const re = new RegExp(src, "i"); const els = Array.from(document.querySelectorAll("button,a,[role=button]")); const el = els.find(e => re.test((e.innerText || "").trim()) || re.test((e.getAttribute("aria-label") || "").trim())); if (el) { el.click(); return true; } return false; }, v); if (!ok && !step.optional) throw new Error(`click_re no match ${v}`); log(`click_re ${v} ${ok}`); break; }
      case "click_sel": { let last; for (let a = 0; a < 3; a++) { try { await page.click(sub(v), { timeout: 10000 }); log(`click_sel ${v}`); last = null; break; } catch (e) { last = e; await page.waitForTimeout(3000); } } if (last) { if (!step.optional) throw last; log(`click_sel miss ${v}`); } break; }
      case "type_sel": { const l = page.locator(sub(v.sel)).first(); try { await l.waitFor({ state: "visible", timeout: 25000 }); await l.click({ timeout: 10000, force: true }); await l.fill(""); await page.keyboard.type(sub(v.value), { delay: 40 }); if (v.enter !== false) await page.keyboard.press("Enter"); log(`type_sel ${v.sel} "${sub(v.value)}"`); } catch (e) { if (!step.optional) throw e; log(`type_sel miss ${v.sel}`); } break; }
      case "js": { let last; for (let a = 0; a < 4; a++) { try { const r = await page.evaluate(`(async()=>{ ${sub(v)} })()`); log(`js ok ${String(r ?? "").slice(0, 80)}`); (out.js_results = out.js_results || []).push(String(r ?? "").slice(0, 4000)); last = null; break; } catch (e) { last = e; await page.waitForTimeout(3000); } } if (last) { if (!step.optional) throw last; log(`js miss ${String(last).slice(0, 80)}`); } break; }
      case "netlog": { out.net = out.net || []; const want = new RegExp(v && v !== "on" ? v : "Chooser|Location|VisitShop|Retailer|Shop\\b|Address|Postal|Geolocation", "i");
        page.on("request", r => { const u = r.url(); if (/graphql/i.test(u) && want.test(u + (r.postData() || ""))) out.net.push({ m: r.method(), u: u.slice(0, 2500), b: (r.postData() || "").slice(0, 1500), t: Date.now() }); });
        page.on("response", async r => { const u = r.url(); if (/graphql/i.test(u) && want.test(u + (r.request().postData() || ""))) { try { const b = (await r.text()).slice(0, 6000); out.net.push({ resp: r.status(), u: u.slice(0, 200), b, t: Date.now() }); } catch {} } }); log("netlog on"); break; }
      case "type_dialog": { // type into the visible textbox inside the open dialog using real Playwright keystrokes
        const dlg = page.locator("[role=dialog], [aria-modal=true]").last(); const boxes = dlg.locator("input:not([type=hidden]):not([tabindex='-1']), [role=textbox], [contenteditable=true]"); const n = await boxes.count(); let picked = null;
        for (let i = 0; i < n; i++) { const b = boxes.nth(i); if (await b.isVisible().catch(() => false)) { picked = b; break; } }
        const info = await dlg.evaluate(d => Array.from(d.querySelectorAll("input,[role=textbox],[contenteditable=true]")).map(e => ({ tag: e.tagName, type: e.type, ph: e.placeholder, aria: e.getAttribute("aria-label"), tid: e.getAttribute("data-testid"), id: e.id, ti: e.tabIndex, vis: !!(e.offsetWidth || e.offsetHeight), val: e.value }))).catch(e => String(e));
        (out.js_results = out.js_results || []).push("dialog inputs: " + JSON.stringify(info).slice(0, 3000));
        if (!picked) { if (!step.optional) throw new Error("type_dialog: no visible textbox in dialog"); log("type_dialog miss"); break; }
        await picked.click({ timeout: 10000 }); await picked.pressSequentially(sub(v.value), { delay: 80 }); if (v.enter !== false) await picked.press("Enter"); log(`type_dialog "${sub(v.value)}"`); break; }
      case "type_marked": { // {sel, value, enter}: Playwright-native typing into a locator (real key events)
        const l = page.locator(sub(v.sel)).first(); try { await l.waitFor({ state: "visible", timeout: 15000 }); await l.scrollIntoViewIfNeeded(); await l.click({ timeout: 10000 }); await l.pressSequentially(sub(v.value), { delay: 90 }); if (v.enter) await l.press("Enter"); log(`type_marked ${v.sel}`); } catch (e) { if (!step.optional) throw e; log(`type_marked miss ${String(e).slice(0, 80)}`); } break; }
      case "js_houses": { try { const r = await page.evaluate(`(async()=>{ ${sub(v)} })()`); const j = typeof r === "string" ? JSON.parse(r) : r; out.js_houses = j.houses || []; out.js_store = j.store || null; out.js_debug = String(j.debug || "").slice(0, 3000); log(`js_houses ${out.js_houses.length} store ${out.js_store}`); } catch (e) { out.js_debug = String(e).slice(0, 500); if (!step.optional) throw e; log(`js_houses miss ${String(e).slice(0, 80)}`); } break; }
      case "press": await page.keyboard.press(v); log(`press ${v}`); break;
      default: log(`unknown step ${kind}`);
    }
  } catch (e) { if (step.optional) log(`optional step ${kind} skipped: ${String(e).slice(0, 80)}`); else throw e; }
}

async function captureStore(page, patterns) {
  const text = await page.evaluate(() => document.body.innerText);
  for (const p of patterns) { const m = text.match(new RegExp(p, "i")); if (m) return (m[1] || m[0]).trim().slice(0, 120); }
  return null;
}

async function extractProducts(page, cardSelector) {
  return await page.evaluate((cardSelector) => {
    const priceRe = /\$\s?\d{1,4}\.\d{2}/; const seen = new Set(); const items = [];
    let cards = cardSelector ? Array.from(document.querySelectorAll(cardSelector)) : [];
    if (!cards.length) {
      const leaves = Array.from(document.querySelectorAll("body *")).filter(el => el.childElementCount === 0 && priceRe.test(el.textContent || "") && (el.textContent || "").trim().length < 40);
      const nPrice = el => el.querySelectorAll ? Array.from(el.querySelectorAll("*")).filter(x => x.childElementCount === 0 && priceRe.test(x.textContent || "") && (x.textContent || "").trim().length < 40).length : 0;
      for (const el of leaves) { let c = el, best = el; for (let i = 0; i < 10 && c.parentElement; i++) { c = c.parentElement; const t = c.innerText || ""; if (t.length > 1500 || nPrice(c) > 3) break; best = c; } cards.push(best); }
    }
    for (const card of cards) {
      const txt = (card.innerText || "").trim(); if (!txt || seen.has(txt) || !priceRe.test(txt)) continue; seen.add(txt);
      const lines = txt.split("\n").map(s => s.trim()).filter(Boolean);
      const price = (txt.match(priceRe) || [""])[0].replace(/\s/g, "");
      const junk = /^(\$\d+$|[★☆\s]+$|\(\d[\d,.k]*\)$|buy \d|gluten|vegan|organic$|keto|low |non-gmo|original price|add|add to cart|sale|save|sponsored|\d+% off|.*de descuento|ship|pickup|delivery|in stock|low stock|snap|ebt|sign in|view offer|options|join prime|current price|original price|best seller|rated |\d+(\.\d+)? out of 5|\d+ reviews?|each|\$?\d+(\.\d+)?\s?(¢|\/|per)\s?\w+)/i;
      const cands = lines.filter(l => l.length > 3 && !priceRe.test(l) && !junk.test(l) && !/^\d+(\.\d+)?\s?(oz|fl oz|lb|ct|g|ml)\b/i.test(l));
      if (!cands.length) continue;                       // Prime sub-cards and price-only fragments
      const name = cands.reduce((a, b) => (b.length > a.length ? b : a), "");
      const brand = (cands[0] !== name && cands[0].length < 40) ? cands[0] : ((card.querySelector("[class*=brand i], [data-testid*=brand i]")?.textContent || "").trim() || null);
      const size = (txt.match(/\b\d+(\.\d+)?\s?(fl oz|fl\. oz|oz|ounce|lb|lbs|ct|count|g|ml|l)\b/i) || [""])[0];
      items.push({ name, brand, price, size, img: card.querySelector("img")?.src || null, link: card.querySelector("a[href]")?.href || null, card_text: lines.slice(0, 8) });
    }
    return items;
  }, cardSelector || null);
}

function extractFromText(text) {
  const priceRe = /^\$\s?\d{1,4}\.\d{2}$/; const anyPrice = /\$\s?\d{1,4}\.\d{2}/;
  const junk = /^(add|add to cart|sale|save|sponsored|\d+% off|ship|pickup|delivery|in stock|low stock|snap|ebt|sign in.*|view offer|options|current price.*|original price.*|your price.*|price per.*|\(.*\/.*\)|best seller|rated .*|\d+ reviews?|\d+|each|buy \d.*|price cut|now\$.*|clearance|[★☆ ]+|gluten-free|vegan|organic|low price|rollback|\d+(\.\d+)?\s?(oz|fl oz|lb|ct|g|ml)\b.*)$/i;
  const lines = text.split("\n").map(l => l.trim()).filter(Boolean); const items = []; const seen = new Set();
  for (let i = 0; i < lines.length; i++) {
    if (!priceRe.test(lines[i])) continue;
    const win = []; for (let j = Math.max(0, i - 5); j <= Math.min(lines.length - 1, i + 5); j++) if (j !== i) win.push(lines[j]);
    const cands = win.filter(l => l.length > 8 && l.length < 120 && /[a-z]/i.test(l) && !anyPrice.test(l) && !junk.test(l));
    if (!cands.length) continue;
    const name = cands.reduce((a, b) => (b.length > a.length ? b : a), ""); const key = name + "|" + lines[i];
    if (seen.has(key)) continue; seen.add(key);
    const size = (name.match(/\b\d+(\.\d+)?\s?(fl oz|fl\. oz|oz|ounce|lb|lbs|ct|count|g|ml)\b/i) || [""])[0];
    items.push({ name, brand: null, price: lines[i].replace(/\s/g, ""), size, img: null, link: null, card_text: [], via: "text" });
  }
  return items;
}

log(`auth user=${user} password_len=${pass.length} endpoint=brd.superproxy.io:9222`);
let browser = null, page = null;
try {
  browser = await chromium.connectOverCDP(wsEndpoint, { timeout: 120000 }); log("connected to Bright Data Scraping Browser");
  page = await browser.newPage(); page.setDefaultTimeout(60000); await page.setViewportSize({ width: 1440, height: 900 }).catch(() => {});
  const steps = block.steps || [{ goto: block.home_url }, { wait: 3000 }, { search: {} }, { wait: 5000 }, { scroll: 4 }];
  for (const step of steps) {
    await runStep(page, step);
    if (step.goto) { try { const cdp = await page.context().newCDPSession(page); await cdp.send("Captcha.waitForSolve", { detectTimeout: 8000 }); log("captcha check passed"); } catch (e) { log(`captcha hook: ${String(e).slice(0, 60)}`); } }
  }
  out.url_final = page.url();
  if (block.store_js) { try { out.store_set = await page.evaluate(block.store_js); } catch (e) { log(`store_js failed ${String(e).slice(0,60)}`); } }
  if (!out.store_set) out.store_set = await captureStore(page, block.store_patterns || ["Delivering to\\s*(\\d{5})", "Pickup at\\s*([^\\n|]{3,60})", "(?:My Store|Your store|Shopping at|Store:)\\s*[:\\-]?\\s*([^\\n]{3,80})"]);
  log(`store_set: ${out.store_set}`);
  out.houses = await extractProducts(page, block.card_selector);
  let text = await page.evaluate(() => document.body.innerText); out.raw_text_chars = text.length;
  if (out.houses.length < 5 && !block.no_reload) { log("few houses, reloading once"); await page.reload({ waitUntil: "domcontentloaded", timeout: 120000 }).catch(() => {}); await page.waitForTimeout(8000); for (let i = 0; i < 3; i++) { await page.mouse.wheel(0, 1500); await page.waitForTimeout(1500); } out.houses = await extractProducts(page, block.card_selector); text = await page.evaluate(() => document.body.innerText); out.raw_text_chars = text.length; out.reloaded = true; }
  const fromText = extractFromText(text); out.houses_text = fromText.length;
  if (fromText.length > out.houses.length) { log(`text parser wins: ${fromText.length} vs ${out.houses.length}`); out.houses_dom = out.houses.length; out.houses = fromText; }
  if (out.js_houses && out.js_houses.length) { out.houses_page = out.houses.length; out.houses = out.js_houses; if (out.js_store) out.store_set = out.js_store; log(`js_houses override: ${out.houses.length}`); }
  fs.writeFileSync(path.join(outDir, `${day}.txt`), text);
  await page.screenshot({ path: path.join(outDir, `${day}.png`) });
  log(`extracted ${out.houses.length} houses; raw text ${text.length} chars`);
} catch (e) {
  out.error = String(e).slice(0, 500); log(`ERROR ${out.error}`);
  try { if (page) await page.screenshot({ path: path.join(outDir, `${day}-error.png`) }); } catch {}
} finally {
  fs.writeFileSync(path.join(outDir, `${day}.json`), JSON.stringify(out, null, 2));
  try { if (browser) await browser.close(); } catch {}
}
console.log(`\nRESULT block=${out.block_id} store=${out.store_set} houses=${out.houses.length} error=${out.error}`);
if (out.error) process.exit(1);
