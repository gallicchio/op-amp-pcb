# Manufacturing

One board, two layers, 100 x 100 mm, every part on the top side, a solid
ground plane on the back.  It passes ERC, DRC with schematic parity, the
91 circuit assertions and the fab-package checks with zero violations,
and `./make.py` rebuilds and rechecks everything from scratch in about a minute.

## What to upload

| file | where it goes |
|---|---|
| `out/opamp/opamp-gerbers.zip` | the *Add gerber file* box |
| `out/opamp/opamp_bom_jlcpcb_upload.csv` | the BOM box (JLCPCB's column layout) |
| **`out/opamp/opamp_cpl_jlcpcb_upload.csv`** | the CPL / pick-and-place box, at JLCPCB |
| `out/opamp/opamp_cpl_kicad_native.csv` | the CPL box at any other fab |
| `out/opamp/opamp-assembly-notes.txt` | paste into the assembly remark |

## The order form, field by field

The same list is in `out/opamp/opamp-fabrication-notes.txt` to keep open while
ordering.  The values that come from the board are computed, not typed.

| field | pick | why |
|---|---|---|
| **PCB** | | |
| Base Material | FR-4 | the default |
| Layers | 2 | what the gerber set contains |
| Dimensions | 100 x 100 mm | read from the board outline; the discounted size |
| PCB Qty | 5 | the minimum; 10 costs about three dollars more |
| Product Type | Industrial/Consumer electronics | the default |
| **PCB Specifications** | | |
| Different Design | 1 | one board in the outline |
| Delivery Format | Single PCB | no panel |
| PCB Thickness | 1.6 mm | the BNC flanges and the terminal blocks expect it |
| PCB Color | Green | any; the white silkscreen reads best on green or black |
| Silkscreen | White | the default for green |
| Material Type | FR4-Standard TG 135-140 | the default; nothing here gets warm |
| Surface Finish | LeadFree HASL | students handle this board: lead-free.  ENIG is fine too |
| **High-spec Options** | | |
| Outer Copper Weight | 1 oz | the design rules assume it |
| Via Covering | Tented | or Plugged if the form upgrades it: either is fine, no via must stay open |
| Min via hole size/diameter | 0.3 mm / (0.4 / 0.45 mm) | the smallest via on the board is 0.30 mm drill, 0.80 mm pad |
| Board Outline Tolerance | +/-0.2 mm (Regular) | nothing mates with the edge |
| Confirm Production file | No | the gerbers are checked here |
| Mark on PCB | Remove Mark | the whole front is a drawing; nowhere for an order number |
| Electrical Test | Flying Probe Fully Test | the default |
| Gold Fingers | No |  |
| Castellated Holes | No |  |
| Edge Plating | No |  |
| **PCB Assembly** | | |
| PCBA Type | Economic | all parts on one side, nothing fine-pitch |
| Assembly Side | Top | every part is on the front |
| PCBA Qty | 2, or as many as the class needs | the per-order fees are the same for 2 or 20 |
| Edge Rails/Fiducials | Added by JLCPCB | the board carries no fiducials; let them add rails with fiducials, removed before delivery |
| Confirm Parts Placement | Yes | look at the preview against PLACEMENT_CHECKS.txt before paying |
| Parts Selection | By JLCPCB | every BOM line has an LCSC code |
| Through-hole parts | keep them: J1, J2, J3, J4, J5, J6, J7, RV1 | the form lists them separately; the BNCs, terminals and trimmer are meant to be fitted |
| Bake Components | No | nothing moisture-sensitive |
| Stencil | none | JLCPCB keeps its own; nothing to order |

## Cost

The board has **97 SMT joints** and **18 through-hole joints** on
39 BOM lines; 7 distinct order codes are JLCPCB *Extended* parts
(the BNCs, the terminal blocks, the trimmer, the DIP switches, the test loops
and the PNP), each with a one-off $3.00 feeder fee.  Parts alone are
**$7.62 per board**, of which the three BNC jacks are
$3.88 and the 17 test loops $1.64.

**2 boards, fully assembled, through-hole parts included**

| line | cost |
|---|---|
| bare PCBs (5 made) | $2.00 |
| parts ($7.62 x 2) | $15.24 |
| assembly: setup $8.00 + stencil $1.50 + THT setup $3.58 + 7 extended codes + 194 SMT and 36 THT joints | $35.49 |
| shipping (DHL) | $22.00 |
| **total** | **$74.73**  ($37.37 each) |

**5 boards, fully assembled, through-hole parts included**

| line | cost |
|---|---|
| bare PCBs (5 made) | $2.00 |
| parts ($7.62 x 5) | $38.11 |
| assembly: setup $8.00 + stencil $1.50 + THT setup $3.58 + 7 extended codes + 485 SMT and 90 THT joints | $37.60 |
| shipping (DHL) | $22.00 |
| **total** | **$99.71**  ($19.94 each) |

**10 boards, fully assembled, through-hole parts included**

| line | cost |
|---|---|
| bare PCBs (10 made) | $5.00 |
| parts ($7.62 x 10) | $76.21 |
| assembly: setup $8.00 + stencil $1.50 + THT setup $3.58 + 7 extended codes + 970 SMT and 180 THT joints | $41.13 |
| shipping (DHL) | $22.00 |
| **total** | **$144.34**  ($14.43 each) |

The fixed fees dominate a small order: a second board costs about
$8.33 more than the first, so order one per bench, not one per class.

## Rotations JLCPCB needs

JLCPCB places from its own drawing of each part, and for some parts that
drawing is turned from KiCad's footprint, so a placement file that is right
everywhere else is wrong there by a fixed angle.  The upload CPL has these
angles already applied, per LCSC code, from `scripts/parts.py`:

| parts | LCSC | turned by | evidence |
|---|---|---|---|
| SW1, SW2, SW3 | C54949 | 270 deg | predicted: DSIC02LSGET: JLCPCB draws the DSIC06 lying along x, KiCad standing; the Lorenz DSIC06 needed +270 (read) |
| Q1, Q2, Q4, Q6 | C20526 | 180 deg | predicted: SOT-23: their pad 1 is at (+1.0,+0.95), KiCad's at (-0.94,-0.95); the SOT-23-5 on GPSDO needed +180 on 59 placements |
| Q3, Q5 | C53444 | 180 deg | predicted: SOT-23, same drawing as the NPN |
| J1, J2, J3 | C41416668 | 90 deg | read: BNC-KYWE-295-W4-N: Lorenz board rev A/B preview, built and working |
| LED1, LED2 | C2297 | 0 deg | read: KT-0805G on KiCad's LED_0805: GPiBridge rev A preview, cathode at pad 1 |
| J4, J5, J7 | C474881 | 0 deg | predicted: KF301-2P: pins along x at +/-2.5, as drawn here; wire entry side to be seen |
| J6 | C474882 | 0 deg | predicted: KF301-3P: pins along x at -5/0/+5, as drawn here |
| TP1, TP2, TP3, TP4, TP5, TP6, TP7, TP8, TP9, TP10, TP11, TP12, TP13, TP14, TP100, TP101, TP102 | C5199800 | 0 deg | predicted: RH-5019 test loop: one 4.0 x 2.2 pad, as drawn here; the loop lies along x |
| RV1 | C52754333 | 0 deg | predicted: 3362P: their pads 1/3 at y=+1.25 and 2 at y=-1.25, as drawn here |
| D1, D2 | C81598 | 0 deg | predicted: 1N4148W SOD-123F: as the Schottky |
| D3, D4 | C8598 | 0 deg | predicted: B5819W SOD-123: their pad 1 at -1.7 as KiCad's; cathode band end to be seen |

*read* means seen in a JLCPCB preview on a real order of that part on that
footprint; *predicted* means derived by fitting JLCPCB's own land pattern
onto ours by pin number (`scripts/easyeda.py <code>`).  Every predicted part is
in `out/opamp/PLACEMENT_CHECKS.txt`, the list to hold against the preview.
`check_outputs.py` proves the two CPL files differ in nothing but those angles.

## Check these in the preview before you pay

| part | what to look for | should be |
|---|---|---|
| Q1, Q3, Q4, Q5 | SOT-23: the lone pad (collector) on the side the collector wire leaves | lone pad at the TOP, the pair at the bottom |
| Q2, Q6 | the same, the other way up | lone pad at the BOTTOM, the pair at the top |
| SW1, SW2, SW3 | 2-way DIP switch: pads on pads; sliders move toward the '1 / 2' legends | SW1 and SW2 sliders moving toward the labelled side; electrically it cannot go in wrong |
| RV1 | 3362P trimmer, keyed | fits one way; screw on top |
| J1, J2 | BNC barrel | pointing off the LEFT edge |
| J3 | BNC barrel | pointing off the RIGHT edge |
| J4, J5 | screw terminal wire openings | facing the LEFT edge |
| J6, J7 | screw terminal wire openings | facing the RIGHT edge |
| D1, D2 | SOD-123 cathode band | at the end the silkscreen bar marks (they are anti-parallel: one up, one down) |
| D3, D4 | SOD-123 cathode band | D3 toward the +15 V rail (top); D4 toward the terminal (bottom) |
| LED1, LED2 | 0805 LED cathode mark | LED1 cathode on the RIGHT (its ground via), anode toward R12; LED2 cathode on the LEFT toward R13, anode to the ground via on its right |
| TP1-TP14, TP100-TP102 | test loops | the loop lying along the pad's long side; not polarised |

The one part that cannot go in wrong is the trimmer: its three holes form an
L, so it fits one way.  `check_outputs.py` re-derives that from the board file
on every build.  The BNCs are not keyed (four symmetric posts and a centre
pin), which is why their correction is read, not predicted, and worth a glance.

## The through-hole parts

8 parts are through-hole: **J1, J2, J3, J4, J5, J6, J7, RV1**, the three BNC
jacks, the four terminal blocks and the trimmer.  They are in the BOM and the
CPL and JLCPCB fits them for a per-order fee plus pennies a joint; keep them
selected when the form lists them.  If you would rather solder them yourself
they are the 18 largest, easiest joints on the board.  Everything else is 0805,
1206, SOD-123 or SOT-23 and is hand-workable with a fine iron.

## Parts, stock and alternates

Stock as JLCPCB's parts API reported it on 2026-10-24; the build re-reads
every code's description against the value and package here and stops if
one has changed.  JLCPCB's assembly stock is what counts and their BOM
upload shows it per line.

| ref | value | LCSC | JLC | unit | stock then | notes |
|---|---|---|---|---|---|---|
| C1 | 100pF | C1790 | basic | $0.0101 | 663,951 | C0G/NP0 50V 0805 |
| C2,C4 | 10uF | C15850 | basic | $0.0426 | 9,138,516 | X5R 25V 0805 |
| C3,C5 | 100nF | C49678 | basic | $0.0205 | 22,490,642 | X7R 50V 0805 |
| D1,D2 | 1N4148W | C81598 | basic | $0.0124 | 4,130,788 | anti-parallel pair across the two inputs: holds the differential input under 0.7 V, as a real op-amp's clamps do, so no base-emitter junction sees its 6 V reverse breakdown |
| D3,D4 | B5819W | C8598 | basic | $0.0260 | 589,077 | 1 A 40 V Schottky in series with each supply: a reversed supply does nothing instead of forward-biasing six transistors. Drops about 0.35 V at this board's 3 mA |
| J1,J2,J3 | BNC | C41416668 | extended | $1.2930 | 215 | 50 ohm BNC jack, right angle, 4 ground posts on 8x8 mm (the Lorenz board's jack: JLCPCB rotation +90 read off a real preview) |
| J4 | IN- / GND | C474881 | extended | $0.1020 | 85,251 | 2-way 5.0 mm screw terminal block, blue, wires enter from the side |
| J5 | IN+ / GND | C474881 | extended | $0.1020 | 85,251 | 2-way 5.0 mm screw terminal block, blue, wires enter from the side |
| J6 | +15 / GND / -15 | C474882 | extended | $0.1400 | 28,056 | 3-way 5.0 mm screw terminal block, blue: +15 V, GND, -15 V |
| J7 | OUT / GND | C474881 | extended | $0.1020 | 85,251 | 2-way 5.0 mm screw terminal block, blue, wires enter from the side |
| LED1,LED2 | GREEN | C2297 | basic | $0.0164 | 2,421,532 | green 0805 LED, one per rail, 1.2 mA through 10k: rails at a glance (JLCPCB rotation 0 on KiCad's LED_0805, read in GPiBridge's preview) |
| Q1,Q2,Q4,Q6 | 2N3904 | C20526 | basic | $0.0116 | 2,045,310 | 2N3904 in SOT-23 (1 = B, 2 = E, 3 = C), the NPN of Lab 4L |
| Q3,Q5 | 2N3906 | C53444 | extended | $0.0190 | 944,043 | 2N3906 in SOT-23 (1 = B, 2 = E, 3 = C), the PNP of Lab 4L; onsemi |
| R1,R2 | 1k | C4410 | basic | $0.0085 | 1,945,919 | 1206, 0.25 W: the input series resistors |
| R3 | 1.5k | C4310 | basic | $0.0028 | 1,272,825 |  |
| R4,R6,R10,R12,R13 | 10k | C17414 | basic | $0.0034 | 54,300,842 |  |
| R5 | 62k | C17783 | preferred | $0.0021 | 230,472 |  |
| R7,R11,R14 | 1k | C17513 | basic | $0.0035 | 43,103,445 |  |
| R8 | 330R | C17630 | basic | $0.0044 | 1,939,287 |  |
| R9 | 12k | C17444 | basic | $0.0028 | 694,664 |  |
| RV1 | 50R | C52754333 | extended | $0.3370 | 520 | 50 ohm single-turn cermet trimmer, top adjust: OFFSET NULL. Its two ends are the diff pair's emitter resistors (25 ohm each at centre) and its wiper is the tail; turning it unbalances the pair by up to +/-37 mV referred to the input |
| SW1 | TAIL | C54949 | extended | $0.3080 | 12,716 | 2-way SMD DIP switch, 2.54 mm pitch, raised sliders (KingTek DSIC, the same family as the Lorenz board's 6-way) |
| SW2 | COMPENSATION | C54949 | extended | $0.3080 | 12,716 | 2-way SMD DIP switch, 2.54 mm pitch, raised sliders (KingTek DSIC, the same family as the Lorenz board's 6-way) |
| SW3 | FEEDBACK | C54949 | extended | $0.3080 | 12,716 | 2-way SMD DIP switch, 2.54 mm pitch, raised sliders (KingTek DSIC, the same family as the Lorenz board's 6-way) |
| TP1 | IN- | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP2 | IN+ | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP3 | TAIL | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP4 | Q6 E | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP5 | Q6 B | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP6 | Q2 C | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP7 | Q3 E | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP8 | Q3 C | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP9 | OUT | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP10 | X | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP11 | +15V | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP12 | -15V | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP13 | Q1 E | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP14 | Q2 E | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |
| TP100,TP101,TP102 | GND | C5199800 | extended | $0.0966 | 101,462 | SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): a scope probe's hook or a mini-grabber clips onto it |

### If something is out of stock

**MMBT3904** (C20526)
  - MMBT3904-1AM / C364310 (Preferred, 104k)
  - any MMBT3904 in SOT-23 with the B-E-C pinout

**MMBT3906LT1G** (C53444)
  - MMBT3906 / C727128 (335k, cheaper, no-name)
  - MMBT3906 2A / C2143 (110k)

**3362P-1-500** (C52754333)
  - 3362P-1-101 / C52754331 (100 ohm, 1168 in stock): same footprint, twice the null range, stage-1 gain 9 instead of 11

**DSIC02LSGET** (C54949)
  - DSIC02LSGET / C5144999 (gull wing, 1235)
  - DSIC02LSGET / C3293152 (713)

**BNC-KYWE-295-W4-N** (C41416668)
  - HL2-BNC-KYWE / C48606310 (107 in stock)
  - MLD-BNC-KYWE-L29.5 / C52766468 (12 in stock)

**RH-5019** (C5199800)
  - RH-5015 / C5199798 (276k): the smaller 2.7 x 1.0 mm loop, same idea

**B5819W SL** (C8598)
  - B5819W / C64885 (Preferred, 751k)

The thinnest line is the BNC-KYWE-295-W4-N: 215 in stock and 3 per
board, about 71 boards' worth; next the 3362P-1-500 at about 520.
The BNC alternates share the 'BNC-KYWE' body (10 x 10 mm flange, four posts on
8 x 8 mm, centre pin), so the footprint takes any of them.

## After the boards arrive

The bring-up order, the expected voltage at every loop and the student
exercises are in [HANDBOOK.md](HANDBOOK.md).  In one line: power it from a
current-limited supply at 30 mA, both green LEDs light, and as a follower
(FEEDBACK 2 on) with IN+ grounded OUT sits within a few tens of millivolts
of zero and the trimmer nulls it.

