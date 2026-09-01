# FAA / EPA rules snapshot — backyard weed-spray drone

**Not legal advice.** The operator must read the primary sources linked below. This file is a research snapshot for the weed-spray project, not a legal opinion, not a permit, and not FAA or EPA guidance.

**No registration or TRUST was filed** as part of writing this snapshot. Grok Bots must never arm, takeoff, or send MAVLink to a real aircraft.

**Date checked:** 2026-08-30 (America/Denver)

**Project facts this snapshot assumes (locked):** US hobby backyard, VLOS, under 5,000 sq ft lawn; recreational operation, no Part 107 assumed; PX4 quad, likely over 250 g when finished, under 55 lb; human confirms every spray; RC transmitter in hand whenever motors can spin; household vinegar/salt via 12V pump, not commercial herbicide in v1; stay on own turf inside a geofence; do not spray people, pets, garden beds, or anything outside the geofence.

---

## Primary-source URLs (fetched 2026-08-30)

| Source | URL | Page title / note |
| --- | --- | --- |
| FAA | https://www.faa.gov/uas/recreational_flyers | Recreational Flyers & Community-Based Organizations (last updated 2026-03-18) |
| FAA | https://www.faa.gov/uas/getting_started/register_drone | How to Register Your Drone |
| FAA | https://www.faa.gov/uas/recreational_flyers/knowledge_test_updates | The Recreational UAS Safety Test (TRUST) (last updated 2026-08-21) |
| FAA | https://www.faa.gov/uas/getting_started | Getting Started |
| FAA | https://www.faa.gov/dronefaq | What To Know About Drones (2025-01-14) |
| FAA | https://www.faa.gov/uas/getting_started/b4ufly | B4UFLY (last updated 2026-08-25) |
| FAA | https://www.faa.gov/uas/getting_started/remote_id | Remote Identification of Drones |
| FAA | https://www.faa.gov/uas/advanced_operations/dispensing_chemicals | Dispensing Chemicals and Agricultural Products (Part 137) with UAS (last updated 2026-05-05) |
| FAA portal | https://faadronezone.faa.gov → https://faadronezone-access.faa.gov | FAADroneZone (registration / services portal). Describe only; do not file. |
| US Code | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title49-section44809&num=0&edition=prelim | 49 USC 44809 — Exception for limited recreational operations of unmanned aircraft (text in effect 2026-08-29) |
| eCFR | https://www.ecfr.gov/current/title-14/chapter-I/subchapter-G/part-137 | 14 CFR Part 137 — Agricultural Aircraft Operations (eCFR as of 2026-08-27) |
| eCFR | https://www.ecfr.gov/current/title-14/part-137/section-137.3 | 14 CFR 137.3 — Definition of terms |
| eCFR | https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-48 | 14 CFR Part 48 — Registration and Marking Requirements for Small Unmanned Aircraft |
| EPA | https://www.epa.gov/minimum-risk-pesticides/what-pesticide | What is a Pesticide? (last updated 2026-01-29) |
| EPA | https://www.epa.gov/minimum-risk-pesticides/minimum-risk-pesticides-inert-ingredient-and-active-ingredient-eligibility | Minimum Risk Pesticides — inert/active eligibility under 40 CFR 152.25(f) (last updated 2026-02-26) |
| EPA | https://www.epa.gov/pesticide-registration/determining-if-cleaning-product-pesticide-under-fifra | Determining If a Cleaning Product Is a Pesticide Under FIFRA (last updated 2026-07-06) |
| eCFR | https://www.ecfr.gov/current/title-40/chapter-I/subchapter-E/part-152/subpart-A/section-152.15 | 40 CFR 152.15 — Pesticide products required to be registered |
| US Code | https://uscode.house.gov/view.xhtml?edition=prelim&num=0&req=granuleid:USC-prelim-title7-section136j | 7 USC 136j — Unlawful acts (FIFRA) |
| EPA enforcement | https://www.epa.gov/enforcement/federal-insecticide-fungicide-and-rodenticide-act-fifra-and-federal-facilities | FIFRA and Federal Facilities (unlawful-acts summary) |
| EPA fact sheet | https://www3.epa.gov/pesticides/chem_search/reg_actions/registration/fs_PC-044001_01-Mar-01.pdf | Biopesticides Fact Sheet for Acetic Acid (EPA, 2001-03-01) |
| EPA label example | https://www3.epa.gov/pesticides/chem_search/ppls/000003-00024-20220914.pdf | EPA-registered “Vinegar Grass & Weed Killer II” label (20% acetic acid; “Do not apply this product by aerial application”) |

No drone forums, Reddit, blogs, or YouTube were used as authority.

---

## Recreational small UAS in a US backyard (44809)

FAA’s recreational page is the agency summary of [49 USC 44809](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title49-section44809&num=0&edition=prelim). Congress created a limited statutory exception so people flying “purely for fun or personal enjoyment” can operate without complying with 14 CFR Part 107 — **if** they meet **all** of the statutory limitations. ([FAA Recreational Flyers](https://www.faa.gov/uas/recreational_flyers))

FAA: “Compensation, or the lack of it, is not what determines if a flight was recreational or not.” And: “When in doubt, assume Part 107.” Same page.

### The eight 44809(a) limitations (statute + FAA numbering)

Quoted from the statute ([49 USC 44809(a)](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title49-section44809&num=0&edition=prelim)); FAA’s recreational page restates the same list:

1. **Recreational only.** “The aircraft is flown strictly for recreational purposes.”
2. **CBO guidelines.** Operated in accordance with an FAA-recognized community-based organization’s safety guidelines.
3. **VLOS.** “Flown within the visual line of sight of the person operating the aircraft or a visual observer co-located and in direct communication with the operator.”
4. **Give way.** Does not interfere with, and gives way to, manned aircraft.
5. **Controlled airspace.** In Class B/C/D or surface Class E designated for an airport: prior FAA authorization (LAANC or DroneZone) and comply with restrictions.
6. **400 ft in Class G.** In Class G, flown from the surface to not more than 400 feet AGL, plus all airspace/flight restrictions (TFRs, special-use, etc.).
7. **TRUST.** Operator has passed the aeronautical knowledge and safety test and keeps proof available to FAA or law enforcement.
8. **Registration/marking** as required by chapter 441, with proof available on request.

FAA adds a ninth operational duty on the recreational page: “Do not operate your drone in a manner that endangers the safety of the national airspace system.” Violations may draw FAA enforcement. ([FAA Recreational Flyers](https://www.faa.gov/uas/recreational_flyers))

Operations that do **not** meet those limitations “must comply with all statutes and regulations generally applicable to unmanned aircraft” — i.e. leave the 44809 carve-out. ([49 USC 44809(b)](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title49-section44809&num=0&edition=prelim))

### This project vs Part 107

This snapshot assumes recreational 44809, not Part 107. That assumption is **fragile for a spray flight.** FAA’s own recreational page lists **“agricultural spraying”** as a **non-recreational Part 91** example, next to BVLOS package delivery. It also says goodwill / volunteering can be non-recreational. Lack of pay does not make a flight recreational. ([FAA Recreational Flyers](https://www.faa.gov/uas/recreational_flyers))

If a spray flight is **not** “strictly for recreational purposes,” 44809 does not apply and the default small-UAS rule is Part 107 — plus whatever Part 137 / EPA rules apply to dispensing. See the vinegar / Part 137 section below. **Do not treat “hobby backyard” as an automatic 44809 pass for a dispensing flight.**

---

## Registration and TRUST — flag 250 g

### Registration (weight threshold)

FAA: “You must register if your drone weighs **250 grams (0.55 lbs) or more.**” ([FAA Recreational Flyers](https://www.faa.gov/uas/recreational_flyers))

FAA register page: “All drones must be registered, except those that weigh **0.55 pounds or less (less than 250 grams)** and are flown under the Exception for Limited Recreational Operations.” Recreational registration is **$5**, covers **all drones in that recreational inventory**, valid **three years**. Drones registered under the recreational exception **cannot** be flown under Part 107. Register at FAADroneZone. Label the aircraft on the outside; carry the certificate when flying. ([How to Register Your Drone](https://www.faa.gov/uas/getting_started/register_drone))

eCFR: no person may operate an eligible small UAS unless registered **or** “the aircraft is operated exclusively in compliance with 49 U.S.C. 44809 **and weighs 0.55 pounds or less on takeoff, including everything that is on board or otherwise attached to the aircraft.**” ([14 CFR 48.15](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-48))

**Project flag:** a finished flyable spray quad (frame + battery + tank + pump + payload liquid) will **almost certainly exceed 250 g / 0.55 lb on takeoff.** Recreational registration + external marking + carrying proof therefore apply **unless the operator actually weighs the ready-to-fly aircraft (everything on board / attached) under 0.55 lb.** Do not assume “maybe under 250 g.” Weigh it. This snapshot did **not** file registration.

**AUW from @parts (2026-08-30, paper, no scale):** S500 + 4S 2200 stack about **1.5–1.7 kg**, wet 250 ml tank on top. Over 250 g either way. Recreational registration + marking + Remote ID apply until a scale says otherwise. Still no filing from this Bot.

### Remote ID (follows registration)

FAA recreational page: as of **2023-09-16**, if the drone **requires** an FAA registration number it must also **broadcast Remote ID** unless flown in an FAA-Recognized Identification Area (FRIA). ([FAA Recreational Flyers](https://www.faa.gov/uas/recreational_flyers); [Remote Identification of Drones](https://www.faa.gov/uas/getting_started/remote_id))

A homemade PX4 quad is unlikely to be a “Standard Remote ID” aircraft from a manufacturer Declaration of Compliance. Practical paths on the FAA page: add an FAA-accepted **Remote ID broadcast module**, or fly only inside a **FRIA**. Broadcast-module operations still require VLOS. This snapshot did not register a module.

### TRUST

FAA: “If you fly your drone recreationally under the Exception for Recreational Flyers, **you must pass the test before you fly.**” Free, online, through an FAA-approved test administrator. Download/save/print the certificate; administrators do not keep a copy; if lost, retake. Carry proof when flying. ([TRUST](https://www.faa.gov/uas/recreational_flyers/knowledge_test_updates))

TRUST is a **44809 condition for recreational operations**, not a 250 g cutoff. The 250 g line is registration. This snapshot did **not** take or file TRUST.

### FAADroneZone (describe; do not file)

- Public URL [https://faadronezone.faa.gov](https://faadronezone.faa.gov) redirects to [https://faadronezone-access.faa.gov](https://faadronezone-access.faa.gov).
- Portal copy: “FAADroneZone is the official FAA website for managing drone services.” Login/create-account UI for: register a drone, airspace authorization, safety-event report, CBO recognition, FRIA, foreign Notice of Identification.
- Recreational vs Part 107 are **separate account/inventory types**. Recreational registration cannot be used for Part 107 flying. ([How to Register Your Drone](https://www.faa.gov/uas/getting_started/register_drone))
- Aircraft **55 lb or greater** cannot use this online small-UAS path (paper / N-number process). This project is under 55 lb.

---

## VLOS, people / pets, night, 400 ft, airspace

### VLOS

Statutory: keep the aircraft in visual line of sight of the operator **or** a co-located visual observer in direct communication. ([49 USC 44809(a)(3)](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title49-section44809&num=0&edition=prelim); [FAA Recreational Flyers](https://www.faa.gov/uas/recreational_flyers))

FAA: recreational operators “must fly their drone within visual line of sight so they can see if other aircraft are near them and safely avoid.” A software geofence, camera downlink, or YOLO box **does not replace VLOS.**

### People and pets

44809’s eight conditions do **not** copy Part 107’s “operations over human beings” subpart. What the primary FAA pages **do** say:

- Recreational flyers must follow rules “including flying below 400 feet, keeping the drone in sight, avoiding all other aircraft, and **not causing a hazard to any people or property.**” ([What To Know About Drones](https://www.faa.gov/dronefaq))
- “Pilots must operate drones so they don’t pose a hazard to people or property.” (same)
- 44809(a)(2) requires CBO safety guidelines; AIM 11-8-3 notes those guidelines “will usually include safety precautions for flight near people.” ([AIM 11-8-3](https://www.faa.gov/Air_Traffic/publications/atpubs/aim_html/chap11_section_8.html))
- Recreational page wrap-up: do not operate in a manner that endangers NAS safety.

**Project rule (stricter than the thinnest reading of 44809):** do not fly over people; pets or people on the lawn are a reason to **hold or land**; do not spray people, pets, garden beds, or anything outside the geofence. Software geofence is a stay-on-turf aid, not a VLOS substitute and not a people-detector.

### Night

FAA Getting Started: “Drones flying at night are required to have certain lighting.” Recreational night flying must be “in accordance with a community-based organization’s (CBO) set of safety guidelines that have night procedures detailing required lighting.” VLOS, 400 ft, and airspace rules still apply. ([Getting Started](https://www.faa.gov/uas/getting_started))

This project is a daytime backyard scan/spot-spray concept. If anyone flies after civil twilight, read the CBO night lighting procedures first. Do not invent a lighting spec here.

### 400 ft and airspace / B4UFLY

- Class G: at or below **400 ft AGL** unless a 44809(c) fixed-site authorization says otherwise. ([49 USC 44809(a)(6)](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title49-section44809&num=0&edition=prelim))
- Controlled airspace (B/C/D / surface E for an airport): prior authorization via **LAANC or DroneZone**.
- Check airspace **before** every flight: [B4UFLY](https://www.faa.gov/uas/getting_started/b4ufly) (FAA-approved apps: Airspace Link, Aloft, AutoPylot, Avision, FlightLoop, UASidekick — page last updated 2026-08-25). B4UFLY is situational awareness; it is not itself the authorization.

Yard location (Class G vs near an airport) is **unknown until the operator checks B4UFLY for the actual address.**

---

## Vinegar spot-spray vs pesticide / aircraft application

**Do not read this section as “it is legal” or “it is illegal.”** The primary pages do not issue a backyard-vinegar-drone advisory. They define two different regimes. The operator must stop and read FAA + EPA (+ the state pesticide agency, once a state is named) **before any real spray flight.**

### (a) Squirting household vinegar on your own turf **by hand**

This is **not** the same act as dispensing from an aircraft.

EPA pesticide definition (FIFRA § 2(u)): “any substance or mixture of substances **intended for** preventing, destroying, repelling, or mitigating any pest,” plus plant regulators / defoliants / desiccants. Intent is judged from claims, composition, use, and mode of action **as distributed or sold.** ([What is a Pesticide?](https://www.epa.gov/minimum-risk-pesticides/what-pesticide); [40 CFR 152.15](https://www.ecfr.gov/current/title-40/chapter-I/subchapter-E/part-152/subpart-A/section-152.15))

40 CFR 152.15 is a **distribute-or-sell** registration rule: “No person may distribute or sell any pesticide product that is not registered…” A substance is intended for a pesticidal purpose if the **seller** claims it can be used as a pesticide, or knows it will be used as one. Grocery household vinegar sold as food, with **no** pesticidal claims, is not the same product as an EPA-registered vinegar herbicide.

EPA’s own acetic-acid fact sheet: “Vinegar consists of approximately 5% acetic acid and 95% water. This is also the concentration of acetic acid when applied as a pesticide product.” ([Biopesticides Fact Sheet for Acetic Acid](https://www3.epa.gov/pesticides/chem_search/reg_actions/registration/fs_PC-044001_01-Mar-01.pdf))

**25(b) minimum-risk trap:** vinegar (max 8% acetic acid) may be used as an **inert** in 25(b) products. EPA: “**vinegar is not listed as a minimum risk active ingredient and may not be used as an active ingredient in unregistered, minimum risk pesticides.**” “Also, acetic acid is a potent herbicide.” Above 8%, “the chemical substance is generally not referred to as vinegar.” ([EPA 25(b) eligibility](https://www.epa.gov/minimum-risk-pesticides/minimum-risk-pesticides-inert-ingredient-and-active-ingredient-eligibility))

So: mixing grocery vinegar/salt **in order to kill weeds**, then **selling or distributing** that mix as a weed killer, is a FIFRA product-registration problem. A homeowner pouring grocery vinegar on their own dandelions by hand is a **different** fact pattern the fetched EPA pages do not bless or ban in one sentence. This snapshot does not claim either.

### (b) Dispensing that mix **from an aircraft**

FAA, not EPA, writes the aircraft-dispensing rule.

> “**14 CFR Part 137 governs the use of aircraft, including drones, to dispense or spray substances (including disinfectants).** Not all substances fall under this regulation, so you should first check to see if your proposed operation is regulated by Part 137. If the substance you plan to dispense **does fall within the definitions in Section 137.3**, refer to [the agricultural-operator certification process].”

([Dispensing Chemicals and Agricultural Products (Part 137) with UAS](https://www.faa.gov/uas/advanced_operations/dispensing_chemicals), last updated 2026-05-05)

**14 CFR 137.3** ([eCFR](https://www.ecfr.gov/current/title-14/part-137/section-137.3)):

> *Agricultural aircraft operation* means the operation of an aircraft for the purpose of **(1)** dispensing any **economic poison**, **(2)** dispensing **any other substance intended for** plant nourishment, soil treatment, propagation of plant life, or **pest control**, or **(3)** engaging in dispensing activities directly affecting agriculture, horticulture, or forest preservation…

> *Economic poison* includes any substance **intended for** preventing, destroying, repelling, or mitigating insects, rodents, nematodes, fungi, **weeds**, and other forms of plant or animal life…

The definition is **purpose-based** (what you intend the aircraft to dispense the stuff **for**), not “is this an EPA-registered pesticide product?” Household vinegar/salt carried on a quad **in order to kill lawn weeds** sits uncomfortably close to 137.3(2) (“any other substance intended for … pest control”) and to 137.3’s “weeds” language. FAA’s UAS Part 137 page tells the operator to **check 137.3**, not to skip Part 137 because the bottle came from a grocery aisle.

**14 CFR 137.11:** “no person may conduct agricultural aircraft operations without, or in violation of, an agricultural aircraft operator certificate” (limited public-aircraft / firefighting exceptions). For UAS, FAA’s current path is: register the drone, petition for exemption (under 55 lb typically Part 107 + exemption from § 107.36 carriage of hazardous material and several Part 137 sections), then apply for an Agricultural Aircraft Operator Certificate (Form 8710-3). ([FAA dispensing chemicals](https://www.faa.gov/uas/advanced_operations/dispensing_chemicals))

**14 CFR 137.37:** no person may dispense from an aircraft any material “in a manner that creates a hazard to persons or property on the surface.”

**14 CFR 137.39** (if the substance **is** an economic poison registered under FIFRA): do not dispense it for a use other than registered, contrary to label safety instructions, or in violation of US law.

FAA recreational page’s non-recreational examples include **“agricultural spraying.”** FAA: if unsure which rules apply, assume Part 107.

**Bottom line for v1 vinegar/salt from this quad:** the fetched primary pages **do not** say “grocery vinegar from a backyard drone is fine under 44809.” They **do** say Part 137 applies to drone dispensing when the operation matches 137.3, and 137.3 is written in “intended for pest control / weeds” language. **This snapshot does not conclude the operation is definitely a Part 137 agricultural aircraft operation, and does not conclude it isn’t.** Operator must read 137.3 + the FAA UAS dispensing page + EPA FIFRA pages **before any real spray flight**, and should not treat SITL or dry-run flights as having answered that question.

### Registered vinegar herbicides (what changes if the bottle is a pesticide product)

EPA has registered acetic-acid weed killers (often ~20% acetic acid). Example label **Vinegar Grass & Weed Killer II**: “**Do not apply this product by aerial application.**” ([EPA label PDF](https://www3.epa.gov/pesticides/chem_search/ppls/000003-00024-20220914.pdf))

FIFRA § 12(a)(2)(G), [7 USC 136j](https://uscode.house.gov/view.xhtml?edition=prelim&num=0&req=granuleid:USC-prelim-title7-section136j): it is unlawful “**to use any registered pesticide in a manner inconsistent with its labeling.**” EPA’s enforcement page repeats that prohibition. ([FIFRA and Federal Facilities](https://www.epa.gov/enforcement/federal-insecticide-fungicide-and-rodenticide-act-fifra-and-federal-facilities))

If the operator switches from unlabeled grocery vinegar to a **registered** herbicide, the **label is the law** for that product: aerial/drone application is often **expressly prohibited**. Do not put a labeled herbicide in this pump because “it’s still vinegar.”

---

## What still applies to **this** backyard vinegar quad

Even if the operator stays on the recreational-flyer path for **non-spray** flights (scan / practice / SITL is software-only):

| Topic | What the pages say for this project |
| --- | --- |
| Recreational conditions | VLOS, CBO guidelines, give way, 400 ft Class G, airspace auth if needed, TRUST, registration if ≥ 250 g, don’t endanger NAS. |
| Weight | Weigh ready-to-fly with battery + tank + liquid. Expect **≥ 250 g** → recreational registration + marking + **Remote ID**. Under 55 lb. |
| TRUST | Required **before** recreational flying. Not filed here. |
| Airspace | Check **B4UFLY** for the actual yard. Unknown until checked. |
| People / pets / off-turf | Do not cause a hazard to people or property (FAA FAQ). Project: hold/land if people or pets on the lawn; never spray them, garden beds, or outside the geofence. |
| Human confirm | Project lock: software must not auto-spray. |
| RC in hand | Project lock: transmitter in the pilot’s hands whenever motors can spin. |
| Grok Bots | Never arm / takeoff / Offboard / MAVLink to a real aircraft; never pulse a real pump. |
| Spray from aircraft | **Open FAA Part 137 / 137.3 question + EPA FIFRA question.** Do not treat v1 grocery vinegar as a free pass. Stop and read before any real spray flight. |
| State / HOA | Unknown. See below. |

Dry / water / no-dispense flight tests still need VLOS, TRUST, registration/Remote ID if over the weight line, and B4UFLY. They do **not** by themselves authorize later dispensing.

---

## What would change if they switch to commercial herbicide **or** fly/spray other property

Any of these **changes the analysis**. Do not “just try it.”

1. **Commercial / registered herbicide in the tank.** Product label controls (FIFRA 12(a)(2)(G)). Many acetic-acid herbicide labels **ban aerial application**. Part 137.39 adds an FAA overlay for economic poisons. Likely leaves 44809 (“strictly recreational”) and lands in **Part 107 + Part 137 certificate/exemption** territory per FAA’s UAS dispensing page.
2. **Spraying someone else’s property / over the fence / HOA common area / public strip.** 44809 does not grant a right to dispense on others’ land. Private agricultural certificate under Part 137, if that part applies, still may not operate “over any property unless he is the owner or lessee… or has ownership or other property interest in the crop” ([14 CFR 137.35](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-G/part-137)). Drift onto a neighbor is a hazard-to-property issue ([137.37](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-G/part-137)) and may be a state pesticide-use issue.
3. **Compensation, selling a spray service, or spraying for a business.** Not recreational. Default **Part 107**. FAA: lack of pay is not enough to stay in 44809 anyway.
4. **State pesticide applicator license.** Many states license aerial / pesticide application even when federal FIFRA product rules are met. State is **unknown**.
5. **Part 107 over people, night anti-collision lighting, hazardous-material carriage (§ 107.36).** Kick in if the operation is not 44809.

---

## Federal vs state vs HOA

| Layer | Status in this snapshot |
| --- | --- |
| **Federal aviation (FAA)** | 44809 / Part 107 / Part 137 / Part 48 / Remote ID (Part 89). Fetched and summarized above. |
| **Federal pesticide (EPA / FIFRA)** | Product registration (sale/distribution), label-is-the-law for **registered** pesticides, 25(b) minimum-risk lists (vinegar is **not** a 25(b) active). Fetched. |
| **State pesticide / applicator rules** | **Unknown.** FIFRA leaves states primary use-enforcement in many cases and states may be **more restrictive** than federal (EPA FIFRA federal-facilities page; aerial-applicator manual notes local bans). Operator must name the state and read that state’s department of agriculture / pesticide program before any real spray flight. |
| **HOA / local ordinances / property** | **Unknown.** FAA FAQ: you can land where it is safe and **not prohibited by local, state, or federal laws**; FAA “does not regulate privacy, but local privacy laws may apply.” An HOA covenant can still forbid drones or spraying regardless of FAA recreational status. Ask the operator; do not assume the backyard is unrestricted. |

---

## Software implications (do **not** remove these)

Nothing in the fetched FAA/EPA pages is a reason to strip safety interlocks. If anything, 137.37 (no hazardous dispensing) and the FAA “hazard to people or property” language cut the other way.

Keep, and do not recommend removing:

- **Human confirm before every spray.** No auto-spray from YOLO. SAFETY.md lock.
- **Geofence** stay-on-own-turf. Does **not** replace VLOS or a people check.
- **RC override in the pilot’s hands** whenever motors can spin.
- **Pump off** on failsafe, laptop disconnect, RC loss, or geofence breach.
- **No Grok Bot arm/takeoff/Offboard** to a real aircraft; no GPIO/pump pulse on hardware from a Bot.

Optional software that **helps** the operator follow the pages, without pretending to be compliance:

- Ready-to-fly weight checklist (250 g / Remote ID flag) before a real aircraft exists.
- B4UFLY / airspace reminder in the preflight UI (operator still checks the official app).
- Hold/land prompt if the operator flags people or pets on the lawn.
- Hard “no spray” outside geofence; no spray command without confirm.

---

## Uncertainties the operator should read themselves

1. **Is a backyard vinegar/salt **drone** spot-spray an “agricultural aircraft operation” under 14 CFR 137.3?** FAA says check 137.3; the text is purpose-based and includes substances intended for pest control / weeds. No fetched FAA page answers “grocery vinegar on my own lawn from a quad.” Read [137.3](https://www.ecfr.gov/current/title-14/part-137/section-137.3) and [Dispensing Chemicals (Part 137) with UAS](https://www.faa.gov/uas/advanced_operations/dispensing_chemicals) before any real spray flight. Consider asking FAA UAS Support Center (`uashelp@faa.gov`, listed on that page) — operator does that, not a Bot.
2. **Is the flight still 44809 “strictly recreational” once the mission is weed control?** FAA says compensation is not the test; lists agricultural spraying as non-recreational; “when in doubt, assume Part 107.”
3. **FIFRA personal-use vs product-registration** for unlabeled grocery vinegar used as a herbicide. 40 CFR 152.15 is written around **sale/distribution**. Do not assume that makes aerial application legal.
4. **Ready-to-fly mass** (battery + wet tank). Registration + Remote ID almost certainly trigger. Weigh it.
5. **Airspace class at the actual address** — B4UFLY, not this file.
6. **State pesticide agency rules** — state unnamed.
7. **HOA / local** — unknown.
8. **CBO night-lighting procedures** if anyone flies at night.
9. **Remote ID path** for a homemade PX4 (broadcast module vs FRIA vs manufacturer Standard RID — homemade is not Standard RID).
10. **This is not legal advice.** Rules move (recreational page 2026-03-18; TRUST page 2026-08-21; B4UFLY 2026-08-25; Part 137 UAS page 2026-05-05). Re-read the live URLs before hardware flights.

---

*Snapshot author: research pass 2026-08-30 America/Denver. Primary sources only. No registration, no TRUST, no spray, no flight.*
