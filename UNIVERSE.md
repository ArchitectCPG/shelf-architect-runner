# Shelf Architect runner: 241-banner universe bucketed by platform (read-only from the DB, 2026-10-13)

Source: retailers collection in the Shelf Architect DB, 241 docs. Nothing written back. Platform column is my assignment from the parent company and known e-commerce stacks; 'verify' means the banner's storefront stack has not been probed yet.

## Families with one recipe each (status)

| family | banners | recipe status |
|---|---|---|
| kroger | 16 | DONE, unattended store pinning (7 tested) |
| albertsons | 12 banners + 7 division docs | DONE, unattended store pinning (8 tested) |
| ahold (Stop & Shop, Giant, Giant Food, Food Lion, Hannaford) | 7 | NOT STARTED, probing now |
| costco | 1 + 8 regions | blocked on KYC |
| meijer | 1 | DONE |
| target | 1 | pulls, unpinned (zip lookup blocked in cloud) |
| walmart | 1 | mapped, not verified; Bright Data scraper lane preferred |
| hyvee, publix, wegmans, aldi, gianteagle, heb | 8 | probing now |
| amazon (Whole Foods, Fresh, Go) | 3 | Whole Foods recipe exists (flaky) |
| cvs, walgreens, dollargeneral, samsclub, bjs | 6 | blocked or errored at goto last sweep |
| c-store, no e-comm (7-Eleven, Circle K, Wawa, Sheetz, Speedway, QuikTrip, Maverik, Trader Joe's, WinCo, Grocery Outlet, DeCA, NEX, Hungryroot) | 13 | no online shelf to pull; presence only |
| independents and regionals | 146 | each is Instacart whitelabel, Freshop, Mercatus or own site; needs a one-time probe per banner |

## Independents and regionals, by doors (probe order)

| id | name | state | doors | prio |
|---|---|---|---|---|
| save-a-lot | Save A Lot |  | 777 |  |
| sprouts | Sprouts Farmers Market | Arizona | 512 | 5 |
| key-food | Key Food | New York | 420 | 2 |
| associated-food-stores | Associated Food Stores (AFS) | Utah | 400 | 4 |
| houchens | Houchens | Kentucky | 400 | 2 |
| infra | INFRA | Minnesota | 360 | 5 |
| otg-cibo-markets | OTG Cibo Markets | New York | 350 | 4 |
| wakefern-shoprite-price-rite-the-fresh-grocer | Wakefern - Shoprite, Price Rite, The Fresh Grocer | New Jersey | 340 | 3 |
| smart-final | Smart & Final | California | 254 | 3 |
| ncg | NCG | Minnesota | 230 | 5 |
| shoprite | ShopRite |  | 225 |  |
| weis-markets | Weis Markets | Pennsylvania | 197 | 3 |
| lucky-s-savemart | Lucky's & SaveMart | California | 194 | 4 |
| brookshire-grocery | Brookshire Grocery Company | Texas | 180 | 3 |
| the-fresh-market | The Fresh Market | North Carolina | 173 | 4 |
| natural-grocers | Natural Grocers |  | 171 |  |
| natural-grocers-vitamin-cottage | Natural Grocers / Vitamin Cottage | Colorado | 171 | 4 |
| stater-bros | Stater Bros. Markets |  | 166 |  |
| stater-brothers | Stater Brothers | California | 166 | 3 |
| spartannash | SpartanNash | Michigan | 150 | 2 |
| northeast-grocers-tops | Northeast Grocers - Tops | New York | 148 | 3 |
| coborn-s-cashwise-marketplace-foods-hornbacher-s | Coborn's (Cashwise, Marketplace Foods, Hornbacher's) | Minnesota | 135 | 3 |
| ingles | Ingles | North Carolina | 134 | 2 |
| northeast-grocers-price-chopper | Northeast Grocers - Price Chopper | New York | 130 | 3 |
| schnucks | Schnucks | Missouri | 127 | 3 |
| plaid-pantry | Plaid Pantry | Oregon | 107 | 3 |
| brookshire-brothers | Brookshire Brothers | Texas | 97 | 2 |
| market-basket | Market Basket |  | 95 |  |
| market-basket-demoula-s | Market Basket / Demoula's | Massachusetts | 95 | 3 |
| big-y | Big Y | Massachusetts | 94 | 2 |
| bravo-supermarkets | Bravo Supermarkets | New York | 91 | 2 |
| hmart | H Mart | New Jersey | 88 | 3 |
| northwest-grocer | Northwest Grocer | Washington | 88 | 4 |
| lowe-s-foods | Lowe's Foods | North Carolina | 83 | 2 |
| cub-foods | Cub | Minnesota | 77 | 3 |
| bashas | Bashas' | Arizona | 74 | 2 |
| raleys | Raley's | California | 74 | 5 |
| foodtown | Foodtown | New Jersey | 73 | 3 |
| fresh-thyme-market | Fresh Thyme Market | Illinois | 69 | 5 |
| redner-s-markets | Redner's Markets | Pennsylvania | 68 | 3 |
| rouses-markets | Rouses Markets | Louisiana | 66 | 3 |
| fiesta-mart | Fiesta Mart | Texas | 65 | 2 |
| loop-neighborhood-market | Loop Neighborhood Market | California | 62 | 3 |
| food-city-az | Food City (AZ) |  | 48 |  |
| festival-foods | Festival Foods | Wisconsin | 42 | 3 |
| wakefern-village-supermarket-fairway-gourmet-garage-select-shoprites | Wakefern - Village Supermarket - Fairway, Gourmet Garage, select Shoprites | New Jersey | 40 | 5 |
| c-k-market | C&K Market | Oregon | 36 | 3 |
| hugo-s | Hugo's | Illinois | 35 | 2 |
| cosentinos-food-stores | Cosentinos Food Stores | Kansas | 32 | 3 |
| food-bazaar | Food Bazaar | New York | 32 | 3 |
| miners-super-one | Miners / Super One | Minnesota | 32 | 2 |
| foodland | Foodland | Hawaii | 30 | 4 |
| america-s-food-basket | America's Food Basket | New York | 27 | 3 |
| d-agostinos-gristedes | D'agostinos & Gristedes | New York | 27 | 3 |
| lunds-byerlys | Lunds & Byerlys |  | 27 |  |
| mom-s-organic-market | Mom's Organic Market | Virginia | 27 | 5 |
| dierberg-s | Dierberg's | Missouri | 26 | 3 |
| gelsons | Gelson's | California | 26 | 5 |
| lunds-byerly-s | Lunds & Byerly's | Minnesota | 26 | 3 |
| king-kullen | King Kullen | New York | 25 | 2 |
| times-supermarket | Times Supermarket | Hawaii | 24 | 4 |
| heinen-s-fine-foods | Heinen's Fine Foods | Ohio | 23 | 3 |
| new-seasons | New Seasons | Oregon | 22 | 4 |
| strack-van-til | Strack & Van Til | Indiana | 22 | 3 |
| vantils | Van Til's Super Market |  | 22 |  |
| petes-market | Pete's Market | Illinois | 21 | 4 |
| rosauers-huckleberries | Rosauers/Huckleberries | Washington | 21 | 2 |
| tonys-fresh-market | Tony's Fresh Market | Illinois | 21 | 2 |
| berkot-s-super-foods | Berkot's Super Foods | Illinois | 20 | 4 |
| harmons | Harmons | Utah | 20 | 5 |
| roche-bros | Roche Bros. |  | 20 |  |
| roche-brothers | Roche Brothers | Massachusetts | 20 | 2 |
| woodmans | Woodmans | Wisconsin | 20 | 2 |
| yoke-s | Yoke's | Washington | 19 | 3 |
| sendik-s | Sendik's | Wisconsin | 17 | 2 |
| busch-s | Busch's | Michigan | 16 | 3 |
| nugget | Nugget | California | 16 | 4 |
| pcc-community-markets | PCC Community Markets | Washington | 16 | 5 |
| super-1-foods | Super 1 Foods | Washington | 16 | 5 |
| buehler-s-fresh-foods | Buehler's Fresh Foods | Ohio | 15 | 4 |
| morton-williams | Morton Williams | New York | 15 | 3 |
| better-health | Better Health | Michigan | 14 | 5 |
| bristol-farms | Bristol Farms | California | 14 | 5 |
| erewhon | Erewhon | California | 14 | 5 |
| earth-fare | Earth Fare | North Carolina | 13 | 5 |
| fresh-encounters | Fresh Encounters | Ohio | 13 | 3 |
| market-of-choice | Market of Choice | Oregon | 13 | 4 |
| mother-s-market | Mother's Market | California | 12 | 5 |
| uncle-guiseppe-s | Uncle Guiseppe's | New York | 12 | 2 |
| fruitful-yield | Fruitful Yield | Illinois | 11 | 5 |
| hitchcock-s | Hitchcock's | Florida | 11 | 4 |
| kowalski-s | Kowalski's | Minnesota | 11 | 3 |
| raley-s-aj-s-finest-foods | Raley's - AJ's Finest Foods | Arizona | 11 | 4 |
| angelo-caputos-fresh-market | Angelo Caputos Fresh Market | Illinois | 10 | 3 |
| baron-s | Baron's | California | 10 | 5 |
| dave-s-marketplace | Dave's Marketplace | Rhode Island | 10 | 4 |
| lassen-s | Lassen's | California | 10 | 5 |
| metropolitan-market | Metropolitan Market | Washington | 10 | 5 |
| sullivan-s | Sullivan's | Mississippi | 10 | 4 |
| decicco-s-decicco-sons | Decicco's - DeCicco & Sons | New York | 9 | 5 |
| kimberton-whole-foods | Kimberton Whole Foods | Pennsylvania | 9 | 4 |
| mccaffrey-s | McCaffrey's | Pennsylvania | 9 | 3 |
| mollie-stones | Mollie Stones | California | 9 | 4 |
| citarella | Citarella | New York | 8 | 5 |
| good-earth-market | Good Earth Market | Utah | 8 | 5 |
| greens-natural | Greens Natural | New York | 8 | 4 |
| lunardi-s | Lunardi's | California | 8 | 2 |
| stew-leonards | Stew Leonards | Connecticut | 8 | 3 |
| crosby-s | Crosby's | Oklahoma | 7 | 3 |
| hornbachers | Hornbachers | North Dakota | 7 | 2 |
| milams-markets | Milam's Markets | Florida | 7 | 2 |
| sunset-foods | Sunset Foods | Illinois | 7 | 2 |
| detwiler-s-farm-market | Detwiler's Farm Market | Florida | 6 | 4 |
| down-to-earth | Down to Earth | Hawaii | 6 | 5 |
| lazy-acres | Lazy Acres | California | 6 | 5 |
| plum-market | Plum Market | Michigan | 6 | 4 |
| town-and-country | Town and Country | Oregon | 6 | 5 |
| union-market | Union Market | New York | 6 | 4 |
| yes-organic | Yes Organic | District of Columbia | 6 | 4 |
| dick-s-fresh-market | Dick's Fresh Market | Wisconsin | 5 | 3 |
| earth-origins | Earth Origins | Florida | 5 | 5 |
| gus-s-community-market | Gus's Community Market | California | 5 | 5 |
| healthier-choices-management-green-acres | Healthier Choices Management - Green Acres | Kansas | 5 | 5 |
| jerry-s-fine-foods | Jerry's Fine Foods | Minnesota | 5 | 2 |
| new-leaf | New Leaf | California | 5 | 4 |
| save-more-foods | Save More Foods |  | 5 |  |
| caraluzzi-s-market | Caraluzzi's Market | Connecticut | 4 | 5 |
| donelan-s-fresh-market | Donelan's Fresh Market | Massachusetts | 4 | 3 |
| fairway-market | Fairway Market |  | 4 |  |
| frazier-farms | Frazier Farms | California | 4 | 5 |
| fresh-farms | Fresh Farms | Illinois | 4 | 4 |
| jensen-s | Jensen's | California | 4 | 4 |
| jimbo-s-naturally | Jimbo's Naturally | California | 4 | 5 |
| landis-market | Landis Market | Pennsylvania | 4 | 4 |
| luke-s-local | Luke's Local | California | 4 | 0 |
| national-coop-group-outpost-coop | National Coop Group - Outpost Coop | Wisconsin | 4 | 5 |
| niemann-s | Niemann's | Illinois | 4 | 2 |
| oliver-s | Oliver's | California | 4 | 4 |
| wild-by-nature | Wild by Nature | New York | 4 | 4 |
| clark-s-nutrition | Clark's Nutrition | California | 3 | 5 |
| fairplay-foods | Fairplay Foods |  | 3 |  |
| woodlands | Woodlands | California | 3 | 5 |
| yummy-foods | Yummy Foods | California | 3 | 3 |
| berkeley-bowl | Berkeley Bowl | California | 2 | 5 |
| draeger-s | Draeger's | California | 2 | 4 |
| jungle-jim-s | Jungle Jim's | Ohio | 2 | 4 |
| knowlan-s | Knowlan's | Minnesota | 2 | 2 |
| mustard-seed | Mustard Seed | Ohio | 2 | 5 |
| good-eggs | Good Eggs | California |  | 5 |

## Probe plan (unattended)

For each independent, the runner tries candidate search URLs in order and keeps the first that yields product cards: (1) https://shop.<domain>/search?search_term=salsa (Freshop/Mercatus), (2) https://www.instacart.com/store/<slug>/s?k=salsa (Instacart storefront, pulls without store pinning), (3) https://shop.<domain>/store/<slug>/s?k=salsa (Instacart whitelabel), (4) the banner's own site search. Result recorded per banner as pull_routes-style notes in the runner README, not in the DB, until Steve OKs.
Instacart routes cannot pin a store unattended (login wall). For independents that is acceptable for a first pass: assortment and price at the default store, flagged 'unpinned'.