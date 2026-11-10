# Shelf Architect intake v2

Goal: collect everything the client already knows before any pull runs. Steve forwards this to the client or fills it on the call (30 min). Opus writes the answers into client_config and discovery, then runs the seed script. Anything left blank gets a pre-filled default on the decision sheets, flagged as a guess.

## 1. Company
- Brand, website, legal name
- Total revenue and split by channel (retail, DTC, Amazon, foodservice, gifting, own stores)
- Fiscal year (default: calendar year, Jan to Dec)
- Decision makers (names, roles) and who signs off on pricing

## 2. Current retail (the existing business)
- Every retailer carrying the brand today: account, approximate doors, which SKUs, which set (aisle, deli, endcap)
- Current SRP by SKU and account
- Velocity if known (units per store per week, SPINS, vendor portal, or "don't know")
- Distributor per account (UNFI, KeHE, direct, broker) and terms if known

## 3. Product and cost
- Full SKU list with pack size, count and format
- COGS per SKU, or "use margin calculator ceilings"
- Shelf life and storage (ambient, refrigerated, frozen)
- Manufacturing capabilities and limits (what they can and cannot make)

## 4. What is launching
- New SKUs or formats, SRP, launch month, which accounts first
- Staging (all at once, or in drops: how many SKUs, when)
- Pipeline after that (next flavors, timing)

## 5. Where they want to go
- Target channels and banners, banners to avoid
- Markets (national, regional, home market)
- Competitors: real and perceived, by category

## 6. Other programs
- Private label: who, what product, status
- Amazon: own storefront, through a retailer, or none
- DTC and gifting priorities

## 7. Tool settings
- data_mode: scrape, syndicated or hybrid (syndicated files available?)
- data_sharing: shared or isolated
- framing: current state or point in time

## Output (Opus, same session)
- client_config/<id>, discovery/<id>, clients/<id>.json in the runner (channels, terms, relevance, hard_exclude, store pins per banner)
- Current-state rows (existing SKUs, doors, SRP) seeded as brand rows before Stage 0, so the brand term pull confirms instead of discovers

## v85 amendments (2026-11-10)
- Two modes. Client: the client fills this or Steve fills it on the call. Prospect: Steve fills what he knows, public sources fill the rest.
- A blank never blocks. It takes a default, is flagged as a guess, and shows on a decision sheet.
- Current-state SKUs, doors and SRP are written as expected doors (matrix.expectations.client_present, clients/<id>.json own_products, client_config.current_retail). They are never written as retail_entries rows. The pull confirms them.
- The runner config written from this intake must carry relevance, hard_exclude and store_expect for every block.
