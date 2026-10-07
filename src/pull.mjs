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
      case "goto": await page.goto(sub(v), { waitUntil: "domcontentloaded", timeout: 120000 }); log(`goto ${sub(v)}`); break;
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
      for (const el of leaves) { let c = el; for (let i = 0; i < 8 && c.parentElement; i++) { c = c.parentElement; const t = c.innerText || ""; if (t.length > 40 && t.length < 900 && /\n/.test(t)) break; } cards.push(c); }
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

log(`auth user=${user} password_len=${pass.length} endpoint=brd.superproxy.io:9222`);
let browser = null, page = null;
try {
  browser = await chromium.connectOverCDP(wsEndpoint, { timeout: 120000 }); log("connected to Bright Data Scraping Browser");
  page = await browser.newPage(); page.setDefaultTimeout(60000);
  const steps = block.steps || [{ goto: block.home_url }, { wait: 3000 }, { search: {} }, { wait: 5000 }, { scroll: 4 }];
  for (const step of steps) {
    await runStep(page, step);
    if (step.goto) { try { const cdp = await page.context().newCDPSession(page); await cdp.send("Captcha.waitForSolve", { detectTimeout: 8000 }); log("captcha check passed"); } catch (e) { log(`captcha hook: ${String(e).slice(0, 60)}`); } }
  }
  out.url_final = page.url();
  out.store_set = await captureStore(page, block.store_patterns || ["Delivering to\\s*(\\d{5})", "Pickup at\\s*([^\\n|]{3,60})", "(?:My Store|Your store|Shopping at|Store:)\\s*[:\\-]?\\s*([^\\n]{3,80})"]);
  log(`store_set: ${out.store_set}`);
  out.houses = await extractProducts(page, block.card_selector);
  const text = await page.evaluate(() => document.body.innerText); out.raw_text_chars = text.length;
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
