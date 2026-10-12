#!/usr/bin/env python3
"""
Ziba Roofing — static site generator.

Run:  python3 build_site.py
Out:  ./site/   (deployable as-is to GitHub Pages / Netlify / any static host)

Design goals
------------
1. SEO: server-rendered HTML, one H1/page, unique title+description+canonical,
   internal linking, sitemap, clean URLs, LocalBusiness + Service + FAQ JSON-LD.
2. AEO (AI/answer engines): llms.txt, machine-readable business.json, explicit
   crawler allowances, question-shaped headings with the answer in the FIRST
   sentence, facts stated as plain text (not images), no client-side rendering.
3. Zero dependencies. No build toolchain, no JS framework, no CDN calls.
"""

import json
import os
import re
import shutil
from datetime import date

# ---------------------------------------------------------------------------
# SINGLE SOURCE OF TRUTH — edit these, rerun the script.
# Anything wrapped in «» is a PLACEHOLDER that Faraz must confirm.
# ---------------------------------------------------------------------------

BIZ = {
    "name": "Ziba Roofing",
    "wordmark_a": "ZIBA",
    "wordmark_b": "ROOFING",
    "legal_name": "Ziba Management Inc.",
    "tagline": "Roofing for the DMV",
    "domain": "https://zibaroofing.com",       # ✅ registered 2026-10-11 (IONOS)
    "phone_display": "(301) 366-8210",
    "phone_e164": "+13013668210",
    "email": "mike@zibamgmt.com",
    "street": "4000 Rosemary Street",            # ✅ Set by Faraz 2026-10-11
    "city": "Chevy Chase",
    "region": "MD",
    "postal": "20815",
    "country": "US",
    "lat": 38.9847,   # Chevy Chase MD 20815 — approximate, refine if exact pin matters
    "lon": -77.0797,
    "license": "410520000203",
    "license_authority": "District of Columbia (DCRA/DLCP) Home Improvement Contractor",
    "founded": "2015",                            # «confirm year»
    "hours": [
        ("Mo,Tu,We,Th,Fr", "07:00", "18:00"),
        ("Sa", "08:00", "14:00"),
    ],
    "hours_human": "Mon–Fri 7am–6pm · Sat 8am–2pm · Emergency tarping 24/7",
    "price_range": "$$",
    # Contact-form delivery. FormSubmit needs NO account: it emails this address directly,
    # but the FIRST submission triggers a one-time confirmation link sent to that inbox.
    # Until someone clicks it, nothing is delivered. See README.
    "form_endpoint": "https://formsubmit.co/mike@zibamgmt.com",
    "form_to": "mike@zibamgmt.com",
    # TEMPORARY: False while DNS still points at IONOS parking, so the
    # gtsvenum.github.io/ziba-roofing/ preview URL works. Flip back to True the
    # moment the A records point at GitHub, or the live domain will 404.
    # Canonical URLs stay zibaroofing.com regardless, so the preview URL cannot
    # cause duplicate-content indexing.
    "pages_custom_domain": True,
    # Set to "" (empty) when the real domain is live. Only needed for the
    # gtsvenum.github.io/ziba-roofing/ preview, which serves from a subdirectory.
    "base_path": "",
}

# Brand palette derived from the real Ziba logo (paisley mark).
# Logo blue #6B8FE0 is too light for AA body contrast, so it is the ACCENT and
# a darkened sibling carries the UI.
COLORS = {
    "navy": "#16243A",
    "blue": "#2F5596",
    "blue_light": "#6B8FE0",
    "gold": "#C9A24B",
    "charcoal": "#2B2B2B",
    "slate": "#5A6676",
    "mist": "#F4F6FA",
    "line": "#DDE3EC",
}

SERVICES = [
    {
        "slug": "roof-replacement",
        "name": "Roof Replacement",
        "short": "Full tear-off and replacement in architectural shingle, metal, or flat membrane.",
        "h1": "Roof Replacement in the DMV",
        "answer": (
            "A full roof replacement in the Washington DC metro area typically takes one to "
            "three days and starts with a complete tear-off down to the deck, so rotted sheathing "
            "is found and replaced rather than covered up."
        ),
        "detail": [
            ("What a replacement actually includes",
             "Tear-off of all existing layers, inspection and replacement of damaged decking, "
             "synthetic underlayment, ice-and-water shield at eaves and valleys, new drip edge, "
             "new pipe boots and flashing, ridge ventilation, and the finish roofing material. "
             "Flashing and boots are where most roofs fail first, so we replace them every time "
             "rather than reusing them."),
            ("How long it takes",
             "Most DC rowhouse and suburban Maryland or Virginia roofs are completed in one to "
             "three working days. Slate, tile, and large or steep-pitch roofs take longer."),
            ("How we price it",
             "Roofing is priced by the square (100 square feet of actual roof surface, not floor "
             "area), adjusted for pitch, number of layers to remove, decking condition, and the "
             "complexity of valleys, dormers, chimneys, and skylights. You get a written "
             "line-item estimate before any work is scheduled."),
            ("Permits and inspections",
             "Like-for-like residential reroofing generally does not require a permit in the "
             "District, but structural decking work, additions to the roof structure, and work in "
             "a historic district often do. We pull what the jurisdiction requires and schedule "
             "the inspections."),
        ],
        "faqs": [
            ("How long does a roof replacement take?",
             "One to three working days for a typical DMV home. Slate, tile, and complex "
             "multi-pitch roofs take longer."),
            ("Can you install a new roof over the old one?",
             "We do not recommend it and we do not do it. A layover hides rotted decking, voids "
             "most manufacturer warranties beyond the first layer, adds dead load, and shortens "
             "the life of the new shingles because of trapped heat."),
            ("How much does a new roof cost in Washington DC?",
             "Most DMV residential replacements fall between $8,000 and $30,000 depending on "
             "squares, pitch, material, and decking repairs. Flat and metal roofs sit at the "
             "upper end. We give a written line-item price before scheduling."),
        ],
    },
    {
        "slug": "roof-repair",
        "name": "Roof Repair & Leak Diagnosis",
        "short": "Find the actual leak, not the stain. Same-week repair appointments.",
        "h1": "Roof Repair and Leak Diagnosis",
        "answer": (
            "Most roof leaks are not holes in the field of the roof — they are failed flashing, "
            "cracked pipe boots, backed-up valleys, or clogged gutters, and water usually enters "
            "well uphill of the ceiling stain you can see."
        ),
        "detail": [
            ("Why the stain is not the leak",
             "Water runs along rafters and sheathing before it drops. A stain over the dining "
             "room can originate at a chimney eight feet away. We trace the path from inside the "
             "attic or ceiling cavity before we go on the roof, which is why we find leaks that "
             "have already been 'fixed' twice."),
            ("The five failures we find most",
             "Cracked rubber pipe boots (the single most common), step flashing at wall "
             "intersections, chimney counterflashing that was caulked instead of cut in, nail "
             "pops under shingle tabs, and ice-dam backup at eaves on north-facing slopes."),
            ("Repair or replace",
             "If the roof is under roughly 15 years old and the failure is localized, repair is "
             "the right call and we will say so. If the shingles are curling, granules are "
             "filling the gutters, and there are multiple leak points, repairs are money spent "
             "twice. We tell you which one you are looking at in writing."),
            ("Emergency response",
             "We tarp active leaks to stop interior damage, then return for the permanent repair "
             "once the weather clears."),
        ],
        "faqs": [
            ("How do I find where my roof is leaking?",
             "Start in the attic during or right after rain and look uphill from the wet spot. "
             "Water travels down rafters before it drops, so the entry point is almost always "
             "higher on the slope than the interior stain."),
            ("Do you do emergency roof tarping?",
             "Yes. We tarp active leaks to stop interior damage and schedule the permanent "
             "repair separately."),
            ("Is it worth repairing an old roof?",
             "If the roof is under about 15 years old and the failure is localized, repair is "
             "usually the better value. Multiple leak points plus curling shingles and granule "
             "loss in the gutters means repairs will not hold."),
        ],
    },
    {
        "slug": "flat-roofing",
        "name": "Flat & Low-Slope Roofing",
        "short": "TPO, EPDM, and modified bitumen for DC rowhouses and commercial decks.",
        "h1": "Flat and Low-Slope Roofing",
        "answer": (
            "Flat roofs are standard on DC rowhouses, and the three systems worth installing are "
            "TPO, EPDM rubber, and modified bitumen — each lasting roughly 20 to 30 years when "
            "the drainage and details are done correctly."
        ),
        "detail": [
            ("TPO",
             "A heat-welded white thermoplastic membrane. The welded seams are the strongest "
             "detail in flat roofing, and the white surface reflects heat, which matters on a "
             "DC rowhouse with living space directly below the roof. Our default recommendation "
             "for most residential flat roofs."),
            ("EPDM rubber",
             "Black synthetic rubber in large sheets with very few seams. Extremely durable and "
             "forgiving of movement, but it absorbs heat rather than reflecting it. A strong "
             "choice for roofs with no conditioned space directly beneath."),
            ("Modified bitumen",
             "Torch-applied or self-adhered asphalt sheets in two or three plies. The most "
             "puncture-resistant option, which makes it the right pick for roofs that get walked "
             "on for HVAC service."),
            ("Drainage is the whole game",
             "A flat roof is not flat — it needs a quarter inch per foot of fall to a drain or "
             "scupper. Standing water 48 hours after rain means the slope or the drain is wrong, "
             "and no membrane will survive that long term. We correct slope with tapered "
             "insulation rather than patching around ponding."),
        ],
        "faqs": [
            ("How long does a flat roof last?",
             "A properly installed TPO, EPDM, or modified bitumen roof lasts 20 to 30 years. "
             "Failures before that are almost always drainage or flashing details, not the "
             "membrane itself."),
            ("What is the best flat roof material for a DC rowhouse?",
             "TPO for most of them. The heat-welded seams outperform glued laps and the "
             "reflective white surface reduces cooling load on the top floor, which is usually "
             "finished living space in a rowhouse."),
            ("Why is water standing on my flat roof?",
             "Insufficient slope or a blocked drain. A low-slope roof needs about a quarter inch "
             "per foot of fall. Water still sitting 48 hours after rain will shorten the life of "
             "any membrane and needs tapered insulation to correct."),
        ],
    },
    {
        "slug": "metal-roofing",
        "name": "Metal Roofing",
        "short": "Standing seam and metal shingle systems with 40–70 year service life.",
        "h1": "Standing Seam and Metal Roofing",
        "answer": (
            "A standing seam metal roof lasts 40 to 70 years — roughly two to three times an "
            "asphalt roof — because the fasteners are concealed inside the seam where weather "
            "never reaches them."
        ),
        "detail": [
            ("Standing seam vs exposed fastener",
             "Standing seam hides the fasteners inside the raised vertical seam. Exposed-fastener "
             "panels are cheaper, but every screw carries a rubber washer that degrades, which "
             "means hundreds of future leak points. For a house, install standing seam."),
            ("Why it costs more up front",
             "Two to three times the installed cost of architectural shingles. Over a 50-year "
             "window it is usually cheaper, because an asphalt roof will be replaced twice in "
             "that span. If you intend to sell within five years, the math does not favor it."),
            ("Noise and lightning",
             "Both concerns are outdated. Over solid decking and underlayment, a metal roof is "
             "no louder than shingles in rain. Metal does not attract lightning, and because it "
             "is non-combustible it is the safer material if lightning does strike nearby."),
            ("Where it genuinely wins",
             "Low-slope sections where shingles should not be used, historic standing-seam "
             "replacements, snow-shedding porch roofs, and modern architecture where the panel "
             "line is the design."),
        ],
        "faqs": [
            ("How long does a metal roof last?",
             "40 to 70 years for standing seam with a quality coating. Exposed-fastener panels "
             "last less because the rubber washers on the screws degrade."),
            ("Is a metal roof noisy when it rains?",
             "No. Installed over solid decking with underlayment — which is how residential metal "
             "is installed — it is no louder than an asphalt shingle roof. The noise reputation "
             "comes from barns with bare metal over open purlins."),
            ("Does a metal roof attract lightning?",
             "No. Metal roofing does not increase the chance of a lightning strike, and because "
             "it is non-combustible it reduces fire risk if one occurs nearby."),
        ],
    },
    {
        "slug": "slate-and-tile",
        "name": "Slate & Tile Roofing",
        "short": "Historic slate repair and replacement for DC, Takoma Park, and Old Town.",
        "h1": "Slate and Tile Roof Restoration",
        "answer": (
            "Natural slate roofs last 75 to 150 years, so a slate roof that is leaking usually "
            "needs targeted repair of the flashing and failed fasteners — not replacement."
        ),
        "detail": [
            ("Most slate roofs fail at the nails, not the slate",
             "The slate outlives the fasteners and the flashing by decades. When a 90-year-old "
             "slate roof starts leaking, the common causes are corroded nails letting individual "
             "slates slip, and valley or chimney flashing that has reached end of life. Replacing "
             "flashing and resetting slipped slates can buy another 30 years."),
            ("Repair done correctly",
             "Individual slates are replaced with a slate hook or a copper bib — never face-nailed "
             "and never caulked. Face-nailing a replacement slate creates the next leak and marks "
             "the work as amateur from the ground."),
            ("Historic districts",
             "Much of our service area sits in historic districts where the roofing material is "
             "regulated. We work to the applicable historic review standards and handle the "
             "documentation."),
            ("When replacement is honest",
             "Widespread delamination — slates flaking in layers and sounding dull instead of "
             "ringing when tapped — means the slate itself is spent. At that point selective "
             "repair is throwing money at a finished roof, and we will tell you."),
        ],
        "faqs": [
            ("How long does a slate roof last?",
             "75 to 150 years depending on the quality of the stone. Vermont and Buckingham slate "
             "sit at the top of that range. The nails and flashing fail long before the slate."),
            ("Can a slate roof be repaired instead of replaced?",
             "Usually yes. Slipped slates and failed valley or chimney flashing account for most "
             "slate roof leaks, and both are repairable. Replacement is only honest when the "
             "slate is delaminating across the roof."),
            ("Can you match my existing slate?",
             "In most cases. Slate is matched by quarry, color, thickness, and size. Salvaged "
             "slate is often the best match on a historic roof."),
        ],
    },
    {
        "slug": "gutters-and-drainage",
        "name": "Gutters & Drainage",
        "short": "Seamless aluminum and half-round copper, sized to the actual roof area.",
        "h1": "Gutters, Downspouts, and Roof Drainage",
        "answer": (
            "Undersized or clogged gutters cause more foundation and fascia damage in the DMV "
            "than roof leaks do, because the water ends up against the house instead of away "
            "from it."
        ),
        "detail": [
            ("Sizing is not one-size",
             "Five-inch K-style gutter is the default, but a steep roof with a large drainage "
             "area overwhelms it in a heavy summer storm. We size the gutter and the number of "
             "downspouts to the actual roof area and pitch. Overflowing gutters are frequently a "
             "sizing problem, not a clog."),
            ("Seamless aluminum",
             "Formed on site to the exact length of your run, so there are no mid-run seams to "
             "split. The standard choice for most homes."),
            ("Half-round copper",
             "For historic homes and anywhere the gutter is visible architecture. Copper lasts "
             "50-plus years and weathers to a patina instead of peeling."),
            ("Where the water goes",
             "A downspout dumping at the foundation is a wet basement waiting to happen. We "
             "extend discharge a minimum of four feet from the wall, or tie into buried drainage "
             "where the grade allows."),
        ],
        "faqs": [
            ("How often should gutters be cleaned?",
             "Twice a year in the DMV — late spring and late fall. Properties under oak or maple "
             "canopy need a third cleaning in midsummer."),
            ("Are gutter guards worth it?",
             "Fine-mesh guards meaningfully reduce cleaning frequency under heavy tree cover. "
             "Foam inserts and plastic screens clog with shingle grit and pine needles and tend "
             "to make the problem worse."),
            ("Why do my gutters overflow even though they are clean?",
             "They are probably undersized or short on downspouts for the roof area draining into "
             "them. Gutters should be sized to actual roof square footage and pitch, not installed "
             "at a default five inches everywhere."),
        ],
    },
    {
        "slug": "storm-damage-and-insurance",
        "name": "Storm Damage & Insurance Claims",
        "short": "Documented damage reports your adjuster can actually approve.",
        "h1": "Storm Damage Repair and Insurance Claim Support",
        "answer": (
            "Most storm-damage claims are denied or underpaid because the damage was documented "
            "poorly, not because it was not covered — so the photo and measurement record matters "
            "as much as the repair."
        ),
        "detail": [
            ("What we document",
             "Dated photographs of every damaged slope, measured hail-strike density per test "
             "square, wind-lift and crease evidence on shingle tabs, collateral damage to soft "
             "metals like gutters and vents, and interior water intrusion. That record is what an "
             "adjuster needs to approve a slope rather than a patch."),
            ("We meet the adjuster on site",
             "An adjuster working alone on an unfamiliar roof can miss damage on the back slope. "
             "We walk it with them so the scope reflects what is actually up there."),
            ("What we will not do",
             "We will not inflate a scope, waive or absorb your deductible, or tell you a roof is "
             "destroyed when it is not. Deductible rebating is insurance fraud in Maryland, "
             "Virginia, and the District, and any contractor offering it is telling you how they "
             "do business."),
            ("Storm-chaser warning",
             "If someone knocks on your door after a hailstorm with out-of-state plates and a "
             "contract to sign today, slow down. Verify the license number against the "
             "jurisdiction's database before you sign anything, including with us — ours is "
             + BIZ["license"] + "."),
        ],
        "faqs": [
            ("Does homeowners insurance cover roof damage?",
             "Sudden damage from wind, hail, or a fallen tree is generally covered. Gradual wear, "
             "age, and deferred maintenance are not. The distinction is why documentation of the "
             "storm event matters."),
            ("How long do I have to file a roof claim after a storm?",
             "Most policies require prompt notice and many set a one-year limit from the date of "
             "loss. Check your specific policy and file as soon as you suspect damage."),
            ("Should I use the contractor my insurance company recommends?",
             "You are not required to. You can choose any licensed contractor. A preferred-vendor "
             "program is a cost-control arrangement for the insurer, not an endorsement of quality."),
        ],
    },
]

AREAS = [
    {
        "slug": "washington-dc",
        "name": "Washington, DC",
        "short_name": "Washington DC",
        "blurb": "Rowhouse flat roofs, historic slate, and tight alley access across all eight wards.",
        "detail": (
            "Most DC roofing work is low-slope rowhouse roofing, not pitched shingle. That changes "
            "everything about the job: access is through the house or off an alley, there is no "
            "driveway for a dumpster, and the roof is often directly over finished living space "
            "with no attic buffer. We work rowhouses routinely and plan the logistics before the "
            "crew shows up."
        ),
        "neighborhoods": ["Capitol Hill", "Shaw", "Petworth", "Columbia Heights", "Brookland",
                          "Georgetown", "Anacostia", "Takoma", "Bloomingdale", "Trinidad",
                          "Chevy Chase DC", "Woodley Park"],
        "note": "Historic districts including Capitol Hill, Georgetown, and Mount Pleasant have "
                "review requirements for visible roofing materials. We handle that documentation.",
    },
    {
        "slug": "montgomery-county-md",
        "name": "Montgomery County, MD",
        "short_name": "Montgomery County",
        "blurb": "Bethesda, Silver Spring, Rockville, Potomac, and Takoma Park.",
        "detail": (
            "Montgomery County has the widest range of roof types in our service area: 1920s "
            "slate in Takoma Park, mid-century ranches in Wheaton, and large modern builds in "
            "Potomac with complex multi-pitch rooflines and extensive valley detail. The county "
            "requires permits for roofing work involving structural decking changes, and "
            "inspections are scheduled through DPS."
        ),
        "neighborhoods": ["Bethesda", "Chevy Chase", "Silver Spring", "Rockville", "Potomac",
                          "Takoma Park", "Kensington", "Wheaton", "Gaithersburg", "Olney",
                          "Germantown", "North Bethesda"],
        "note": "Montgomery County DPS permits and inspections are handled by us, not left to you.",
    },
    {
        "slug": "prince-georges-county-md",
        "name": "Prince George's County, MD",
        "short_name": "Prince George's County",
        "blurb": "Hyattsville, College Park, Bowie, Laurel, and Upper Marlboro.",
        "detail": (
            "Prince George's County housing stock skews toward post-war colonials and ranches "
            "with straightforward gable and hip roofs, which makes replacement fast and "
            "predictable. The most common call we get here is storm damage after summer "
            "thunderstorm lines come through."
        ),
        "neighborhoods": ["Hyattsville", "College Park", "Bowie", "Laurel", "Greenbelt",
                          "Upper Marlboro", "Mount Rainier", "Riverdale Park", "Beltsville",
                          "Clinton", "Largo", "Oxon Hill"],
        "note": "Summer storm lines hit PG County hard. We document damage for insurance claims.",
    },
    {
        "slug": "arlington-va",
        "name": "Arlington, VA",
        "short_name": "Arlington",
        "blurb": "Clarendon, Ballston, Rosslyn, and the single-family neighborhoods south of Route 50.",
        "detail": (
            "Arlington is dense with 1940s–1960s brick colonials and Cape Cods carrying 30-plus "
            "year old roofs now reaching end of life, alongside new infill construction with "
            "steep complex rooflines. Arlington County requires a permit for most reroofing work, "
            "which is stricter than DC — we pull it."
        ),
        "neighborhoods": ["Clarendon", "Ballston", "Rosslyn", "Shirlington", "Cherrydale",
                          "Lyon Village", "Arlington Ridge", "Crystal City", "Westover",
                          "Aurora Highlands", "Donaldson Run"],
        "note": "Arlington County requires permits for most reroofing. We handle the application.",
    },
    {
        "slug": "alexandria-va",
        "name": "Alexandria, VA",
        "short_name": "Alexandria",
        "blurb": "Old Town historic roofing, Del Ray, and the West End.",
        "detail": (
            "Old Town Alexandria sits in one of the oldest historic districts in the country, and "
            "the Board of Architectural Review governs roofing materials visible from the street. "
            "Standing seam metal and slate are common original materials here, and substituting "
            "asphalt where metal was original will not pass review."
        ),
        "neighborhoods": ["Old Town", "Del Ray", "Rosemont", "Beverley Hills", "Seminary Hill",
                          "Landmark", "Parkfairfax", "Potomac Yard", "Arlandria"],
        "note": "Old Town falls under BAR review for street-visible roofing. We prepare submissions.",
    },
    {
        "slug": "fairfax-county-va",
        "name": "Fairfax County, VA",
        "short_name": "Fairfax County",
        "blurb": "McLean, Falls Church, Vienna, Tysons, Reston, and Great Falls.",
        "detail": (
            "Fairfax County covers the largest area we serve and the largest roofs. McLean and "
            "Great Falls homes frequently run 40 to 70 squares with multiple dormers, turrets, "
            "and long valley runs — roofs where the detail work matters more than the field "
            "shingle. Heavy mature tree canopy also means more moss, more debris, and a real "
            "need for gutter sizing done right."
        ),
        "neighborhoods": ["McLean", "Falls Church", "Vienna", "Tysons", "Reston", "Herndon",
                          "Great Falls", "Annandale", "Burke", "Springfield", "Oakton",
                          "Centreville"],
        "note": "Large multi-pitch roofs and heavy tree canopy define the work out here.",
    },
]

WHY = [
    ("Licensed and insured in all three jurisdictions",
     "Ziba Roofing operates under " + BIZ["legal_name"] + ", " + BIZ["license_authority"] +
     " license #" + BIZ["license"] + ", carrying general liability and workers' compensation. "
     "Ask any roofer for their number and verify it before you sign. Including us."),
    ("We are contractors, not a sales organization",
     "The person who prices your roof understands how it gets built, because the same company "
     "builds whole houses. You will not get a commissioned closer with a tablet and a discount "
     "that expires tonight."),
    ("Written line-item estimates",
     "You see the squares, the material, the decking allowance, the flashing scope, and the "
     "disposal cost as separate lines. A single lump-sum number is how surprises get hidden."),
    ("We replace flashing every time",
     "Flashing and pipe boots are the most common point of failure on a roof and the cheapest "
     "thing to reuse if you are cutting corners. We replace them on every full roof. No exceptions."),
    ("Clean site, magnet swept",
     "Dumpster placed to protect your driveway and landscaping, tarps over plantings, and a "
     "magnetic sweep of the lawn and street at the end of every working day. Roofing nails in a "
     "tire are the most common complaint about roofers, and they are entirely preventable."),
    ("Straight answers about repair versus replacement",
     "If your roof needs a $600 repair instead of a $20,000 replacement, that is what the "
     "estimate will say. Telling a homeowner to replace a sound roof is the fastest way to lose "
     "the referrals that actually sustain this business."),
]

PROCESS = [
    ("Inspection", "We photograph the roof, the flashing details, the attic where accessible, and "
                   "the gutters. You get the photos whether or not you hire us."),
    ("Written estimate", "A line-item scope and price, including a stated allowance for decking "
                         "replacement so rotted sheathing does not become a surprise invoice."),
    ("Scheduling and permits", "We pull any required permit, order material, and give you a "
                               "start date with a weather contingency."),
    ("Installation", "Tear-off, deck inspection, underlayment, flashing, finish material, "
                     "ventilation. Site protected and swept daily."),
    ("Final walkthrough", "We walk the property with you, show you photos of the completed "
                          "details you cannot see from the ground, and hand over warranty "
                          "documentation."),
]

GENERAL_FAQS = [
    ("What areas do you serve?",
     "Ziba Roofing serves the DMV: Washington DC, Montgomery County and Prince George's County in "
     "Maryland, and Arlington, Alexandria, and Fairfax County in Virginia."),
    ("Are you licensed and insured?",
     "Yes. Ziba Roofing operates under " + BIZ["legal_name"] + " under " + BIZ["license_authority"] +
     " license #" + BIZ["license"] + ", with general liability and workers' compensation coverage. "
     "Certificates are available on request."),
    ("How much does a new roof cost in the DMV?",
     "Most residential replacements in the Washington DC metro area run between $8,000 and "
     "$30,000. The drivers are roof size in squares, pitch, material, how many existing layers "
     "come off, and how much decking needs replacing. Flat and metal roofs sit at the upper end."),
    ("How do I know if I need a new roof or just a repair?",
     "Shingles curling at the edges, bare patches where granules have washed off, granules "
     "collecting in the gutters, daylight visible through the attic sheathing, and leaks in more "
     "than one location all point to replacement. A single leak on a roof under 15 years old is "
     "usually a repair."),
    ("How long does a roof last in the Washington DC area?",
     "Architectural asphalt shingles last 20 to 30 years here, flat membrane roofs 20 to 30 "
     "years, standing seam metal 40 to 70, and natural slate 75 to 150. DMV summers are hard on "
     "asphalt, so roofs on unventilated attics tend toward the low end of those ranges."),
    ("Do you offer free estimates?",
     "Yes. Roof inspection and written estimate are free, and you get the inspection photos "
     "whether or not you hire us."),
    ("Do you work with insurance claims?",
     "Yes. We document storm damage to the standard an adjuster needs, and we meet the adjuster "
     "on site. We do not waive deductibles, which is illegal in DC, Maryland, and Virginia."),
    ("What is the best time of year to replace a roof in the DMV?",
     "Late spring through early fall. Asphalt shingles need temperatures above roughly 40°F to "
     "seal properly. We install year-round using hand-sealing in cold weather, but given the "
     "choice, schedule in mild weather."),
    ("How long does a roof replacement take?",
     "One to three working days for most DMV homes. Slate, tile, and large complex roofs take "
     "longer."),
    ("Do you require a deposit?",
     "A material deposit is due at scheduling with the balance on completion. We do not ask for "
     "full payment up front — no legitimate roofer does."),
]
