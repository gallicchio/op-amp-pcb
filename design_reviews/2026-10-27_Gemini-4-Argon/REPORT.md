# Design Review Report: Discrete Transistor Op-Amp, rev A

**Reviewer:** Gemini-4-Argon  
**Date:** 2026-10-27

## 1. Verdict

**Order after named fixes** (high confidence: 95%). The core Lab 5L circuit, the custom SOT-23 silkscreen-schematic symbols and copper routing, the rewiring of `SW2` (`COMPENSATION`) pole 2, the eight B.Cu hops and 36 F.SilkS junction dots, the 102 netlist assertions, ERC, and DRC all pass and faithfully implement Figs. 5L.10 and 5L.15–5L.18 of *Learning the Art of Electronics*. However, before uploading to JLCPCB or handing `docs/HANDBOOK.md` to students, six issues should be fixed:
1. **Terminal-block JLCPCB rotation (`C474881`, `C474882`):** EasyEDA's footprints for `KF301-5.0-2P` and `KF301-5.0-3P` draw the wire-entry mouths and insertion arrows on the `+y` edge, whereas `scripts/gen_footprints.py` draws them on the `-y` edge; at `JLC_ROTATION = 0`, JLCPCB will place `J4`, `J5`, `J6`, and `J7` with their wire openings facing **inward** toward the middle of the board (`+180 deg` fixes this on the symmetric pin row).
2. **`out/opamp/PLACEMENT_CHECKS.txt` lookup bug (`scripts/gen_docs.py`):** Because `gen_docs.py` matches only the first comma-separated designator of each `PREVIEW_CHECKS` row against an LCSC code's designator list, `PLACEMENT_CHECKS.txt` tells the reviewer that `Q2` and `Q6` must have their lone pad at the **TOP** (they are at the **BOTTOM**), that `J7` must face the **LEFT** edge (it is on the **RIGHT** edge), and that `J3` must point off the **LEFT** edge (it points off the **RIGHT** edge), while omitting `look for` lines altogether for `Q3, Q5, Q8`, `D5, D6`, and `TP1`–`TP103`; furthermore, `PREVIEW_CHECKS` states that the lone SOT-23 collector pad is *"on the side the collector wire leaves"*, which is false for 5 of the 8 transistors (`Q2, Q3, Q5, Q6, Q8`).
3. **Follower instability with 1 m (`100 pF`) of coax on `OUT` outside the crossover deadband:** The `+90°` phase margin with `100 pF` on `OUT` quoted in `docs/DESIGN_NOTES.md` is an artifact of running `.ac` at `V(OUT) = 0 V` inside the class-B crossover deadband (`I_C4 ≈ 10 µA`, `r_e4 ≈ 2.6 kΩ`, `Z_out ≈ 2.1 kΩ`). Outside the deadband (`V(OUT) = ±1 V` to `±5 V`), `R15 / R16 = 47 Ω` sit **inside** the `SW3` follower feedback loop (`SW3` pin 2 taps `OUT` downstream of `R15 / R16`), so `100 pF` of coax on `J3` drops the follower's phase margin to `+13.5°` at `+1 V`, `+0.4°` (`-0.7°`) at `±2 V`, **`-9.6°` at `+5 V`** (and **`-4.5°` at `+1 V` into `1 kΩ`**), causing sustained `12.8 MHz` (`184 mV p-p`) oscillation on the flat tops of a `±5 V` square wave. Students should probe `TP9` (`OUT`) with a `10x` probe (`15 pF`, `PM >= +13.7°`) in follower mode rather than hanging a 1 m BNC cable on `J3`, or a `47 Ω` series resistor should be placed between `OUT` and `J3` pin 1.
4. **Scope ground-clip hazard on `TP7` (`Q3 E`) and `TP6` (`Q2 C`):** Contrary to `docs/HANDBOOK.md` (*"The 50 mA supply limit is what saves R8"*), clipping a scope ground lead to `TP7` (`Q3 E`) draws `44.2 mA` through `R8` (`330 Ω 0805`, rated `0.125 W`) and only **`46.8 mA` total** from the `+15 V` supply — so a **50 mA** supply limit **never trips** while `R8` continuously dissipates **`646 mW` (`5.2×` its rating)** and `Q3` suffers **`12.6 V` of reverse emitter-base avalanche breakdown** (`2.5×` its `5.0 V` rating). Even on `TP6` (`Q2 C`), total `+15 V` current is `50.4 mA`, leaving `502–515 mW` (`4.1×` rating) in `R8`.
5. **Handbook loop-voltage table & Exercise 1/4/5 inconsistencies:** `sim/opamp_sim.py` simulates `core()` with ideal `±15.0 V` rails while hardcoding `vrail = 14.6`, so `docs/HANDBOOK.md` lists `TP11 (+15V)` and `TP7 (Q3 E)` as the exact same voltage (`+14.6 V`, implying `0 V` across `R8`), gives `TP4 - TP12 = 1.0 V` (`1.0 mA` instead of `1.4 mA`), and gives `TP11 - TP6 = 0.7 V` (`0.47 mA` instead of `0.72 mA`); `HANDBOOK.md` and `gen_sch.py` still call `Q2 C` and `Q3 C` by their old names `C2` and `C3` in four places; and Exercise 5 fails if the student either forgets to ground `IN-` in open loop (`Q1 B` floats to `-147 mV` via `D1`, `4.3×` beyond `RV1`'s null range, pinning `OUT` at `+13.4 V`) or forgets to un-ground `IN-` before switching `FEEDBACK 2` on (which shorts `OUT` to ground).
6. **Silkscreen & build-script polish:** Moving `R5` `3.2 mm` east from `x = 46.3` to `x = 49.5` (with `"R5" / "62k"` on its left at `x = 47.8`) cleanly resolves the open round-1 overlap where `"Q6 B"` (`TP5`) sat on top of `R5`'s ground via; moving `J6`'s `"-15V"` label `0.5 mm` down clears `D4`'s silkscreen bracket; adding `"50R"` to `RV1` labels the one unlabeled resistance on the board; and fixing `scripts/kienv.py` allows `KICAD_APPIMAGE` to work when KiCad 9 is installed on `PATH`. All of these generator fixes are provided and verified in `fixes.patch`.

---

## 2. Findings

| # | Severity | Where | One-line summary |
|---|---|---|---|
| 1 | **major** | `scripts/layout.py:142-158`, `docs/DESIGN_NOTES.md:120-124` | Follower oscillates (`PM = +0.4°` at `+2 V`, `-9.6°` at `+5 V`, `-4.5°` into `1 kΩ`) with 1 m (`100 pF`) coax on `OUT`; `R15/R16` are inside the `SW3` loop, and the `+90°` figure was a deadband (`Vout = 0`) artifact. |
| 2 | **major** | `scripts/gen_docs.py:328-331,397-399`, `out/opamp/PLACEMENT_CHECKS.txt` | `PLACEMENT_CHECKS.txt` gives backwards orientations for `Q2, Q6`, `J7`, and `J3`, omits `look for` lines for `Q3, Q5, Q8`, `D5, D6`, and `TP1`–`TP103`, and falsely says the lone SOT-23 pad is on the collector-wire side. |
| 3 | **major** | `scripts/parts.py:165-166`, `scripts/gen_footprints.py:206-231` | `KF301` terminal blocks (`C474881`, `C474882`) have wire entry on `+y` in EasyEDA vs `-y` in `gen_footprints.py`; `JLC_ROTATION = 0` places `J4`–`J7` with wire mouths facing inward instead of the board edge. |
| 4 | **major** | `docs/HANDBOOK.md:36-40,215-216`, `scripts/parts.py:139` (`R8`) | A `50 mA` bench-supply limit does **not** save `R8` (`0805`, `0.125 W`) when a scope ground clip shorts `TP7` (`46.8 mA` total rail current `< 50 mA`, `646 mW` in `R8`, `12.6 V` reverse `V_EB` on `Q3`) or `TP6` (`515 mW` in `R8`). |
| 5 | **major** | `sim/opamp_sim.py:18-37,164-169`, `docs/HANDBOOK.md:81-108,139-141` | `opamp_sim.py` simulates `core()` at `±15.0 V` (no Schottky drop) while hardcoding `vrail = 14.6`, making `HANDBOOK.md`'s loop table (`TP11 = +14.6 V` and `TP7 = +14.6 V`) violate KVL in Exercise 1; `core()` also omits `R14` and phase unwrapping. |
| 6 | **major** | `docs/HANDBOOK.md:22,69,149-159`, `scripts/gen_sch.py:606` | Four stale references to nodes `C2` and `C3` (which are now bypass capacitors) instead of `Q2 C` and `Q3 C`; Exercise 5 fails if `IN-` is left open in open-loop (`-147 mV` float via `D1`) or left grounded when closing `FEEDBACK 2` (shorts `OUT` to `GND`). |
| 7 | **minor** | `scripts/kienv.py:55,134-140,204-215` | `kienv.py` ignores `KICAD_APPIMAGE` and `~/.local/bin/kicad-10*.AppImage` whenever system KiCad 9 (`/usr/bin/kicad-cli` and `/usr/share/kicad`) is present on `PATH`. |
| 8 | **minor** | `scripts/layout.py:60,160,175-185,229,278,290-300`, `scripts/gen_pcb.py:425` | Silkscreen schematic issues: `"Q6 B"` sits on `R5`'s ground via (fixed by moving `R5` to `x = 49.5`); `J6`'s `"-15V"` touches `D4`'s outline; `RV1` omits `"50R"`; and `GND_STUBS` have no white silkscreen line from pad to ground symbol. |
| 9 | **minor** | `sim/opamp_sim.py:192-196`, `docs/DESIGN_NOTES.md:52,125`, `docs/HANDBOOK.md:24,55` | Simulated `21.8 mA` short-circuit current includes `4.67 mA` from the `+10 V` input generator leaking through `R2 -> D2 -> R1 -> SW3(follower)` into `OUT`; true op-amp `I_sc` is `+17.2 mA / -15.1 mA`, and `Q7 / Q8` only carry `2.74 mA / 1.14 mA`. |
| 10 | **minor** | `docs/DESIGN_NOTES.md:27`, `CLAUDE_CODE_CHAT.md:55` | Wiper-fault explanation (*"grit under the wiper cannot open the tail: the resistance only rises"*) is backwards for an open wiper: `RV1` pin 2 is the sole path to `TAIL`, so an open wiper opens the tail completely (`I_tail = 0`); only finite contact resistance (`CRV`) is absorbed by `Q6`. |
| 11 | **minor** | `scripts/gen_sch.py:66,553,585,629`, `docs/DESIGN_NOTES.md:70-71`, `scripts/check_circuit.py:139,146,160,185-192` | Unchecked/stale numbers (`Ib = 5 uA` vs `2 uA`; `OUT 10 mA max` vs `15 mA` vs `20 mA`; `"takes a third"` vs `"leaves a third"`; `14 MHz / 100 deg` vs `15 MHz / 106 deg`; box names in `HANDBOOK.md`; missing value assertions in `check_circuit.py`). |
| 12 | **nit** | `docs/history/r.*`, `docs/images/opamp-top-flat.png`, `scripts/check_outputs.py:202-233`, `scripts/gen_docs.py:25-33` | Repository hygiene & cost model: stray committed `docs/history/r.pdf`, `r.png`, `opamp-top-flat.png`; `/home/jason/...` in round-1 logs; dead `check_usb_setback()` code; `$7.77` vs `$7.78` rounding; `$3.00` Extended feeder fee counted on 4 THT codes. |

---

### Detailed Findings

#### Finding 1 — **major**: Follower oscillates with 1 m (`100 pF`) of coax on `OUT` outside the crossover deadband (`PM = +0.4°` at `+2 V`, `-9.6°` at `+5 V`, `-4.5°` into `1 kΩ` at `+1 V`)
- **Where:** `scripts/layout.py` lines 142–158 (`WIRES` for `/OUT`), `scripts/gen_sch.py` lines 348–383, `docs/DESIGN_NOTES.md` section 5 item 3 (lines 120–124).
- **What is wrong, and what was expected:** `docs/DESIGN_NOTES.md` section 5 item 3 states: *"Cable capacitance on OUT is not the problem: with the 47 ohm sense resistors between the emitters and OUT, 100 pF of coax raises the margin to 90 degrees and 10 nF still leaves 30."* That conclusion came from running `.ac` at the quiescent point `Vin = 0 V` (`V(OUT) = -5.6 mV`), where the unbiased class-B push-pull (`Q4`, `Q5`) sits inside its **crossover deadband** (`I_C4 ≈ 10 µA`, `I_C5 ≈ 0`). Inside the deadband, `Q4`'s dynamic emitter resistance is `r_e4 = V_T / I_C4 ≈ 2,600 Ω`, so the open-loop output resistance is `2.6 kΩ || 11 kΩ ≈ 2.1 kΩ` (dominated by `r_e4`, not `R15 = 47 Ω`) and `A_0 = 138`. Adding `100 pF` across `2.1 kΩ` creates a dominant pole at `750 kHz` that lowers `f_unity` to `1.96 MHz` with `+90.1°` phase margin **only while `|V(OUT)| < 50 mV`**.
  Outside the deadband (where the circuit operates whenever a student runs Bring-up Step 7 or Exercise 6 with a `1 V` to `10 V` sine or square wave), `Q4` or `Q5` conducts (`r_e ≈ 24–270 Ω`) and `A_0` rises to `330–368`. Moreover, `SW3` (`FEEDBACK 2`) taps `OUT` **after** `R15 / R16 = 47 Ω` (`J3` pin 1, `J7` pin 1, and `SW3` pin 2 are all on net `/OUT`). Thus `R15` and `R16` are **inside** the feedback loop and do not isolate `J3` from the loop; instead, `Z_out = r_e + 47 Ω ≈ 71–185 Ω` forms an in-loop pole `1 / (2π Z_out C_load)` at `8–22 MHz`, right across unity-gain crossover (`10–15 MHz`).
- **Evidence (`review_sims3.py`, `review_sims3.log`):**
  Small-signal `.ac` phase margin of the follower (`COMPENSATION 1`: `100 pF + 1 kΩ`) vs DC output voltage `V_dc` and load:

  | Operating point | `C_load = 0` (`3 pF` stray) | `C_load = 100 pF` on `OUT` (`J3`) | `10x` probe (`15 pF`) on `OUT` | `47 Ω` before `J3` + `100 pF` coax |
  |---|---|---|---|---|
  | `V_dc = 0.0 V` (deadband, `11 kΩ`) | `A0 = 138.2`, `f_u = 14.25 MHz`, **`PM = +53.7°`** | `f_u = 1.96 MHz`, **`PM = +90.1°`** | **`PM = +65.7°`** | **`PM = +92.7°`** |
  | `V_dc = +0.5 V` (`11 kΩ`) | `A0 = 355.4`, `f_u = 15.63 MHz`, **`PM = +44.3°`** | `f_u = 5.76 MHz`, **`PM = +28.8°`** | **`PM = +29.5°`** | **`PM = +35.0°`** |
  | `V_dc = +1.0 V` (`11 kΩ`) | `A0 = 363.8`, `f_u = 16.59 MHz`, **`PM = +41.4°`** | `f_u = 7.77 MHz`, **`PM = +13.5°`** | **`PM = +20.0°`** | **`PM = +26.2°`** |
  | `V_dc = +2.0 V` (`11 kΩ`) | `A0 = 367.8`, `f_u = 17.19 MHz`, **`PM = +41.4°`** | `f_u = 10.11 MHz`, **`PM = +0.4°`** | **`PM = +13.7°`** | **`PM = +18.2°`** |
  | `V_dc = -2.0 V` (`11 kΩ`) | `A0 = 363.9`, `f_u = 17.35 MHz`, **`PM = +40.2°`** | `f_u = 10.06 MHz`, **`PM = -0.7°`** | **`PM = +13.1°`** | **`PM = +17.6°`** |
  | `V_dc = +5.0 V` (`11 kΩ`) | `A0 = 369.5`, `f_u = 17.30 MHz`, **`PM = +43.2°`** | `f_u = 12.60 MHz`, **`PM = -9.6°`** | **`PM = +18.8°`** | **`PM = +14.8°`** |
  | `V_dc = +1.0 V`, `R_load = 1 kΩ` | `A0 = 336.8`, `f_u = 15.75 MHz`, **`PM = +47.9°`** | `f_u = 14.88 MHz`, **`PM = -4.5°`** | **`PM = +19.2°`** | **`PM = +21.4°`** |

  In `.tran`, driving the follower with a `±5.0 V` square wave (`COMPENSATION 1`) with `C_load = 100 pF` on `OUT` produces **continuous `12.8 MHz` oscillation (`184.0 mV p-p`, 895 half-cycles between `15 µs` and `50 µs`)** on the flat top of the square wave.
- **Proposed fix:**
  1. For rev A documents: update `docs/DESIGN_NOTES.md` section 5 item 3 and `docs/HANDBOOK.md` section 7 step 7 / section 8 exercise 6 to note that `R15 / R16` sit *inside* the `SW3` follower loop, so `OUT` should be probed with a `10x` scope probe on `TP9` (`15 pF`, which stays stable across all output voltages) rather than a long direct BNC coax cable on `J3` when in follower mode.
  2. For rev B (or rev A if modifying the netlist): either put a `47 Ω` isolation resistor between the `/OUT` node (where `SW3` pin 2 and `J7` pin 1 connect) and `J3` pin 1 (outside the feedback loop, which restores `PM >= +14.8°` at `+5 V` with `100 pF` coax), or increase `C1` from `100 pF` to `220 pF`.
- **Confidence:** 99%.

---

#### Finding 2 — **major**: `out/opamp/PLACEMENT_CHECKS.txt` gives wrong orientations for `Q2, Q6`, `J7`, and `J3`, omits `look for` lines for `Q3, Q5, Q8`, `D5, D6`, and `TP1`–`TP103`, and `PREVIEW_CHECKS` misstates the SOT-23 lone-pad rule
- **Where:** `scripts/gen_docs.py` lines 328–331 and 397–399; `out/opamp/PLACEMENT_CHECKS.txt` lines 11–52; `docs/MANUFACTURING.md` lines 153–154; `docs/DESIGN_NOTES.md` line 114.
- **What is wrong, and what was expected:**
  1. In `scripts/gen_docs.py` line 329:
     ```python
     look = next((l for l in PREVIEW_CHECKS if l[0].split(",")[0].strip() in refs), None)
     ```
     `PLACEMENT_CHECKS.txt` groups parts by LCSC code (`C20526`, `C53444`, `C474881`, `C41416668`, `C81598`, `C5199800`), whereas `PREVIEW_CHECKS` splits parts sharing the same LCSC code into separate rows according to their board orientation. Because `next(...)` only tests `l[0].split(",")[0]` and stops at the first match:
     - **`C20526` (`Q1, Q2, Q4, Q6, Q7`)**: prints `should be: lone pad at the TOP, the pair at the bottom` for all five — **wrong for `Q2` and `Q6`**, which are rotated `270°` (`-90°`) and have their lone pad at the **BOTTOM**.
     - **`C53444` (`Q3, Q5, Q8`)**: neither `"Q1"` nor `"Q2"` is in `['Q3', 'Q5', 'Q8']`, so `look` is `None` and `Q3, Q5, Q8` get **no `look for` line at all**.
     - **`C474881` (`J4, J5, J7`)**: prints `should be: facing the LEFT edge` for all three — **wrong for `J7`**, which is on the right edge (`x = 95.5, rot = 270`) and faces the **RIGHT** edge.
     - **`C41416668` (`J1, J2, J3`)**: prints `should be: pointing off the LEFT edge` for all three — **wrong for `J3`**, which is on the right edge (`x = 94.3, rot = 0`) and points off the **RIGHT** edge.
     - **`C81598` (`D1, D2, D5, D6`)**: matches only `"D1, D2"` and omits the specific `"D5 cathode DOWN toward Q7; D6 cathode DOWN toward the bus"` row for `D5, D6`.
     - **`C5199800` (`TP1`–`TP103`)**: `"TP1-TP14"` is not in `refs`, so `look` is `None`.
  2. In `PREVIEW_CHECKS` (`scripts/gen_docs.py` line 397, `docs/MANUFACTURING.md` line 153, `out/opamp/PLACEMENT_CHECKS.txt` line 13) and `docs/DESIGN_NOTES.md` line 114, the check says: *"SOT-23: the lone pad (collector) on the side the collector wire leaves"*.
     In `scripts/gen_pcb.py` (`q_geometry`, lines 515–575) and `scripts/layout.py` (`PLACE`, lines 52–74):
     - Only **`Q1, Q4, Q7`** (NPNs at `rot = 90`) have their lone collector pad (`pad 3`, at top `cy - 0.94`) on the side the collector wire leaves (`cy - 4.0`).
     - For the three PNPs (**`Q3, Q5, Q8`**, placed at `rot = 90`), the emitter wire (`E`, with the inward arrow) leaves at the **TOP** (`cy - 4.0`) and the collector wire (`C`) leaves at the **BOTTOM** (`cy + 4.0`), while the lone collector pad (`pad 3`) is at the **TOP** — i.e., on the **emitter wire's side**!
     - For the two mirrored NPNs (**`Q2, Q6`**, placed at `rot = 270`), the collector wire (`C`) leaves at the **TOP** (`cy - 4.0`) and the emitter wire (`E`) leaves at the **BOTTOM** (`cy + 4.0`), while the lone collector pad (`pad 3`) is at the **BOTTOM** — again on the **emitter wire's side**!
- **Evidence:** `check_pcb_silk_copper.log` section 1 (exact pad coordinates for `Q1`–`Q8`) and `out/opamp/PLACEMENT_CHECKS.txt` lines 11–52.
- **Proposed fix:** In `scripts/gen_docs.py`, iterate over all rows of `PREVIEW_CHECKS` that intersect `refs` (prefixing the matching subset of designators when a code spans multiple orientations) and change the SOT-23 `look for` text to `"SOT-23: the lone pad (collector, pin 3) vs the pair (base and emitter)"`. Included and verified in `fixes.patch`.
- **Confidence:** 100%.

---

#### Finding 3 — **major**: `KF301` screw terminal blocks (`C474881`, `C474882`) have wire entry at `+y` in EasyEDA vs `-y` in `gen_footprints.py`, so `JLC_ROTATION = 0` places `J4`–`J7` 180° backwards (wire mouths facing inward)
- **Where:** `scripts/parts.py` lines 165–166 (`JLC_ROTATION["C474881"]` and `["C474882"]`), `scripts/gen_footprints.py` lines 206–231 (`kf301`).
- **What is wrong, and what was expected:** `scripts/gen_footprints.py` (`kf301`) puts pad 1 at `x = -2.5` (or `-5.0`) and draws the wire-entry mouths on the **`-y` edge** (`yf = -4.0`), stating: *"JLCPCB's land pattern (easyeda) ... draws the body from y = -4.0 to +3.7: the wires enter from -y at rotation 0."*
  However, inspecting the actual EasyEDA footprint SVGs for `C474881` and `C474882` in `scripts/easyeda_cache.json`:
  - In **`C474881` (`KF301-5.0-2P`)**, with `pad 1` at `(-2.50, 0.00)` and `pad 2` at `(+2.50, 0.00)`, the two U-shaped wire-opening cutouts (`id="gge135"` and `id="gge129"` on `layerid="3"`, and `id="gge138"` and `id="gge144"` on `layerid="12"`) are drawn from **`y = +1.50 mm` to `y = +3.70 mm` (`+y` side)**, while the sloped back/top step line (`id="gge41"`) is at `y = -2.20 mm` (`-y` side).
  - In **`C474882` (`KF301-5.0-3P`)**, with `pad 1..3` at `(-5.00, 0), (0, 0), (+5.00, 0)`, the two filled wire-entry directional arrows (`id="gge192"`, `id="gge195"`, `id="gge198"`, `id="gge201"` on `layerid="3"` and `layerid="12"`) are at **`y = +3.50 mm` pointing inward to `y = +1.00 mm` (`+y` side)**.
  - Physically, on a standard `KF301-5.0` block (`datasheets/KF301-5.0-2P_C474881.pdf`), when viewing the wire-entry mouths from the front, pin 1 is on the left; therefore, in top view (`+X` right, `+Y` down) with pin 1 at `-X` (left), the wire-entry mouths face **`+Y` (down)**, not `-Y` (up).
  Because `layout.py` places `J4, J5` on the left edge at `rot = 90` (`-y` facing the left edge, `+y` facing right/inward) and `J6, J7` on the right edge at `rot = 270` (`-y` facing the right edge, `+y` facing left/inward), leaving `JLC_ROTATION = 0` causes JLCPCB to place all four terminal blocks with their wire openings facing **inward toward the center of the board**.
- **Evidence:** EasyEDA SVG polylines/paths extracted in `check_footprints_and_jlc.py` (`C474881` wire cutouts `[(-3.47, 3.7), (-3.47, 1.5), (-1.55, 1.5), (-1.55, 3.7)]` and `[(1.53, 3.7), (1.53, 1.5), (3.45, 1.5), (3.45, 3.7)]`; `C474882` arrow paths `[(2.0, 2.0), (3.0, 2.0), (3.0, 3.5), (2.0, 3.5)]` + `[(2.5, 1.0), (1.5, 2.0), (3.5, 2.0)]`).
- **Proposed fix:** In `scripts/parts.py`, set `JLC_ROTATION["C474881"]` and `JLC_ROTATION["C474882"]` to `180` (since the through-hole rows `(±2.5, 0)` and `(-5, 0, +5)` are symmetric about `(0, 0)`, rotating `+180°` aligns EasyEDA's `+y` wire-entry face with `gen_footprints.py`'s `-y` wire-entry face on the board edge). Included in `fixes.patch`.
- **Confidence:** 95% (verify in JLCPCB's 3D placement preview before paying, as `PLACEMENT_CHECKS.txt` instructs).

---

#### Finding 4 — **major**: The `50 mA` bench-supply current limit does NOT protect `R8` (`330 Ω 0805`, rated `0.125 W`) when a scope ground clip shorts `TP7` (`Q3 E`) or `TP6` (`Q2 C`), nor does it prevent reverse `V_EB` breakdown on `Q3` or `Q6`
- **Where:** `docs/HANDBOOK.md` lines 36–40 and 215–216; `scripts/parts.py` line 139 (`R8` `0805W8F3300T5E`).
- **What is wrong, and what was expected:** `docs/HANDBOOK.md` states:
  - Line 36: *"Set the bench supply's current limit to 50 mA, always, not only for a new board: the board never needs more than 30 mA a rail, and with the limit a scope's ground clip on the wrong loop (Q2 C or Q3 E to ground would otherwise put 0.6 W into the 0805 R8) or a shorted output cannot burn anything."*
  - Line 215: *"a ground clip on a signal loop: Q2 C or Q3 E to ground puts 0.6 W into R8, Q6 E or Q6 B to ground 0.2 W into R7. The 50 mA supply limit is what saves R8; power off and move the clip"*
  Let us check the actual currents and powers (`review_sims_abuse.py`, `review_sims_abuse.log`):
  1. **Ground clip on `TP7` (`Q3 E`)**: `TP7` is the bottom of `R8 = 330 Ω`, whose top is on the `+14.6 V` rail. Grounding `TP7` puts the full `14.6 V` rail across `R8`:
     - `I(R8) = 14.6 V / 330 Ω = 44.24 mA`
     - `P(R8) = (14.6 V)^2 / 330 Ω = 645.9 mW` (**`5.2×` the `125 mW` rating** of the `0805W8F3300T5E` resistor!)
     - Total `+15 V` supply current = `44.24 mA (R8) + 1.35 mA (Q1 + R3) + 1.21 mA (LED1) = 46.8 mA`!
     - Because **`46.8 mA < 50 mA`**, a bench supply current-limited at `50 mA` **never even enters current limit**! It stays at `15.0 V` indefinitely while `R8` dissipates `0.65 W`.
     - Worse yet, grounding `TP7` (`Q3 E = 0 V`) turns `Q3` off, so `R3` pulls `Q2 C` (`Q3 B`) to `+12.62 V`, applying **`V_EB(Q3) = 12.62 V` of reverse voltage** across `Q3`'s emitter-base junction (`2.5×` `MMBT3906LT1G`'s `5.0 V` `V_(BR)EBO` max rating on datasheet p. 1), driving `~6.4 mA` of reverse avalanche current through `R3` into `Q3`'s base-emitter junction.
  2. **Ground clip on `TP6` (`Q2 C`)**: `Q3`'s base is held at `0 V`, so `Q3 E` sits at `+1.56 V` (with `I(R8) = 39.5 mA` flowing into `Q3 E` and out of `Q3 B` into the ground clip) and `I(R3) = 14.6 V / 1.5 kΩ = 9.73 mA`:
     - Total `+15 V` supply current is `50.4 mA`, so a `50 mA` supply limit reduces the rail by less than `1%` (`0.1 V`), leaving **`502–515 mW` (`4.1×` rating)** in `R8` and `142 mW` (`1.14×` rating) in `R3`.
  3. **Ground clip on `TP4` (`Q6 E`) or `TP5` (`Q6 B`)**: Total `-15 V` supply current is only `~18 mA` (far below `50 mA`), while `R7` (`1 kΩ 0805`, rated `125 mW`) dissipates **`213.2 mW` (`TP4`)** or **`192.3 mW` (`TP5`)** (`1.5–1.7×` rating), and on `TP4` `Q6` sees **`12.57 V` of reverse `V_EB`** (`2.1×` `MMBT3904`'s `6.0 V` `V_(BR)EBO` rating).
  4. **Ground clip on `TP13` (`Q1 E`) or `TP14` (`Q2 E`)** in follower mode (`FEEDBACK 2`): Holding `Q1 E / Q2 E` at `0 V` with `IN+ = 0 V` turns `Q2` and `Q3` off, so `OUT` (and thus `IN-`) rails to `-12.8 V`; the `R1–D1–R2` input divider pulls `Q1 B` to `-6.88 V` and `Q2 B` to `-6.18 V` while their emitters are held at `0 V`, putting **`6.88 V` and `6.18 V` of reverse `V_EB`** across `Q1` and `Q2` (exceeding `6.0 V` `V_(BR)EBO`).
- **Evidence:** `review_sims_abuse.py` and `review_sims_abuse.log`; Uni-Royal `0805W8F` datasheet (`1/8 W = 125 mW` at 70°C); onsemi `MMBT3906LT1G` (`C53444`) datasheet p. 1 (`V_EBO = -5.0 Vdc`); JSCJ `MMBT3904` (`C20526`) datasheet p. 1 (`V_EBO = 6 V`).
- **Proposed fix:**
  - In `docs/HANDBOOK.md` lines 36–40 and 215–216, state accurately that the `50 mA` limit protects the rail Schottkys (`D3, D4`) if a rail loop (`TP11, TP12`) is clipped to ground, whereas clipping `TP6` (`Q2 C`) or `TP7` (`Q3 E`) to ground still puts `0.5–0.65 W` into `R8` (so the clip must be moved off if `R8` gets hot, or a `30 mA` limit used when no `1 kΩ` load is attached).
  - For rev B (at zero cost to clarity): change `R7` (`1 kΩ`) to `1206` (`0.25 W`, already in the BOM as `C4410` for `R1, R2` — 0 new BOM lines!) so `TP4 / TP5` ground clips are within rating (`0.21 W < 0.25 W`), and change `R8` (`330 Ω`) to `1206` (or two `1206` resistors in series/parallel) with a `30 mA` bring-up limit.
- **Confidence:** 100%.

---

#### Finding 5 — **major**: `sim/opamp_sim.py` simulates `core()` at `±15.0 V` (without `D3 / D4` Schottky drops) while hardcoding `vrail = 14.6`, making `docs/HANDBOOK.md`'s loop-voltage table and Exercise 1 violate KVL and Ohm's law
- **Where:** `sim/opamp_sim.py` lines 18–37 (`core()`), lines 53–77 (`open_loop()`), lines 164–169 (`results_json()`); `sim/results.json`; `docs/HANDBOOK.md` lines 81–108 and 139–141.
- **What is wrong, and what was expected:**
  In `sim/opamp_sim.py`, `core()` sets `VP vp 0 15` and `VN vn 0 -15` (ideal `±15.000 V` rails with no `D3 / D4` `B5819W` diodes), and then `results_json()` line 169 hardcodes `out["vrail"] = 14.6`. When `docs/HANDBOOK.md` Section 5 prints those mixed numbers rounded to `0.1 V`, three KVL contradictions appear right in the table that students use in **Exercise 1** (*"Measure every loop and account for every 0.6 V. Work out the tail current from TP4 and R7, and check it against the drop across R3 (TP11 minus TP6)"*):
  1. **`TP11` (`+15V` rail after Schottky) = `+14.6 V`** and **`TP7` (`Q3 E`, after `R8 = 330 Ω`) = `+14.6 V`**:
     Because `v(e3) = +14.573 V` was simulated from a `+15.000 V` rail (`15.000 - 0.427 = 14.573 V`), rounding it to `0.1 V` gives `+14.6 V` — identical to `TP11` (`+14.6 V`), implying **`0.0 V` across `R8` and `0 mA` in `Q3`**! With `±14.6 V` rails (or with `B5819W` diodes in the simulation), `TP7` (`Q3 E`) is at **`+14.2 V`** (`+14.18 V` at `±14.6 V` rails; `+14.38 V` with `B5819W` at `4 mA`).
  2. **`TP4` (`Q6 E`) = `-13.6 V`** and **`TP12` (`-15V` rail after Schottky) = `-14.6 V`**:
     The table entry for `TP4` explicitly says `"across R7: 1.4 mA x 1 k | -13.6 V"`, yet from the table `TP4 - TP12 = -13.6 V - (-14.6 V) = 1.0 V`, which gives **`1.0 mA`**, not `1.4 mA`! With a `-14.6 V` rail, `TP4` (`Q6 E`) is at **`-13.3 V`** (`-13.27 V`, so `-13.27 - (-14.6) = 1.33 V -> 1.33 mA`) and `TP5` (`Q6 B`) is at **`-12.6 V`** (`-12.61 V`, not `-13.0 V`).
  3. **`TP11` (`+14.6 V`) minus `TP6` (`Q2 C = +13.9 V`)**:
     Exercise 1 explicitly asks the student to compute `TP11 minus TP6` across `R3 = 1.5 kΩ` and check that it equals half the tail current (`~0.7 mA × 1.5 kΩ = 1.07 V`). Using the table's numbers gives `14.6 V - 13.9 V = 0.7 V` (`0.47 mA`), which fails the check by `35%`! With a `+14.6 V` rail, `TP6` (`Q2 C`) sits at **`+13.5 V`** (`+13.53 V`, so `14.6 - 13.53 = 1.07 V`).
  4. In addition, `core()` in `sim/opamp_sim.py` omits `R14 = 1 kΩ` (`"Ccomp c3 c2 {ccomp}"`), and `open_loop()` (lines 58–75) does not unwrap phase (`math.atan2`), so running `python3 sim/opamp_sim.py` prints `unity gain at 8.91 MHz, phase +137 deg -> phase margin as follower 317 deg` (which is actually `-43 deg` for the bare `100 pF` capacitor).
- **Evidence:** `review_sims.py` and `review_sims.log` section 1:

  | Node / Loop | `opamp_sim.py` (`±15.0 V`, no `D3/D4`) | Actual at `±14.6 V` rails | With `B5819W` (`D3/D4`) from `±15.0 V` | `HANDBOOK.md` Table |
  |---|---|---|---|---|
  | `TP11` (`+15V` rail) | `+15.000 V` (overridden to `+14.6 V`) | `+14.600 V` | `+14.804 V` | `+14.6 V` |
  | `TP12` (`-15V` rail) | `-15.000 V` (overridden to `-14.6 V`) | `-14.600 V` | `-14.802 V` | `-14.6 V` |
  | `TP6` (`Q2 C`) | `+13.914 V` | **`+13.526 V` (`+13.5 V`)** | `+13.723 V` (`+13.7 V`) | `+13.9 V` |
  | `TP7` (`Q3 E`) | `+14.573 V` | **`+14.184 V` (`+14.2 V`)** | `+14.382 V` (`+14.4 V`) | `+14.6 V` |
  | `TP5` (`Q6 B`) | `-12.952 V` | **`-12.606 V` (`-12.6 V`)** | `-12.781 V` (`-12.8 V`) | `-13.0 V` |
  | `TP4` (`Q6 E`) | `-13.613 V` | **`-13.266 V` (`-13.3 V`)** | `-13.442 V` (`-13.4 V`) | `-13.6 V` |

- **Proposed fix:** In `sim/opamp_sim.py`, set `vsup=14.6` as the default in `core()` (or include `D3 / D4` `B5819W` in `core()`), include `R14 = 1k` in `core()`, unwrap phase in `open_loop()`, and regenerate `sim/results.json` and `docs/HANDBOOK.md`.
- **Confidence:** 100%.

---

#### Finding 6 — **major**: Stale `C2` and `C3` node names in `docs/HANDBOOK.md` and `scripts/gen_sch.py` collide with bypass capacitors `C2` and `C3`, and Exercise 5 fails if `IN-` is left open in open-loop or left grounded when closing `FEEDBACK 2`
- **Where:** `docs/HANDBOOK.md` lines 22, 69, 149–159; `scripts/gen_sch.py` line 606.
- **What is wrong, and what was expected:**
  1. **Stale `C2` / `C3` node names:** In Response 2 (`CLAUDE_CODE_CHAT.md` line 142), the probe loops `C2 / E3 / C3` were renamed to `Q2 C / Q3 E / Q3 C` because `C2` (`10 µF`) and `C3` (`100 nF`) are the `+15 V` rail bypass capacitors. However, four places still use the old names `C2` and `C3` to mean `Q2`'s collector and `Q3`'s collector:
     - `docs/HANDBOOK.md` line 22: `"the 100 pF Miller capacitor from C3 back to C2, with 1 k in series"` -> should be `"from Q3 C back to Q2 C"`.
     - `docs/HANDBOOK.md` line 69: `"100 pF + 1 k from C3 to C2 (normal)"` -> should be `"from Q3 C to Q2 C"`.
     - `docs/HANDBOOK.md` line 152 (Exercise 4): `"Note how quickly C3 hits a rail"` -> should be `"Q3 C (TP8)"`.
     - `scripts/gen_sch.py` line 606 (on the schematic sheet): `"into a 3 nF low-pass at C2."` -> should be `"at Q2 C."`.
  2. **Exercise 4 & 5 `IN-` grounding / un-grounding trap (`check_exercises.py`, `check_exercises.log`):**
     - When `FEEDBACK` (`SW3`) has both sliders OFF (open loop), `IN-` has no DC path to ground on the PCB. If a student leaves `IN-` unconnected in Exercises 4 or 5, `Q1`'s `2.3 µA` base bias current must come from `IN+` (`Q2 B`) through the input protection diode `D1` (`1N4148W`). At `2.3 µA`, `D1` drops `143 mV`, pulling `Q1 B` to **`-147 mV`** while `Q2 B` is at `-4 mV`. That `-143 mV` differential input offset is **`4.3×` larger than `RV1`'s entire `±33 mV` null range**, pinning `TP8` (`Q3 C`) at `+14.07 V` and `OUT` at `+13.35 V` regardless of `RV1`'s setting. Thus `IN-` **must** remain grounded during Exercises 4 and 5 (open loop).
     - Conversely, in Exercise 5 (`"Open loop, a 50 mV triangle in. OUT against TP8: a dead band of about 1.2 V where neither Q4 nor Q5 conducts. Now close the loop (FEEDBACK 2) with the same input..."`), if the student keeps `IN-` grounded from the open-loop step and switches `FEEDBACK 2` ON, `SW3` pole 2 ties `OUT` directly to `IN-`, **shorting `OUT` to ground**!
     - Also in Exercise 5, with a `50 mV` peak triangle in open loop (`gain ≈ 377` to `TP8`), `TP8` clips hard at `-14.7 V` and `+14.1 V` (`28.8 V p-p`), so the `1.2 V` deadband is only `4%` of the ramp; a `5–10 mV` peak triangle (with `RV1` adjusted to center `OUT`) shows the `1.2 V` deadband without clipping `Q3`.
- **Evidence:** `check_exercises.py` and `check_exercises.log`.
- **Proposed fix:** Fix all four `C2` / `C3` references in `docs/HANDBOOK.md` and `scripts/gen_sch.py`, and update Exercises 4 and 5 in `docs/HANDBOOK.md` to remind the student to keep `IN-` grounded in open loop (`5–50 mV` triangle) and **un-ground `IN-`** before closing `FEEDBACK 2`. Included in `fixes.patch`.
- **Confidence:** 100%.

---

#### Finding 7 — **minor**: `scripts/kienv.py` ignores `KICAD_APPIMAGE` whenever system KiCad 9 (`kicad-cli` 9.x and `/usr/share/kicad`) is installed
- **Where:** `scripts/kienv.py` lines 55, 134–140, 204–215.
- **What is wrong, and what was expected:** `README.md` line 65 instructs the user to run `export KICAD_APPIMAGE=$HOME/.local/bin/kicad-10.0.7-x86_64.AppImage && ./make.py`. However, in `scripts/kienv.py`:
  1. Line 55 sets `PLAIN_CLI = shutil.which("kicad-cli")` without checking whether `KICAD_APPIMAGE` is set or whether `kicad-cli` on `PATH` is version 10.
  2. Line 137 (`runner()`) checks `if APPRUN is None and _MOUNT is None and PLAIN_CLI is None: _use_appimage()`. On any machine where system KiCad 9 is installed (`/usr/bin/kicad-cli` reporting `'9.0.8'`), `PLAIN_CLI` is not `None`, so `_use_appimage()` is **never called** even when `KICAD_APPIMAGE` is explicitly set and `/home/jason/.local/bin/kicad-10.0.7-x86_64.AppImage` is executable!
  3. Line 206 (`share_dir()`) checks `/usr/share/kicad` before calling `runner()` / `_use_appimage()`, so if `share_dir()` is called first (as in `gen_sch.py` or `check_outputs.py`), it picks KiCad 9's `/usr/share/kicad` instead of mounting the KiCad 10 AppImage.
- **Evidence:** Running `KICAD_APPIMAGE=/home/jason/.local/bin/kicad-10.0.7-x86_64.AppImage ./make.py` on this machine failed with:
  `This project needs KiCad 10; the one that was found reports '9.0.8'. runner /usr/bin/kicad-cli. Point KICAD_APPIMAGE at a KiCad 10 .AppImage...`
- **Proposed fix:** In `scripts/kienv.py`, accept `shutil.which("kicad-cli")` for `PLAIN_CLI` only when `KICAD_APPIMAGE` is unset and `kicad-cli --version` starts with `"10."`, and call `runner()` at the start of `share_dir()` before checking system `/usr/share/kicad`. Included and verified in `fixes.patch`.
- **Confidence:** 100%.

---

#### Finding 8 — **minor**: Silkscreen schematic issues: `"Q6 B"` over `R5`'s ground via, `J6`'s `"-15V"` touching `D4`'s outline, `RV1` missing `"50R"`, and `GND_STUBS` lacking silkscreen wires from pad to ground symbol
- **Where:** `scripts/layout.py` lines 60, 160, 175–185, 229, 278, 290–300; `scripts/gen_pcb.py` lines 425–426, 494–512.
- **What is wrong, and what was expected:**
  1. **`"Q6 B"` (`TP5`) over `R5`'s ground via (listed as open in Section 6 of the brief):** `TP5` is at `(43.5, 74.0)` and its label `"Q6 B"` is at `(45.5, 74.0)` with bounding box `(45.50, 73.21) to (49.16, 74.79)`. `R5` is placed at `(46.3, 71.0)` with its ground via at `(46.3, 74.5)` and ground symbol at `(46.3, 75.05..76.45)`. Thus `"Q6 B"` sits directly over `R5`'s ground via between `R5` and its ground symbol.
     - **Clean fix without re-planning `Q6`:** The right side of the `TAIL` box (`x = 46.5..51.8, y = 67..76`) is empty. Moving `R5` `3.2 mm` east from `(46.3, 71.0)` to `(49.5, 71.0)` (with its ground via at `(49.5, 74.5)` and `"R5" / "62k"` right-justified on its left at `(47.8, 70.3)` and `(47.8, 71.7)`) places `R5` and its ground symbol completely clear of `"Q6 B"` (`x <= 49.16`) with **0 DRC violations**.
  2. **`J6`'s `"-15V"` label touching `D4`'s silkscreen bracket:** When `D4` moved `1.2 mm` east to `(85.5, 87.0, 180)` in Prompt 15, `D4`'s right-hand `F.SilkS` bracket moved to `x = 87.86, y = 86.00..88.00`, intersecting the bounding box `(87.53, 87.61) to (91.40, 89.19)` of `J6`'s `"-15V"` label at `(91.4, 88.4)` (`check_pcb_silk_copper.log` section 3). Moving `"-15V"` to `(91.5, 88.9)` clears both `D4` and `J6` with **0 DRC violations**.
  3. **`RV1` missing its `"50R"` value on the front silkscreen:** `RV1` is in `HIDE_VALUE` (`layout.py` line 228), and `TEXTS` prints `"OFFSET"`, `"NULL"`, `"RV1"`, making `RV1` the only resistor/trimmer on the board whose resistance value (`50R`) is not printed on the front silkscreen. Changing `"RV1"` at `(36.5, 48.8)` to `"RV1 50R"` (with `"OFFSET" / "NULL" / "RV1 50R"` at `y = 45.4, 46.8, 48.2`) adds the value cleanly with **0 DRC violations**. Similarly, `D3` (`B5819W`) and `D5, D6` (`1N4148W`) have only `"D3"`, `"D5"`, `"D6"` on the silkscreen without their part numbers.
  4. **`GND_STUBS` have no white silkscreen wire connecting the pad to the ground symbol:** In `scripts/gen_pcb.py` line 425, `silk_wires()` has `if net == "GND": continue`, and `ground_symbol()` starts `0.55 mm` past the ground via center `(vx, vy)`. As a result, on the bare silkscreen (`opamp-silk-top.png`) and on the green solder-masked PCB, all 16 ground symbols float `2.0 to 5.6 mm` away from their component pads with no white silkscreen line from the pad to the via (most noticeably on `J4, J5, J6, J7`, whose ground tracks run horizontally out of the terminal block and turn 90° down to the via, leaving the ground symbol `5.5 mm` away with no silkscreen wire).
- **Evidence:** `check_pcb_silk_copper.py` and `check_pcb_silk_copper.log`; patched PCB built and DRC-checked (`0 violations`) in `project/`.
- **Proposed fix:** Apply the `R5`, `"-15V"`, and `"RV1 50R"` coordinates in `scripts/layout.py` (included in `fixes.patch`), and optionally draw clipped `GND_STUBS` in `silk_wires()`.
- **Confidence:** 100%.

---

#### Finding 9 — **minor**: Simulated short-circuit output current (`21.8 mA` in `sim/results.json`, quoted as `22 mA` with `"the rest through the sense transistor"`) includes `4.67 mA` from the `+10 V` input generator leaking through `R2 -> D2 -> R1 -> SW3` into `OUT`
- **Where:** `sim/opamp_sim.py` lines 192–196; `docs/DESIGN_NOTES.md` lines 52 and 125–126; `docs/HANDBOOK.md` lines 24, 55, 183.
- **What is wrong, and what was expected:** `sim/opamp_sim.py` computes `isc_ma` by running a follower (`Rfb out inm 1m`) with `Vin = ±10 V` on `inp` (`IN+`) and `Rshort out 0 0.01`. Because `inm` (`IN-`) is tied to `out` (`0 V`) by the follower switch `SW3` while `inp` (`IN+`) is at `+10 V`, the input clamp `D2` conducts `(10 V - 0.76 V) / (R1 + R2) = 4.67 mA` directly from the input source `Vin` through `R2 -> D2 -> R1 -> SW3(pole 2) -> OUT` into the output short!
  Breaking down the exact branch currents into `Rshort` (`review_sims2.log`):
  - **Sourcing (`OUT` shorted to `GND`)**:
    - `I(R15 from Q4)` = **`+14.49 mA`** (`V(R15) = 681 mV`)
    - `I(Q7 collector, from Q3 C via D5)` = **`+2.74 mA`** (`I(R8) = 4.11 mA` minus `I(R9) = 1.37 mA`)
    - **True op-amp short-circuit sourcing current = `+17.23 mA`** (at `Vin = +1.0 V`, total `I_short = +17.40 mA`).
    - Only when `Vin = +10.0 V` in follower mode does an extra **`+4.67 mA`** from the external function generator flow through `R2 -> D2 -> R1 -> SW3` to give `+21.85 mA`.
  - **Sinking (`OUT` shorted to `GND`)**:
    - `I(R16 to Q5)` = **`-13.98 mA`** (`V(R16) = 657 mV`)
    - `I(Q8 collector, to Q3 C via D6 and R9)` = **`-1.14 mA`** (`(-1.38 V - (-15 V)) / 12 kΩ`)
    - **True op-amp short-circuit sinking current = `-15.12 mA`** (plus `-4.67 mA` from `Vin = -10 V` through `R1/D1/R2` in follower mode = `-19.73 mA`).
  Thus `docs/DESIGN_NOTES.md` line 125 (*"The limit holds Q4 or Q5 at about 14.5 mA (22 mA reaches the short, the rest through the sense transistor)"*) and `docs/HANDBOOK.md` line 55 (*"15 mA through Q4 or Q5, 22 mA into a dead short with the sense transistor's share"*) overstate the sense transistor's current by `3×`: `Q7` can never carry more than `2.74 mA` (limited by `Q3`), and `Q8` can never carry more than `1.14 mA` (limited by `R9`).
- **Evidence:** Branch-current decomposition in `review_sims2.py` / `review_sims2.log`.
- **Proposed fix:** Measure `isc_ma` in `sim/opamp_sim.py` with `Vin = ±1.0 V` (or in `x11` / open-loop mode so the input source does not bypass the op-amp into `OUT`), or note in `DESIGN_NOTES.md` / `HANDBOOK.md` that the op-amp itself limits at `17 mA` (`14.5 mA` from `Q4` + `2.7 mA` from `Q3/Q7`) plus up to `4.7 mA` from the input source in follower mode.
- **Confidence:** 100%.

---

#### Finding 10 — **minor**: `docs/DESIGN_NOTES.md` section 2's explanation of the offset-null wiper fault is physically backwards for a lifted wiper
- **Where:** `docs/DESIGN_NOTES.md` line 27; `CLAUDE_CODE_CHAT.md` line 55.
- **What is wrong, and what was expected:** `docs/DESIGN_NOTES.md` line 27 says of `RV1`: *"Its wiper is the tail, so grit under the wiper cannot open the tail: the resistance only rises"*.
  Look at the schematic (`scripts/gen_sch.py` lines 224–228): `RV1` pin 3 is `Q1 E`, `RV1` pin 1 is `Q2 E`, and `RV1` pin 2 (the wiper) is the **only** connection to `TAIL`. All tail current from both `Q1` and `Q2` flows out through the wiper (`pin 2`). If grit under the wiper causes the wiper contact to go **open-circuit**, the tail **is** completely opened (`I_tail = 0`, `Q1` and `Q2` turn off, `V(Q2 C) = +15 V`, `V(OUT) = -13.5 V`, as verified in `review_sims.log` section 2: `Wiper OPEN: v(c2)=+15.000V, v(c3)=-14.538V, v(out)=-13.471V`).
  What wiring the wiper to `TAIL` actually achieves is immunity to finite **contact resistance variation (`CRV`)** of the wiper: any finite contact resistance `R_wiper` sits in series with the high-impedance collector of the `Q6` current sink (`~1 MΩ`), where it drops only `I_tail × R_wiper` of collector compliance without disturbing the `Q1 / Q2` emitter balance.
- **Evidence:** `scripts/check_circuit.py` lines 97–99 and `review_sims.log` section 2.
- **Proposed fix:** Reword `docs/DESIGN_NOTES.md` line 27 to: *"Its wiper feeds the high-impedance tail sink, so wiper contact resistance (CRV) is absorbed in series with the tail without unbalancing the pair."* Included in `fixes.patch`.
- **Confidence:** 100%.

---

#### Finding 11 — **minor**: Unchecked and stale numbers/names across `scripts/gen_sch.py`, `docs/HANDBOOK.md`, `docs/DESIGN_NOTES.md`, and `scripts/check_circuit.py`
- **Where:** `scripts/gen_sch.py` lines 66, 553, 585, 629; `docs/HANDBOOK.md` lines 21, 22, 25, 48, 89, 180; `docs/DESIGN_NOTES.md` lines 70–71; `scripts/check_circuit.py` lines 139, 146, 160, 185–192.
- **What is wrong, and what was expected:**
  1. **`scripts/gen_sch.py` line 585 (`INPUT PROTECTION` note on schematic):** says `"Ib (about 5 uA) drops 5 mV across it"`, whereas `docs/HANDBOOK.md` line 180 and the back silkscreen (`layout.py` line 410) say `"2 uA"` (`0.69 mA / 300 = 2.3 µA -> 2.3 mV`).
  2. **`scripts/gen_sch.py` line 629 (`OUTPUT` note on schematic):** says `"-14 to +13 V into the 11k; 10 mA max."`, whereas `docs/HANDBOOK.md` line 48 and the back silkscreen (`layout.py` line 415) say `"±12 V into 1k, 15 mA"`, and the front silkscreen beside `J3` (`layout.py` line 269) says `"±13 V 20 mA"`.
  3. **`scripts/gen_sch.py` line 553 (top story block on schematic):** says `"gain Q3, PNP common emitter: 12k / (330 + re) = 30; the push-pull's dead zone takes a third of it x12"`. Since `34 × 0.365 = 12.4`, the dead zone **leaves** a third of it (or takes **two thirds** of it). Also, line 66 (title block comment) says `"difference x11, gain x12, follower x1"` without noting that `x12` includes the resting push-pull's `0.37` dead-zone factor.
  4. **Stage box names in `docs/HANDBOOK.md` section 1 (lines 21, 22, 25):** lists `GAIN x30`, `COMPENSATION`, and `FEEDBACK`, whereas the board's silkscreen boxes are titled `GAIN STAGE x30`, `OPTIONAL COMPENSATION`, and `OPTIONAL FEEDBACK`.
  5. **`docs/DESIGN_NOTES.md` lines 70–71:** quotes `about 100 degrees` for the bare-100pF x11 phase margin (`sim/results.json` has `105.8°`) and `14 MHz` for the simulated unity-gain crossing (`sim/results.json` has `14.96 MHz`, quoted as `15 MHz` in the review brief).
  6. **`scripts/check_circuit.py` lines 139, 146, 160, 185–192:**
     - Line 139 hardcodes `100e-12` and `1000` in `f_z = 1 / (2 * math.pi * 100e-12 * (1000 - 350))` instead of using `farads(N.value["C1"])` and `ohms(N.value["R14"])`.
     - Line 146 has a stale comment `# 33 ohm in each emitter` above the `47` ohm check.
     - Line 160 hardcodes `11000 / 1000` instead of `(ohms(N.value["R10"]) + ohms(N.value["R11"])) / ohms(N.value["R11"])`.
     - Lines 185–192 never check the values or footprints of `C2`–`C5` (`10uF`, `100nF`), `R12` (`10k`), `R13` (`10k`), `D1, D2, D5, D6` (`1N4148W`), or `D3, D4` (`B5819W`).
- **Evidence:** `scripts/gen_sch.py`, `docs/HANDBOOK.md`, `docs/DESIGN_NOTES.md`, `scripts/check_circuit.py`.
- **Proposed fix:** Included and verified in `fixes.patch` (`108 circuit checks passed`).
- **Confidence:** 100%.

---

#### Finding 12 — **nit**: Repository hygiene, stray tracked files, and cost-model details
- **Where:** `docs/history/r.pdf`, `docs/history/r.png`, `docs/images/opamp-top-flat.png`; `design_reviews/2026-10-24_Claude-Fable-5.1/build.log` & `build_patched.log`; `CLAUDE_CODE_CHAT.md` line 10; `scripts/check_outputs.py` lines 202–233; `scripts/gen_outputs.py` line 197 vs `scripts/gen_docs.py` line 111; `scripts/gen_docs.py` lines 25–33.
- **What is wrong, and what was expected:**
  1. Scratch render files `docs/history/r.pdf` (193 KB) and `docs/history/r.png` (536 KB) and obsolete `docs/images/opamp-top-flat.png` (99 KB, no longer generated by `gen_outputs.py`) are committed in git.
  2. `design_reviews/2026-10-24_Claude-Fable-5.1/build.log` and `build_patched.log` contain the local path `/home/jason/.local/bin/kicad-10.0.7-x86_64.AppImage`, and `CLAUDE_CODE_CHAT.md` line 10 mentions `~/mudd/pcbs/op-amp-pcb/datasheets_not_in_git/Tom_Hayes_Paul_Horowitz_Learning_the_Art_of_Electronics.pdf`.
  3. `scripts/check_outputs.py` lines 202–233 defines an unused function `check_usb_setback()` (`HRO TYPE-C-31-M-12`) copied from another board.
  4. `scripts/gen_outputs.py` prints `parts $7.77/board` (summing unrounded `price * qty = $7.7745`), whereas `scripts/gen_docs.py` prints `parts $7.78/board` (summing the 4-decimal rounded `"Ext $"` column `= $7.7790`).
  5. In `scripts/gen_docs.py` lines 25–33, `EXTENDED_PART_FEE = 3.00` is multiplied by all `7` Extended codes (`$21.00`), whereas 4 of the 7 Extended codes (`C41416668`, `C474881`, `C474882`, `C52754333`) are THT parts that are hand/wave-soldered and do not incur JLCPCB's `$3.00` SMT feeder loading fee (only the 3 SMT Extended codes `C53444`, `C54949`, `C5199800` = `$9.00` do); conversely, `LeadFree HASL` (`~$1.50–$4.50`) and `Remove Mark` (`~$1.50`) add small PCB surcharges above the `$2.00` leaded-HASL base price.
- **Confidence:** 100%.

---

## 3. Section 3's Questions Answered by Number

### 1. The circuit against the book (`scripts/gen_sch.py`, `out/opamp.net`, `docs/DESIGN_NOTES.md` section 1)
- **Is every value and every connection the book's?**
  Verified stage by stage against *Learning the Art of Electronics* (Hayes & Horowitz, 2016), Lab 5L, Figs. 5L.10, 5L.12–5L.18 (pp. 214–218):
  - **Difference amplifier (Fig. 5L.12 / 5L.15):** `Q1, Q2` (`MMBT3904`), collector load `R3 = 1.5 kΩ` from `+15V` to `Q2 C` (`IN+` side), `Q1 C` tied directly to `+15V`. Matches the book.
  - **Tail (Fig. 5L.10 / 5L.12):** `SW1` selects either `Q6` (`MMBT3904`) current sink (`R5 = 62 kΩ` to `GND`, `R6 = 10 kΩ` to `-15V`, `R7 = 1 kΩ` emitter resistor to `-15V`, pole 1) or `R4 = 10 kΩ` to `-15V` (pole 2). Matches the book's first bipolar current sink in Fig. 5L.10 (`62k / 10k / 1k`, p. 214) and resistor tail (`10k`, p. 212).
  - **Gain stage (Fig. 5L.13 / 5L.15):** `Q3` (`MMBT3906`) PNP common-emitter stage, base driven directly from `Q2 C`, emitter resistor `R8 = 330 Ω` to `+15V`, collector resistor `R9 = 12 kΩ` to `-15V`. Matches the book.
  - **Compensation (Fig. 5L.17):** `C1 = 100 pF` between `Q3 C` and `Q2 C` (via `SW2`), with the board's added `R14 = 1 kΩ` bypassed by `SW2` pole 2. Matches the book when `SW2` pole 2 is on.
  - **Push-pull output and feedback divider (Figs. 5L.14–5L.18):** `Q4` (`MMBT3904`, collector to `+15V`) and `Q5` (`MMBT3906`, collector to `-15V`) emitter follower driven by `Q3 C`, driving the `R10 = 10 kΩ` / `R11 = 1 kΩ` divider to `GND` whose tap `X` (`OUT / 11`) returns to `IN-` via `SW3` pole 1 (Fig. 5L.16) or `OUT` returns to `IN-` via `SW3` pole 2 (Fig. 5L.18). Matches the book.
- **Is `Q3` drawn and wired the right way up for a PNP?**
  Yes. On the schematic (`scripts/gen_sch.py` line 264), `Q3` uses `Transistor_BJT:MMBT3906` with `mirror="x"`, placing pin 2 (emitter, with inward arrow) at the top (`+15V` via `R8 = 330 Ω`), pin 3 (collector) at the bottom (`-15V` via `R9 = 12 kΩ`), and pin 1 (base) on the left (`Q2 C`). On the PCB (`scripts/gen_pcb.py` `q_geometry("Q3")`), `TRANSISTORS["Q3"] = ("PNP", "left")` sets `n = -1`, drawing the emitter leg and inward-pointing arrow at the top (`E` label inside top of circle, wired to `R8`) and the collector leg at the bottom (`C` label inside bottom of circle, wired to `Q3 C` and `R9`). (Note: on the SOT-23 package itself, `Q3` is at `rot = 90` so physical pad 3 [collector] is at top-center and physical pad 2 [emitter] is at bottom-right; `q_geometry` routes the collector hairline/copper down between pads 1 and 2 and the emitter hairline/copper around pad 3 to the top leg — see Finding 2.)
- **Does `check_circuit.py` assert everything that matters, and what does it not assert?**
  `check_circuit.py` asserts 102 topology and value properties, including the rewiring of `SW2` pole 2 and `Q7 / Q8 / D5 / D6`. What it did **not** assert (see Finding 11): the values/footprints of `C2`–`C5`, `R12`, `R13`, and `D1`–`D6`; it also hardcoded `100e-12`, `1000`, and `11000 / 1000` in two formulas instead of reading `C1`, `R14`, `R10`, and `R11` from the netlist.

### 2. What the board adds (`docs/DESIGN_NOTES.md` section 2)
- **2a. Offset null (`RV1` `50 Ω` between emitters, wiper to tail):**
  - **Null range:** With `RV1` swept from `pot = 0.0` to `1.0` (`review_sims.log` section 2), the follower output offset shifts from `-37.51 mV` to `+28.83 mV` (a total span of `66.34 mV`, or **`±33.2 mV`** around the `-4.34 mV` midpoint). All documents (`HANDBOOK.md`, `DESIGN_NOTES.md`, `MANUFACTURING.md`), `parts.py`, `gen_sch.py`, and `check_circuit.py` now consistently quote `±33 mV`.
  - **Stage 1 gain with the wiper at an end:** In closed-loop follower bias (`V(OUT) ≈ 0 V`), `Q2`'s collector current is fixed by `Q3`'s `V_BE` and `R8` drop at `~0.72 mA`, and the total resistance in the emitter loop (`r_e1 + RV1a + RV1b + r_e2 ≈ 38 + 50 + 36 = 124 Ω`) is constant regardless of wiper position, so Stage 1's small-signal differential gain is **`11.13` at `pot = 0.0`**, **`11.11` at `pot = 0.5`**, and **`11.11` at `pot = 1.0`** (in open-loop with `IN+ = IN- = 0 V`, `G1` drops slightly from `11.15` at centre to `10.30` / `10.17` at the ends because the `33 mV` imbalance shifts `I_E1 / I_E2` by `±0.5 mA`).
  - **What happens if the wiper opens or the ends short:** If the wiper (`pin 2`) opens, `TAIL` is completely disconnected (`I_tail = 0`), killing the diff pair and driving `OUT` to `-13.47 V` (contradicting `DESIGN_NOTES.md` line 27 — see Finding 10). If the ends (`pins 1 and 3`) short together, `Q1 E` and `Q2 E` are tied directly together (`0 Ω` differential degeneration), raising Stage 1's differential gain from `11.11` to **`17.92`** (`A_0 = 240.7`) and reducing the null range to `0 mV`.
- **2b. Input protection (`R1 / R2` `1 kΩ 1206` and `D1 / D2` `1N4148W` anti-parallel between bases):**
  - **Worst case a student can produce (`+15 V` on one input, `-15 V` on the other):**
    Total series resistance is `R1 + R2 = 2 kΩ` in series with one conducting `1N4148W` (`V_F = 0.785 V` at `14.6 mA`). Current is `(30.0 - 0.785) / 2000 = 14.61 mA`. Power in each `1206` resistor (`R1`, `R2`) is `(14.61 mA)^2 × 1 kΩ = 213.4 mW` (**`0.21 W`**), safely within the `0.25 W` (`250 mW`) rating of `1206W4F1001T5E` (`C4410`). Power in `D1` or `D2` is `11.5 mW` (rated `400 mW`). (If a student applies `+20 V` and `-20 V` from two external supplies/generators simultaneously, `I = 19.6 mA` and `P(R1) = P(R2) = 385.6 mW`, `1.54×` rating.)
  - **Base-emitter reverse voltage on the off transistor:** With one input at `+15 V` and the other at `-15 V`, `D1 / D2` clamp `|V(Q1 B) - V(Q2 B)|` to `0.785 V`, while the conducting transistor holds `TAIL` (`RV1`) within `0.65–0.72 V` of its base; the off transistor's base-emitter junction is reverse-biased by at most **`0.14 V`** (with `RV1` at an extreme) or **`0.02 V`** (with `RV1` centred) — completely safe against `MMBT3904`'s `6.0 V` `V_(BR)EBO`.
  - **Does the clamp interfere with normal use?** In linear closed-loop circuits and small-signal open-loop exercises (`|V_diff| < 100 mV`), `D1 / D2` conduct `< 50 nA` and add `~2 pF` across the bases (`f_-3dB ≈ 40 MHz` with `R1 || R2`). In the comparator / Schmitt trigger / relaxation oscillator of Lab 8L (`8L.1`, `8L.1.3`, `8L.2`), once `|V(IN+) - V(IN-)| > 0.7 V`, the input impedance between `IN+` and `IN-` drops to `R1 + R2 = 2 kΩ`, which loads high-impedance positive-feedback dividers unless hysteresis is kept below `~1 V` or lower divider resistances (`~1 kΩ`) are used (as `HANDBOOK.md` section 9 notes).
- **2c. `R14`, the `1 kΩ` in series with `C1 = 100 pF`:**
  - **Right-half-plane zero argument with `R8 = 330 Ω` degeneration:** At `I_C3 = 1.30 mA`, `Q3`'s intrinsic emitter resistance is `r_e3 = 26 mV / 1.30 mA = 20 Ω`. With unbypassed emitter resistor `R8 = 330 Ω`, `Q3`'s effective stage transconductance is `G_m3 = 1 / (r_e3 + R8) = 1 / 350 Ω = 2.86 mS`. A bare Miller capacitor `C1 = 100 pF` introduces a feedforward **right-half-plane (RHP) zero** at `f_z = G_m3 / (2π C1) = 1 / (2π × 100 pF × 350 Ω) = 4.55 MHz`, which adds phase lag instead of lead and drives the follower's phase margin to `-39.4°` (`-42.6°` at `15 MHz`). Inserting `R14 = 1 kΩ > 1 / G_m3 = 350 Ω` moves the zero into the **left-half plane (LHP)** at `f_z = 1 / (2π C1 (R14 - 1/G_m3)) = 1 / (2π × 100 pF × 650 Ω) = 2.45 MHz`, providing positive phase lead near unity-gain crossover and yielding `+50.8°` (`+53.7°` interpolated) follower phase margin.
  - **Do the switch positions do what `HANDBOOK.md` says?** Yes: `SW2` pin 4 (`Q2 C`) -> pin 1 -> `R14` -> `C1` -> `Q3 C` gives `100 pF + 1 kΩ` when slider 1 is ON; `SW2` pin 3 (`Q2 C`) -> pin 2 -> `R14/C1` junction bypasses `R14` directly from `Q2 C` to `C1` when slider 2 is ON (whether slider 1 is ON or OFF); both OFF leaves `C1` disconnected from `Q2 C`.
- **2d. Output current limit (`R15 / R16 = 47 Ω`, `Q7 / Q8`, `D5 / D6`):**
  - **Limit value (`0.65 V / 47 Ω` vs simulated `21.8 mA`), both polarities:** As proven in Finding 9 (`review_sims2.log`), `Q4 / R15` limits at **`+14.49 mA`** (`V(R15) = 681 mV`) and `Q5 / R16` limits at **`-13.98 mA`** (`V(R16) = 657 mV`). In addition, `Q7` routes `Q3`'s clamped collector drive (`I(R8) - I(R9) = 4.11 - 1.37 = +2.74 mA`) into `OUT`, and `Q8` routes `R9`'s pull-down current (`-1.14 mA`) from `OUT`, giving a true op-amp short-circuit output current of **`+17.23 mA` sourcing** and **`-15.12 mA` sinking**. The `21.8 mA` (`-19.7 mA`) figure in `sim/results.json` includes `±4.67 mA` from the `±10 V` input generator leaking through `R2 -> D1/D2 -> R1 -> SW3(follower)` into `OUT`.
  - **`OUT` shorted to `GND`, to `+15 V`, and to `-15 V` (power in `Q4` or `Q5` in SOT-23, and for how long):**
    - **`OUT` shorted to `GND` (`0 V`)**: With `±14.6 V` rails, `V_CE(Q4) = 14.6 - 0.68 = 13.92 V` at `I_C4 = 14.49 mA`, so **`P(Q4) = 201.7 mW`** (`207.5 mW` at `±15.0 V`); in the negative polarity, `V_EC(Q5) = 13.94 V` at `I_C5 = 13.98 mA`, so **`P(Q5) = 194.9 mW`**. The stocked `MMBT3904` (`C20526`, JSCJ datasheet p. 1) is rated `P_C = 200 mW` at `T_a = 25°C` (`R_θJA = 625 °C/W`, `T_J(max) = 150°C`) and `MMBT3906LT1G` (`C53444`, onsemi datasheet p. 1) is rated `P_D = 225 mW` (`R_θJA = 556 °C/W`). At `202 mW`, `T_J ≈ 25°C + 0.202 W × 625 °C/W = 151°C` at steady state, so a short to ground is survived for minutes (and indefinitely if `T_a <= 24°C`).
    - **`OUT` shorted to `-15 V` (`-14.6 V`)**: `Q4` drops `2 × 14.6 - 0.69 = 28.51 V` at `I_C4 = 14.71 mA`, dissipating **`P(Q4) = 419.4 mW`** (`431 mW` at `±15.0 V`).
    - **`OUT` shorted to `+15 V` (`+14.6 V`)**: `Q5` drops `28.52 V` at `I_C5 = 14.42 mA`, dissipating **`P(Q5) = 411.3 mW`** (`423 mW` at `±15.0 V`).
    - At `~0.42 W` (`2.1×` rating), steady-state `T_J` would reach `25 + 0.42 × 625 = 288°C`, and an SOT-23 die/leadframe (`thermal time constant ~ 2–5 s`) crosses `150°C` in **`~3–6 seconds`**. Thus `HANDBOOK.md`'s revised statement (*"so a short to ground is survived for minutes, not an afternoon: 0.21 W in a SOT-23 whose stocked part is rated 0.2 W. A short to a rail puts 0.43 W into Q4 or Q5, twice its rating: a slip, not a minute"*) is **true**.
  - **Do `D5 / D6` and `Q7 / Q8` disturb normal operation?** No (`review_sims3.log` section 2d): removing `Q7, Q8, D5, D6` changes `A_0` from `138.2` to `138.4`, follower `f_unity` from `14.25 MHz` to `13.96 MHz`, follower `PM` from `+53.7°` to `+55.2°` (`1.5°` difference), and swing (`-14.29 V` to `+13.41 V`) by `< 0.01 V`.
- **2e. `D3 / D4` `B5819W` in the rails:**
  - **Polarity & drop:** `D3` has anode (`pin 2`) on `+15V_IN` and cathode (`pin 1`) on `+15V`; `D4` has cathode (`pin 1`) on `-15V_IN` and anode (`pin 2`) on `-15V`. At `~3.9 mA` quiescent rail current, `B5819W` (`C8598`, JSCJ datasheet p. 2) drops `~0.20–0.23 V` at `25°C` (rising to `~0.32 V` at `30 mA`).
  - **Reversed supply / `+15 V` and `-15 V` swapped:** `D3` and `D4` are reverse-biased by `15 V` each (well below `B5819W`'s `40 V` `V_RRM` rating); `< 10 µA` leakage flows; neither LED lights; no transistor is stressed.
  - **Single supply (`+15 V` only or `-15 V` only):** Simulated in `review_sims_abuse.log` section 2: with `+15 V` only (`-15 V` at `0 V` or open), or `-15 V` only (`+15 V` at `0 V` or open), all resistor and transistor powers are `< 5 mW` and no junction sees reverse `V_EB > 0.7 V`.
  - **`+30 V` on one terminal:** If `+30 V` is applied to `+15V_IN` (or `-30 V` to `-15V_IN`) relative to `GND` (which also happens if a student swaps the `GND` lead with the `+15 V` or `-15 V` lead on `J6`!), the transistors and resistors survive (`P(Q6) = 86 mW`, `P(R9) = 76 mW`), **but the bulk decoupling capacitor `C2` or `C4` (`10 µF 0805 X5R`, `C15850`, `CL21A106KAYNNNE`) is rated for `25 V` (`"A" = 25 V`) and sees `29.7 V` (`1.19×` its maximum voltage rating)!** Upgrading `C2, C4` to a `35 V` or `50 V` `10 µF` capacitor in rev B eliminates this overvoltage risk.
- **2f. LEDs and bypass capacitors:**
  - `LED1` (`+15V` -> `R12 = 10 kΩ` -> `LED1` anode pin 2, cathode pin 1 -> `GND`) and `LED2` (`GND` -> `LED2` anode pin 2, cathode pin 1 -> `R13 = 10 kΩ` -> `-15V`) run at `(14.6 - 2.7) / 10 kΩ = 1.19 mA` (`P(R12) = P(R13) = 14 mW`), well within `KT-0805G`'s `30 mA` rating (`C2297` datasheet p. 3).
  - `C2, C4` (`10 µF 25V X5R 0805`) and `C3, C5` (`100 nF 50V X7R 0805`) bypass `+15V` and `-15V` to `GND`.

### 3. Stability and the simulation (`sim/opamp_sim.py`, `sim/results.json`)
- **3.0. Models vs `MMBT3904` / `MMBT3906LT1G` datasheets:**
  - `sim/opamp_sim.py` uses `Bf = 300` (`NPN`) / `200` (`PNP`), `VAF = 100`, `CJC = 4.0 pF` / `4.5 pF`, `CJE = 8 pF` / `10 pF`, `TF = 350 ps`.
  - Against JSCJ `MMBT3904` (`C20526`) and onsemi `MMBT3906LT1G` (`C53444`) datasheets: `h_FE` at `1–10 mA` is `100–300` (matches `Bf = 300 / 200`); `C_obo` at `5 V` is `4.0 pF max` (NPN, typical `~2.2 pF`) and `4.5 pF max` (PNP), so `CJC = 4.0 / 4.5 pF` zero-bias in SPICE is slightly conservative; `C_ibo` at `0.5 V` is `8.0 pF max` (NPN) and `10.0 pF max` (PNP), matching `CJE = 8 / 10 pF`; `f_T` at `10 mA, 20 V` is `300 MHz` (NPN) / `250 MHz` (PNP), whereas at `I_C = 0.7–1.3 mA` the JSCJ curve (p. 2) shows `f_T ≈ 150–180 MHz`, which is why the real board's unity-gain crossing will be `~5–8 MHz` rather than `14–15 MHz`.
- **3a. A `10x` scope probe (`10` to `15 pF` // `10 MΩ`) on `TP8` (`Q3 C`) or `TP6` (`Q2 C`), with and without the `1 kΩ` (`review_sims3.log` section 3a):**
  - **With `1 kΩ` (`COMPENSATION 1`):**
    - No probe (`3 pF` stray): Follower `f_u = 14.25 MHz`, **`PM = +53.7°`** (`50.8°` grid-sampled); `x11` `f = 409.1 kHz`, **`PM = +119.8°`**.
    - `10 pF` probe on `TP8` (`Q3 C`): Follower `f_u = 12.17 MHz`, **`PM = +44.4°`**; `x11` **`PM = +119.0°`**.
    - `15 pF` probe on `TP8` (`Q3 C`): Follower `f_u = 11.31 MHz`, **`PM = +42.3°`** (outside deadband at `V_dc = +1 V`: **`PM = +30.8°`**); `x11` **`PM = +118.5°`**.
    - `10 pF` probe on `TP6` (`Q2 C`): Follower `f_u = 13.54 MHz`, **`PM = +40.9°`**; `x11` **`PM = +119.0°`**.
    - `15 pF` probe on `TP6` (`Q2 C`): Follower `f_u = 13.00 MHz`, **`PM = +37.0°`**; `x11` **`PM = +118.8°`**.
    - `15 pF` probes on **BOTH** `TP6` and `TP8`: Follower `f_u = 10.52 MHz`, **`PM = +25.5°`**; `x11` **`PM = +117.5°`**.
    - Conclusion: With `COMPENSATION 1`, the follower remains stable even with `15 pF` probes on both `TP6` and `TP8`.
  - **Without `1 kΩ` (`COMPENSATION 2`, bare `100 pF`):**
    - Follower has negative phase margin in all cases (`-39.4°` no probe, `-42.7°` / `-43.7°` with `10 / 15 pF` on `TP8`, `-44.1°` / `-45.8°` with `10 / 15 pF` on `TP6`, `-47.4°` with both) and rings/oscillates at **`3.83 MHz`** (`580 mV p-p`), as Exercise 8 intends.
    - `x11` amplifier stays stable (`PM = +104.5°` to `+105.9°`).
  - **With both `COMPENSATION` sliders OFF (no `C1`):**
    - Follower oscillates at **`13.79 MHz`** (`PM = -30.3°` to `-51.7°`).
    - `x11` amplifier has only **`+19.8°`** margin (`+7.7°` with `15 pF` on `TP6`) and rings heavily at **`8.11 MHz`**.
- **3b. A metre of coax on `OUT` (`100 pF`) with `FEEDBACK 2` (follower): does it ring, and is the rev B `"47 ohm in series with OUT"` item still needed?**
  - **Yes, it rings/oscillates outside the deadband, and the rev B item IS still needed!** See Finding 1 (`review_sims3.log` section 3b and bias-sweep table): while `PM = +90.1°` inside the `V(OUT) = 0 V` crossover deadband (where `r_e4 = 2.6 kΩ`), on a `±0.5 V` step `100 pF` gives `6.7%` overshoot, at `V(OUT) = ±2 V` `PM` drops to **`+0.4° / -0.7°`**, at `V(OUT) = +5 V` `PM` is **`-9.6°`** (producing continuous `12.8 MHz`, `184 mV p-p` oscillation on a `±5 V` square wave), and with `R_load = 1 kΩ` at `V(OUT) = ±1 V` `PM` is **`-4.5° / -4.8°`**. Because `SW3` pin 2 connects to `OUT` *after* `R15 / R16`, `R15 / R16` are inside the feedback loop and do not isolate coax capacitance on `J3`. A `47 Ω` resistor placed between `OUT` and `J3` pin 1 (outside the `SW3` feedback loop) restores `PM = +14.8°` at `+5 V` and `+18.2°` at `+2 V`.
- **3c. Both `FEEDBACK` sliders ON (`R10` shorted):**
  - Shorting `R10` ties `OUT` and `X` both to `IN-`, configuring a **voltage follower loaded by `R11 = 1 kΩ` to ground** (`review_sims3.log` section 3c): `V_os = -3.04 mV`, small-signal `A_0 = 15.2` at `V(OUT) = 0 V` (`336.8` outside the deadband), `PM = +100.0°` at `0 V` (`+47.9°` at `±1 V`), and output swing into the `1 kΩ` load is **`-11.96 V` to `+11.96 V`** (current-limited by `R15/Q7` and `R16/Q8` at `±12.0 mA`). Completely harmless and matches `HANDBOOK.md` line 73.
- **3d. The `x11` amplifier with `2 V` peak in, the slew rate, and the crossover deadband at `TP8`:**
  - **`x11` amplifier with `2 V` peak (`1 kHz`) in:** `OUT` clips cleanly at **`-14.28 V` and `+13.41 V`** into the `11 kΩ` divider (with `±15.0 V` rails; **`-13.89 V` and `+13.02 V`** with `±14.6 V` post-Schottky rails).
  - **Slew rate (`review_sims3.log` section 3d):** On a `±5 V` (`10 V p-p`) follower step (`COMPENSATION 1`), rising slew rate is **`4.44 V/µs`** and falling slew rate is **`4.47 V/µs`** (`5.13 V/µs` rise / `5.18 V/µs` fall on a `±10 V` step), limited by `I_tail / C1 ≈ (0.7 mA) / 100 pF`.
  - **Crossover deadband at `TP8` (`Q3 C`):** In open loop, neither `Q4` nor `Q5` conducts significantly while `V(TP8)` traverses **`-0.55 V` to `+0.56 V` (`~1.12 V` deadband into `11 kΩ`, `~1.25 V` into `1 kΩ`)**. In closed-loop follower mode with a `0.5 V` sine wave, as `V(OUT)` crosses zero (`-20 mV` to `+20 mV`), `V(TP8)` jumps rapidly from `-0.020 V` to `+0.526 V` (`0.55 V` jump at zero crossing; `1.12 V` total deadband span across `±50 mV` output).

### 4. The silkscreen as a schematic (`docs/images/opamp-silk-top.png`, `scripts/layout.py`, `scripts/gen_pcb.py`)
- **Junction dots and hops:** Programmatic verification of all 218 `F.Cu` tracks, 8 `B.Cu` hop tracks, 36 `F.SilkS` filled circles (`r = 0.5 mm`), and 8 `F.SilkS` hop arcs (`r = 0.5 mm`) in `check_pcb_silk_copper.log` section 2 confirms that **every** 3-way (and one 4-way at `(82.10, 43.00)` on `/OUT`) wire junction has a `0.5 mm` silkscreen dot, **zero** T-junctions are missing a dot, and **every** wire crossing is one of the 8 `B.Cu` hops with a `F.SilkS` semicircle arc over the crossed wire.
- **Transistor symbols, pads, arrows, and hairlines:** Every transistor (`Q1`–`Q8`) sits inside a `4.0 mm` radius circle with a `0.55 mm` base bar, `0.45 mm` collector/emitter legs, filled emitter arrowhead (pointing out at the outer end for NPNs `Q1, Q2, Q4, Q6, Q7`; pointing in against the base bar for PNPs `Q3, Q5, Q8`), `B`, `C`, `E` lettered inside the circle next to the leads, and `0.16 mm` hairlines (`Q_W_STUB`) showing the exact copper path from each SOT-23 pad to its symbol lead.
- **Ambiguous, overlapping, or missing labels:**
  - See Finding 8: `"Q6 B"` (`TP5`) overlaps `R5`'s ground via (fixed in `fixes.patch`); `J6`'s `"-15V"` touches `D4`'s bracket (fixed in `fixes.patch`); `RV1` lacked `"50R"` (fixed in `fixes.patch`); `D3`, `D5`, `D6` lack their part numbers (`B5819W`, `1N4148W`); and the 16 `GND_STUBS` have no white silkscreen line between the component pad and the ground symbol.
  - Box titles `GAIN STAGE x30`, `OPTIONAL COMPENSATION`, and `OPTIONAL FEEDBACK` differed slightly from `HANDBOOK.md`'s table (`GAIN x30`, `COMPENSATION`, `FEEDBACK`; fixed in `fixes.patch`).
  - All grounds point down except `C4` and `C5` on the `-15 V` rail, which point up toward ground above the `-15 V` rail (note: `LED2` was moved below `-15V` in Prompt 15 so `LED2`'s ground symbol also points down).

### 5. Copper and board (`hardware/opamp.kicad_pcb`, `scripts/gen_pcb.py`, `scripts/layout.py`)
- **Hops and `B.Cu` ground plane integrity (`check_copper_and_mfg.log` section 3):** The `B.Cu` ground zone fills as **1 continuous outline with 0 isolated islands and 0 unrouted nets**. The 8 `B.Cu` hop tracks have lengths between `2.0 mm` and `6.0 mm`; the closest pair of hops is Hop 2 (`+15V` at `x = 88.5, y = 40.8..45.2`) and Hop 4 (`/IN-` at `x = 87.3, y = 40.0..46.0`), which run parallel `1.2 mm` apart with `0.65 mm` of copper ground plane between their vias (`1.44 mm` center-to-center) and solid ground return all around them.
- **`0.35 mm` tracks for `20 mA`:** In 1 oz (`35 µm`) outer copper, a `0.35 mm` track has cross-sectional area `0.01225 mm^2` (`~3.9 mΩ/mm`, IPC-2221 ampacity `> 1.2 A` for `10°C` rise); at `20–50 mA` maximum current, resistive drop and heating are negligible.
- **Clearances to M3 holes (`MH1`–`MH4`) and BNC flanges (`J1`–`J3`) (`check_copper_and_mfg.log` sections 1–2):**
  - `MH1`–`MH4` (`3.2 mm` drill at `(4, 4), (96, 4), (4, 96), (96, 96)`): nearest copper track/via edge is **`8.71 mm`** away (`MH4` to `/-15V_IN`), and nearest fiducial is **`7.62 mm`** away — huge clearance for M3 standoffs/screw heads (`3.0 mm` radius).
  - `J1, J2` (`x = 6.0, rot = 180`) and `J3` (`x = 94.3, rot = 0`): the `10 × 10 mm` body sits `1.0 mm` (`J1, J2`) and `0.7 mm` (`J3`) inside the board edge, while the threaded BNC barrel overhangs the board edge by **`18.5 mm`** (`J1, J2`) and **`18.8 mm`** (`J3`).
- **Three fiducials (`layout.py` `FIDUCIALS`):** `1.0 mm` bare `F.Cu` circles inside `2.0 mm` `F.Mask` openings at `(11.0, 7.0)`, `(89.0, 7.0)`, and `(11.0, 92.0)`, asymmetric in 3 corners so board orientation is unambiguous.
- **Custom footprints (`hardware/lib/opamp.pretty/`) and SOT-23 pinout:**
  - Verified against datasheets and `scripts/easyeda_cache.json` (`check_footprints_and_jlc.log`):
    - `Package_TO_SOT_SMD:SOT-23`: `1 = B (-0.94, -0.95)`, `2 = E (-0.94, +0.95)`, `3 = C (+0.94, 0)`, matching JSCJ `MMBT3904` (`C20526`) and onsemi `MMBT3906LT1G` (`C53444`) datasheets (`1 = BASE, 2 = EMITTER, 3 = COLLECTOR`).
    - `BNC_KYWE_RightAngle`: `1.3 mm` center drill at `(0, 0)`, four `1.4 mm` ground posts at `(±4.0, ±4.0)`, matching SAMZO `BNC-KYWE-295-W4-N` drawing (`8.0 × 8.0 mm` post square).
    - `Potentiometer_Bourns_3362P_Vertical`: `0.9 mm` drills at `(-2.54, +1.27)`, `(0, -1.27)`, `(+2.54, +1.27)`, matching Bourns `3362P` datasheet (`2.54 mm / 5.08 mm` L-pattern).
    - `SW_DIP_SPSTx02_KingTek_DSIC02_P2.54mm`: pads `2.4 × 1.5 mm` at `(±4.40, ±1.27)` (`8.80 mm` row spacing, `2.54 mm` pitch), matching KingTek `DSIC02LSGET` (`EasyEDA` has `9.00 mm` row spacing, `0.1 mm` difference per side).
    - `TerminalBlock_KF301_1x02_P5.00mm` / `1x03`: `1.4 mm` drills on `5.00 mm` pitch (`2.2 mm` pads), matching `KF301-5.0` drawing (except wire-entry silkscreen is on `-y` vs EasyEDA's `+y` — see Finding 3).
    - `TestPoint_Loop_RH-5019`: single `4.0 × 2.2 mm` SMD pad matching EasyEDA `C5199800`.

### 6. The JLCPCB package (`out/opamp/`, `scripts/parts.py`, `out/opamp/PLACEMENT_CHECKS.txt`, `docs/MANUFACTURING.md`)
- **CPL rotations & polarised parts (`check_footprints_and_jlc.log`):**
  - `SOT-23` (`C20526`, `C53444`) at `+180°`: EasyEDA pad 1 is at `(+1.00, +0.95)`, KiCad pad 1 is at `(-0.94, -0.95)`; `+180°` aligns all 3 pads within `0.06 mm`.
  - `DSIC02LSGET` (`C54949`) at `+270°`: EasyEDA draws pole 1 (`pins 1–4`, labeled `A1–B1` in the symbol SVG and `"1"` / `"ON"` in the footprint SVG) at `x = -1.27, y = ±4.50` (`ON` at `y = -2.51` near pin 4) and pole 2 (`pins 2–3`, `A2–B2`, `"2"`) at `x = +1.27, y = ±4.50`. Rotating `+270°` places EasyEDA's pads 1, 2, 3, 4 and `"ON"` mark directly on KiCad's pads 1, 2, 3, 4 and `ON` silkscreen marks (`0.10 mm` offset).
  - `SOD-123` diodes (`C81598` `D1, D2, D5, D6` and `C8598` `D3, D4`) at `+0°`: EasyEDA has cathode (`pad 1` and silkscreen cathode bar) at `-x` (`-1.73 mm` and `-1.70 mm`), matching KiCad's `D_SOD-123` (`pad 1` at `-1.65 mm`).
  - `LED_0805` (`C2297` `LED1, LED2`) at `+0°`: EasyEDA's silkscreen cathode mark is at `-x` (matching KiCad `pad 1 = cathode`), verified as `0°` on `GPiBridge`.
  - `3362P` (`C52754333` `RV1`) at `+0°`: EasyEDA pads `1, 2, 3` at `(-2.50, +1.25), (0, -1.25), (+2.50, +1.25)` match KiCad within `0.04 mm`.
  - `KF301` (`C474881`, `C474882`) at `+0°`: **Should be `+180°`** so EasyEDA's `+y` wire openings match `gen_footprints.py`'s `-y` wire openings on the board edges (see Finding 3).
- **Does the `DSIC02` switch connect pins `1–4` and `2–3` across the body?** Yes — confirmed directly from `C54949`'s EasyEDA schematic symbol SVG (`texts=['A1', '1', 'A2', '2', 'B1', '4', 'B2', '3']`) and footprint SVG.
- **Economic vs Standard PCBA & cost model:** Economic PCBA supports top-side SMT + THT assembly when all parts are placed on the Top side. As noted in Finding 12, JLCPCB only charges the `$3.00` Extended feeder loading fee on **SMT** Extended parts (`3` codes = `$9.00`, not `7` codes = `$21.00`, since the 4 THT Extended codes are wave/hand-soldered), while `LeadFree HASL` and `Remove Mark` add `~$3–$6` of PCB option fees, so the actual order total is ~$6–$9 lower than `docs/MANUFACTURING.md`'s estimate.

### 7. The documents as a lab handout (`docs/HANDBOOK.md`, `docs/DESIGN_NOTES.md`, `docs/MANUFACTURING.md`)
- **Do the exercises work as described, and do the loop voltages follow from the circuit?**
  - See Finding 5 (the loop voltage table in `HANDBOOK.md` mixes `±15.0 V` node voltages with `±14.6 V` rail voltages, breaking KVL in Exercise 1) and Finding 6 (four stale `C2 / C3` references and the `IN-` grounding/un-grounding trap in Exercises 4 and 5).
  - All other exercises (Exercises 2, 3, 6, 7, 8, 9, 10 and the Lab 6L–9L compatibility table in Section 9) were simulated and work as described (with the coax-loading caveat on Exercise 6 in Finding 1).
- **Which numbers, counts, and names does `gen_docs.py` not check?**
  See Finding 11: `gen_docs.py` checks 28 regex claims, but does not check schematic text notes (`Ib = 5 uA` vs `2 uA`, `10 mA max` vs `15 mA`, `"takes a third"` vs `"leaves a third"`), `DESIGN_NOTES.md`'s `14 MHz` and `100 degrees`, or stage box names in `HANDBOOK.md` section 1.
- **What is missing from `docs/DESIGN_NOTES.md` section 5 ("What could be wrong with a first board")?**
  1. The `KF301` screw terminal blocks (`J4`–`J7`) soldered with their wire openings facing **inward** (`JLC_ROTATION = 0` vs `180`, Finding 3).
  2. `PLACEMENT_CHECKS.txt` giving backwards preview instructions for `Q2, Q6`, `J7`, and `J3` (Finding 2).
  3. Follower oscillation (`12.8 MHz`) outside the deadband when a 1 m BNC coaxial cable (`100 pF`) is attached to `J3` (Finding 1).
  4. Burning `R8` (`0.5–0.65 W` in an `0805`) or reverse-avalanche-degrading `Q3` / `Q6` when a student clips a scope ground lead onto `TP7`, `TP6`, or `TP4` even with a `50 mA` bench supply limit (Finding 4).

### 8. What a student will do to it (`review_sims_abuse.py`, `review_sims_abuse.log`)
| Student mistake | What happens | Damages the board? | Zero-clarity-cost prevention |
|---|---|---|---|
| **Supply reversed / `+15 V` and `-15 V` swapped** | `D3, D4` (`B5819W`, `40 V`) block `15 V` reverse each; `0 mA` flows; LEDs stay off | **No** | Already prevented by `D3, D4` |
| **`+15 V` (or `-15 V`) swapped with `GND` on `J6`** | Relative to board `GND` (`J6 pin 2`), the other rail terminal is at `±30 V` forward-biasing `D3` or `D4`, putting `29.6 V` across `C2` or `C4` (`25 V` rated `0805` X5R); if a grounded BNC shield is attached to `J1`–`J3`, it shorts the misplaced supply lead to ground (caught by `50 mA` supply limit) | **`C2` or `C4` overvoltaged (`29.6 V` vs `25 V` rating)** | Use `35 V` or `50 V` `10 µF` capacitors for `C2, C4` |
| **One rail only (`+15 V` or `-15 V` open or `0 V`)** | Output rails harmlessly; max component power `< 5 mW`; max reverse `V_EB < 0.7 V` | **No** | Already safe; single lit LED diagnoses it |
| **`30 V` between one rail and `GND`** | `C2` or `C4` (`25 V` rated) sees `29.6 V`; `P(Q6) = 86 mW`, `P(R9) = 76 mW` | **`C2` or `C4` overvoltaged (`29.6 V > 25 V`)** | Use `35 V` or `50 V` `10 µF` capacitors for `C2, C4` |
| **`20 V` peak generator into one input (`±20 V`)** | In follower mode, `I <= 6 mA`, `P(R1, R2) < 40 mW`, max reverse `V_EB = 3.5 V` (`< 6 V`); if `+20 V` and `-20 V` are applied simultaneously to `IN+` and `IN-`, `P(R1) = P(R2) = 386 mW` (`1.54×` `1206` rating) | **No** for single `20 V` generator | Already protected by `R1, R2` (`1206`) and `D1, D2` |
| **Scope ground clip on `TP11` (`+15V`) or `TP12` (`-15V`)** | Shorts rail through `D3` or `D4` (`B5819W`, `1 A`) to `GND` | **Saved by `50 mA` supply limit** (without limit, a `>2 A` supply blows `D3`/`D4`) | Keep the `50 mA` (or `30 mA`) bench supply limit |
| **Scope ground clip on `TP7` (`Q3 E`) or `TP6` (`Q2 C`)** | `TP7`: `44.2 mA` in `R8` (`646 mW`, `5.2×` `0805` rating) at `46.8 mA` total rail current (**below `50 mA` limit!**) + `12.6 V` reverse `V_EB` on `Q3` (`2.5×` rating). `TP6`: `515 mW` in `R8`, `142 mW` in `R3` at `50.4 mA` total rail current | **Yes: overheats `R8` (`0.5–0.65 W` vs `0.125 W`) and reverse-avalanches `Q3` (`TP7`)** | Make `R8` `1206`/`2512` and add anti-parallel diode across `Q3 B–E` (or warn in `HANDBOOK.md` that `50 mA` does not save `R8`) |
| **Scope ground clip on `TP4` (`Q6 E`) or `TP5` (`Q6 B`)** | `R7` (`1 kΩ 0805`, `125 mW`) dissipates `213 mW` (`TP4`) or `192 mW` (`TP5`) at `18 mA` rail current; `TP4` puts `12.6 V` reverse `V_EB` on `Q6` | **Overloads `R7` (`1.7×` rating) and reverse-avalanches `Q6` (`TP4`)** | Use `1206` (`C4410`, already on BOM) for `R7` |
| **Scope ground clip on `TP13` (`Q1 E`) or `TP14` (`Q2 E`)** | In follower mode, `OUT` and `IN-` rail to `-12.8 V`, pulling `Q1 B / Q2 B` to `-6.88 V / -6.18 V` while `Q1 E / Q2 E = 0 V` (`6.88 V` reverse `V_EB`) | **Slightly exceeds `6.0 V` `V_(BR)EBO` of `Q1, Q2`** | Brief slip is current-limited by `R1, R2` |
| **`OUT` tied to `IN+` (positive feedback) or `IN-`** | Latches at `+13.4 V` or `-14.2 V` (`OUT` to `IN+`) or acts as follower (`OUT` to `IN-`); max power `< 25 mW` | **No** | Already safe |
| **`OUT` shorted to `GND`, `+15 V`, or `-15 V`** | Short to `GND`: `202 mW` in `Q4`/`Q5` (survived for minutes). Short to `±15 V`: `420 mW` in `Q4`/`Q5` (survived for a few seconds) | **Short to rail > 5 s damages `Q4` or `Q5`** | Stated on back silkscreen and `HANDBOOK.md` |
| **`100 Ω` load on `OUT`** | Current limiter clamps `I_OUT` at `±15 mA` (`V_OUT = ±1.5 V`); `P(Q4) = 172 mW`, `P(Q5) = 168 mW` (`< 200 mW` rating!) | **No** | Current limiter protects `Q4, Q5` continuously into `100 Ω` |
| **Trimmer `RV1` turned to an end** | Shifts offset by `±33 mV`; Stage 1 gain unchanged (`11.1`) in closed loop | **No** | Already safe (`RV1` wiper is on `TAIL`) |
| **DIP slider halfway** | Open contact (same as OFF for that pole) | **No** | Already safe |

---

## 4. What Was Checked and Found Right

1. **Schematic and netlist parity with Lab 5L (`check_circuit.py`, `out/opamp.net`):** All 8 transistors, 16 resistors, 1 trimmer, 5 capacitors, 6 diodes, 2 LEDs, 3 DIP switches, 7 connectors, and 18 test loops match the book's circuit and the board's documented additions. ERC passes with 0 violations.
2. **Compensation switch `SW2` rewiring:** Pole 1 (`pins 4–1`) puts `R14 (1 kΩ) + C1 (100 pF)` between `Q2 C` and `Q3 C`; pole 2 (`pins 3–2`) connects `Q2 C` directly to the `R14–C1` junction so position 2 alone (or 1+2 together) selects the bare `100 pF` capacitor.
3. **PCB copper, DRC, and ground plane (`check_pcb_silk_copper.log`, `check_copper_and_mfg.log`):** KiCad 10.0.7 DRC with `--severity-all --schematic-parity` passes with **0 violations**. All 36 `F.SilkS` junction dots and 8 `F.SilkS` hop arcs match the copper topology; the `B.Cu` ground zone fills as a single unbroken polygon (`0 islands`) with generous clearance to `MH1`–`MH4` (`>= 8.71 mm`) and proper BNC barrel overhang (`18.5–18.8 mm`).
4. **Transistor symbols and SOT-23 pad mapping:** Every transistor circle has the correct NPN (outward) or PNP (inward) emitter arrow, `B/C/E` labels, and hairline stubs matching the copper tracks to SOT-23 pads `1 = B, 2 = E, 3 = C`.
5. **EasyEDA pad alignment and LCSC codes (`check_footprints_and_jlc.log`, `check_outputs.py`):** All 22 LCSC codes have ample stock and match JLCPCB's component descriptions; `SOT-23` (`+180°`), `DSIC02` (`+270°`), `BNC` (`+90°`), `3362P` (`0°`), `SOD-123` (`0°`), `LED_0805` (`0°`), and `RH-5019` (`0°`) pad coordinates align within `< 0.15 mm` of the board's pads; `RV1` is geometrically keyed by its L-shaped hole pattern; and the `B.SilkS` QR code decodes to `https://github.com/gallicchio/op-amp-pcb`.

---

## 5. What Could Not Be Checked, and Why

1. **Visual inspection of raster PNGs (`docs/images/*.png`, `docs/history/*.png`):** The model endpoint running this session rejects raster image attachments (`<image attachment omitted from this request because the model rejected image input>`). Instead of visual raster inspection, we wrote programmatic geometric analyzers (`check_pcb_silk_copper.py`, `check_copper_and_mfg.py`, `check_footprints_and_jlc.py`) using KiCad 10.0.7's `pcbnew` Python API (`GetBoundingBox()`, `GetTracks()`, `Zones()`) and `sexp_parse.py` to verify every coordinate, bounding box overlap, line intersection, pad position, and EasyEDA SVG path mathematically to `0.01 mm`.
2. **Live JLCPCB placement preview ("Confirm Parts Placement"):** Only JLCPCB's web order preview shows their private 3D/2D rendering of the predicted parts (`C20526`, `C53444`, `C54949`, `C474881`, `C474882`, `C52754333`, `C81598`, `C8598`, `C5199800`), which must be checked against the corrected `PLACEMENT_CHECKS.txt` when ordering.
3. **Scanned vector PDFs (`DSIC02LSGET_C54949.pdf`, `KF301-5.0-2P_C474881.pdf`, `RH-5019_C5199800.pdf`):** These three PDFs contain vector outlines rather than embedded text streams (`pdftotext` outputs empty pages); we cross-checked their dimensions and polarity markings directly from EasyEDA's component SVGs in `scripts/easyeda_cache.json`.

---

## 6. Publishing Check

- **Copyrighted files properly gitignored:** `/datasheets/`, `/datasheets_not_in_git/`, `/scripts/jlc_cache.json`, and `/scripts/easyeda_cache.json` are in `.gitignore` and verified untracked via `git ls-files`.
- **Items to clean up before making the repository public:**
  1. `CLAUDE_CODE_CHAT.md` line 10 contains the prompt text referencing `~/mudd/pcbs/op-amp-pcb/datasheets_not_in_git/Tom_Hayes_Paul_Horowitz_Learning_the_Art_of_Electronics.pdf` (and `~/OpticsPCBs/CLAUDE_PCB.md`).
  2. `design_reviews/2026-10-24_Claude-Fable-5.1/build.log` and `build_patched.log` contain the local path `/home/jason/.local/bin/kicad-10.0.7-x86_64.AppImage`.
  3. Stray tracked files `docs/history/r.pdf` (193 KB), `docs/history/r.png` (536 KB), and obsolete `docs/images/opamp-top-flat.png` (99 KB) should be `git rm`'d before pushing.
  4. No API keys, tokens, or credentials exist anywhere in the repository.

---

## 7. Patches and Verification Files in This Directory

- **`fixes.patch`**: Unified diff (`diff -ru` against the repository root) implementing the generator and document fixes for Findings 2, 3, 6, 7, 8, 10, and 11 (`scripts/kienv.py`, `scripts/parts.py`, `scripts/layout.py`, `scripts/gen_docs.py`, `scripts/gen_sch.py`, `scripts/check_circuit.py`, `README.md`, `docs/HANDBOOK.md`, `docs/DESIGN_NOTES.md`). Built and verified in `project/`: **ERC 0, 108 circuit checks passed, 0 schematic text overlaps, DRC 0, all fab checks passed, 28 of 28 document claims matched (`BUILD OK`)**.
- **`review_sims.py` / `review_sims.log`**: `ngspice` operating-point comparison (`±15.0 V` ideal rails vs `±14.6 V` rails vs `B5819W` Schottky rails) and `RV1` offset-null / open-wiper / shorted-ends simulations.
- **`review_sims2.py` / `review_sims2.log`**: `ngspice` output current-limit branch-current decomposition and transistor power dissipation under shorts to `GND`, `+15 V`, and `-15 V`.
- **`review_sims3.py` / `review_sims3.log`**: `ngspice` simulations of limiter capacitance/leakage, `10x` scope probe loading (`10 pF` and `15 pF`) on `TP6` and `TP8`, `100 pF`–`10 nF` coax loading inside and outside the crossover deadband, both `FEEDBACK` sliders on, slew rate, and `TP8` crossover jump.
- **`review_sims_abuse.py` / `review_sims_abuse.log`**: `ngspice` student-abuse stress matrix (scope ground clip on every probe loop `TP1`–`TP14`, single rail, `30 V` rail, `±20 V` inputs, `OUT` tied to `IN+`, and `100 Ω` load).
- **`check_exercises.py` / `check_exercises.log`**: `ngspice` verification of `HANDBOOK.md` Exercises 2, 4, 5 (`IN-` open vs grounded in open loop, and `TP8` deadband step in follower mode) and Exercise 8 (`COMPENSATION` switch settings).
- **`check_pcb_silk_copper.py` / `check_pcb_silk_copper.log`**: KiCad 10 `pcbnew` geometric verification of transistor pads/rotations, 36 `F.SilkS` junction dots, 8 `B.Cu` hops and `F.SilkS` arcs, and `F.SilkS` text/line bounding-box overlaps.
- **`check_copper_and_mfg.py` / `check_copper_and_mfg.log`**: KiCad 10 `pcbnew` verification of M3 mounting-hole clearances, BNC edge setback/overhang, and `B.Cu` ground-plane integrity.
- **`check_footprints_and_jlc.py` / `check_footprints_and_jlc.log`**: EasyEDA land-pattern coordinate transformation check against `pcb_geom.json` and `opamp_cpl_jlcpcb_upload.csv`.

