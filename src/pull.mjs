// Shelf Architect runner: drives Bright Data's Scraping Browser (remote Chromium over CDP)
// to walk one retailer block: set a store, search a term, capture products + prices.
// Usage: node src/pull.mjs blocks/<block>.json
import { chromium } from "playwright-core";
import fs from "node:fs";
import path from "node:path";

const blockFile = process.argv[2];
if (!blockFile) { console.error("usage: node src/pull.mjs blocks/<block>.json"); process.exit(2); }
const block = JSON.parse(fs.readFileSync(blockFile, "utf8"));

const user = process.env.BRD_BROWSER_USER;          // brd-customer-<id>-zone-<zone>
const pass = process.env.BRD_BROWSER_PASSWORD;      // repo secret
if (!user || !pass) { console.error("missing BRD_BROWSER_USER / BRD_BROWSER_PASSWORD"); process.exit(2); }
const wsEndpoint = `wss://${user}:${pass}@brd.superproxy.io:9222`;

const stamp = new Date().toISOString();
const day = stamp.slice(0, 10);
const outDir = path.join("data", block.retailer, block.block_id.replace(/[^a-z0-9@_-]/gi, "_"));
fs.mkdirSync(outDir, { recursive: true });
const out = { block_id: block.block_id, retailer: block.retailer, pulled_at: stamp, runner: "github-actions+brightdata-scraping-browser",
              store_requested_zip: block.store_zip, store_set: null, search_term: block.search_term, url_final: null,
              houses: [], raw_text_chars: 0, steps: [], error: null };
const log = (m) => { console.log(m); out.steps.push(`${new Date().toISOString().slice(11,19)} ${m}`); };

async function clickByText(page, texts, timeout = 8000) {
  for (const t of texts) {
    const loc = page.getByRole("button", { name: new RegExp(t, "i") }).first();
    try { await loc.waitFor({ state: "visible", timeout }); await loc.click(); log(`clicked button "${t}"`); return true; } catch {}
    const loc2 = page.getByText(new RegExp(`^\\s*${t}\\s*$`, "i")).first();
    try { await loc2.waitFor({ state: "visible", timeout: 2000 }); await loc2.click(); log(`clicked text "${t}"`); return true; } catch {}
  }
  return false;
}

// Generic product-card extraction: any element with a $x.xx price, walk up to a card-ish ancestor.
async function extractProducts(page) {
  return await page.evaluate(() => {
    const priceRe = /\$\s?\d{1,4}\.\d{2}/;
    const seen = new Set(); const items = [];
    const nodes = Array.from(document.querySelectorAll("body *")).filter(el => {
      const t = (el.childElementCount === 0 ? el.textContent : "") || "";
      return priceRe.test(t) && t.trim().length < 40;
    });
    for (const el of nodes) {
      let card = el;
      for (let i = 0; i < 8 && card.parentElement; i++) {
        card = card.parentElement;
        const txt = card.innerText || "";
        if (txt.length > 40 && txt.length < 900 && /\n/.test(txt)) break;
      }
      const txt = (card.innerText || "").trim();
      if (!txt || seen.has(txt)) continue; seen.add(txt);
      const lines = txt.split("\n").map(s => s.trim()).filter(Boolean);
      const price = (txt.match(priceRe) || [""])[0].replace(/\s/g, "");
      const name = lines.find(l => l.length > 8 && !priceRe.test(l) && !/add|cart|sale|save|\d+ ?(oz|lb|ct|fl)/i.test(l)) || lines[0];
      const size = (txt.match(/\b\d+(\.\d+)?\s?(oz|fl oz|lb|lbs|ct|g|ml|l)\b/i) || [""])[0];
      const img = card.querySelector("img")?.src || null;
      const link = card.querySelector("a[href]")?.href || null;
      items.push({ name, price, size, img, link, card_text: lines.slice(0, 8) });
    }
    return items;
  });
}

log(`auth user=${user} password_len=${pass.length} endpoint=brd.superproxy.io:9222`);
let browser = null, page = null;
try {
  browser = await chromium.connectOverCDP(wsEndpoint, { timeout: 120000 });
  log("connected to Bright Data Scraping Browser");
  page = await browser.newPage();
  page.setDefaultTimeout(60000);
  await page.goto(block.home_url, { waitUntil: "domcontentloaded", timeout: 120000 });
  log(`loaded ${block.home_url}`);
  // Let Bright Data auto-solve any challenge.
  try { const cdp = await page.context().newCDPSession(page); await cdp.send("Captcha.waitForSolve", { detectTimeout: 10000 }); log("captcha check passed"); } catch (e) { log(`captcha hook n/a: ${String(e).slice(0,80)}`); }
  await page.waitForTimeout(3000);

  // 1) Set store
  if (await clickByText(page, block.store_button_texts)) {
    await page.waitForTimeout(2000);
    const zipBox = page.getByRole("textbox").filter({ hasNot: page.locator("[type=password]") }).first();
    try { await zipBox.waitFor({ timeout: 10000 }); await zipBox.fill(block.store_zip); await zipBox.press("Enter"); log(`entered zip ${block.store_zip}`); } catch { log("no zip textbox found after store click"); }
    await page.waitForTimeout(4000);
    const picked = await clickByText(page, ["Make this my store", "Select this store", "Make my store", "Shop this store", "Select store", "Choose store"], 6000);
    if (!picked) {
      // fall back: click the first store result card
      try { await page.locator("button, a").filter({ hasText: /store|select|shop/i }).nth(1).click({ timeout: 5000 }); log("clicked first store-ish control"); } catch { log("could not pick a store result"); }
    }
    await page.waitForTimeout(4000);
  } else { log("no store button found; continuing with site default"); }
  out.store_set = await page.evaluate(() => (document.body.innerText.match(/(?:My Store|Your store|Shopping at|Store:)\s*[:\-]?\s*([^\n]{3,80})/i) || [null, null])[1]);
  log(`store_set: ${out.store_set}`);

  // 2) Search
  let searched = false;
  for (const hint of block.search_input_hints) {
    const box = page.getByRole("searchbox").first().or(page.getByPlaceholder(new RegExp(hint, "i")).first()).or(page.getByRole("textbox", { name: new RegExp(hint, "i") }).first());
    try { await box.waitFor({ timeout: 6000 }); await box.fill(block.search_term); await box.press("Enter"); searched = true; log(`searched "${block.search_term}" via "${hint}"`); break; } catch {}
  }
  if (!searched) { const u = `${block.home_url}?search=${encodeURIComponent(block.search_term)}`; await page.goto(u, { waitUntil: "domcontentloaded" }); log(`fallback search url ${u}`); }
  await page.waitForTimeout(6000);
  for (let i = 0; i < 4; i++) { await page.mouse.wheel(0, 2500); await page.waitForTimeout(1200); }
  out.url_final = page.url();

  // 3) Extract
  out.houses = await extractProducts(page);
  const text = await page.evaluate(() => document.body.innerText);
  out.raw_text_chars = text.length;
  fs.writeFileSync(path.join(outDir, `${day}.txt`), text);
  await page.screenshot({ path: path.join(outDir, `${day}.png`), fullPage: false });
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
