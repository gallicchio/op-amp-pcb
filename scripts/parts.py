"""Single source of truth for every part: value, footprint, LCSC code, notes.

The schematic, the BOM, the CPL, the cost estimate and the silkscreen legends
are all generated from this table, so there is exactly one place to change a
part.  Stock figures are what JLCPCB's parts API returned on the date given;
`scripts/jlc_api.py <code>` re-queries them, and the release refuses to build
when a code's description no longer matches the value and package here.
"""

REV = "A"
BOARD_DATE = "2026-10-24"
BOARD_NAME = "LAoE Discrete Op-Amp"
PROJECT_URL = "github.com/gallicchio/op-amp-pcb"   # the git remote of this checkout
STOCK_DATE = "2026-10-24"

# lcsc       : JLCPCB / LCSC order code
# jlc_type   : "basic" | "preferred" | "extended"  (Extended = per-part setup fee)
# process    : "SMT" | "THT"
# stock      : stock seen at JLCPCB on STOCK_DATE
# alt        : drop-in alternates, checked to share the footprint
PARTS = {
    # ---- the transistors of Chapter 4: 2N3904 / 2N3906 in SOT-23 -----------
    "NPN": dict(
        value="MMBT3904", mpn="MMBT3904", lcsc="C20526", jlc_type="basic",
        process="SMT", stock=2045310, price=0.0116,
        footprint="Package_TO_SOT_SMD:SOT-23",
        symbol="Transistor_BJT:MMBT3904",
        desc="2N3904 in SOT-23 (1 = B, 2 = E, 3 = C), the NPN of Lab 4L",
        alt=["MMBT3904-1AM / C364310 (Preferred, 104k)",
             "any MMBT3904 in SOT-23 with the B-E-C pinout"]),
    "PNP": dict(
        value="MMBT3906", mpn="MMBT3906LT1G", lcsc="C53444", jlc_type="extended",
        process="SMT", stock=944043, price=0.019,
        footprint="Package_TO_SOT_SMD:SOT-23",
        symbol="Transistor_BJT:MMBT3906",
        desc="2N3906 in SOT-23 (1 = B, 2 = E, 3 = C), the PNP of Lab 4L; onsemi",
        alt=["MMBT3906 / C727128 (335k, cheaper, no-name)",
             "MMBT3906 2A / C2143 (110k)"]),
    # ---- passives: 0805 so a student can probe and rework them -------------
    "R_0805": dict(footprint="Resistor_SMD:R_0805_2012Metric", process="SMT",
                   symbol="Device:R_US"),
    "C_0805": dict(footprint="Capacitor_SMD:C_0805_2012Metric", process="SMT",
                   symbol="Device:C"),
    # the two input resistors are 1206: a rail shorted to an input puts 0.2 W in them
    "R_1206": dict(footprint="Resistor_SMD:R_1206_3216Metric", process="SMT",
                   symbol="Device:R_US"),
    # ---- the offset-null trimmer between the two emitters -------------------
    "POT": dict(
        value="50R", mpn="3362P-1-500", lcsc="C52754333", jlc_type="extended",
        process="THT", stock=520, price=0.337,
        footprint="opamp:Potentiometer_Bourns_3362P_Vertical",
        symbol="Device:R_Potentiometer_Trim_US",
        desc="50 ohm single-turn cermet trimmer, top adjust: OFFSET NULL. Its two "
             "ends are the diff pair's emitter resistors (25 ohm each at centre) "
             "and its wiper is the tail; turning it unbalances the pair by up to "
             "+/-37 mV referred to the input",
        alt=["3362P-1-101 / C52754331 (100 ohm, 1168 in stock): same footprint, "
             "twice the null range, stage-1 gain 9 instead of 11"]),
    # ---- the three selectors: 2-way DIP switches, so nothing ships loose ----
    "DIP2": dict(
        value="SW_DIP_x02", mpn="DSIC02LSGET", lcsc="C54949", jlc_type="extended",
        process="SMT", stock=12716, price=0.308,
        footprint="opamp:SW_DIP_SPSTx02_KingTek_DSIC02_P2.54mm",
        symbol="Switch:SW_DIP_x02",
        desc="2-way SMD DIP switch, 2.54 mm pitch, raised sliders (KingTek DSIC, "
             "the same family as the Lorenz board's 6-way)",
        alt=["DSIC02LSGET / C5144999 (gull wing, 1235)",
             "DSIC02LSGET / C3293152 (713)"]),
    # ---- connectors ----------------------------------------------------------
    "BNC": dict(
        value="BNC", mpn="BNC-KYWE-295-W4-N", lcsc="C41416668", jlc_type="extended",
        process="THT", stock=215, price=1.293,
        footprint="opamp:BNC_KYWE_RightAngle",
        symbol="Connector:Conn_Coaxial",
        desc="50 ohm BNC jack, right angle, 4 ground posts on 8x8 mm (the Lorenz "
             "board's jack: JLCPCB rotation +90 read off a real preview)",
        alt=["HL2-BNC-KYWE / C48606310 (107 in stock)",
             "MLD-BNC-KYWE-L29.5 / C52766468 (12 in stock)"]),
    "TERM2": dict(
        value="Screw_Terminal_01x02", mpn="KF301-5.0-2P", lcsc="C474881",
        jlc_type="extended", process="THT", stock=85251, price=0.102,
        footprint="opamp:TerminalBlock_KF301_1x02_P5.00mm",
        symbol="Connector:Screw_Terminal_01x02",
        desc="2-way 5.0 mm screw terminal block, blue, wires enter from the side"),
    "TERM3": dict(
        value="Screw_Terminal_01x03", mpn="KF301-5.0-3P", lcsc="C474882",
        jlc_type="extended", process="THT", stock=28056, price=0.140,
        footprint="opamp:TerminalBlock_KF301_1x03_P5.00mm",
        symbol="Connector:Screw_Terminal_01x03",
        desc="3-way 5.0 mm screw terminal block, blue: +15 V, GND, -15 V"),
    # ---- probe pins: a 2.54 mm pin a scope hook grabs ------------------------
    "TP": dict(
        value="", mpn="RH-5019", lcsc="C5199800", jlc_type="extended",
        process="SMT", stock=101462, price=0.0966,
        footprint="opamp:TestPoint_Loop_RH-5019",
        symbol="Connector:TestPoint",
        desc="SMT test loop, 3.8 x 2.0 mm wire loop on one pad (Keystone 5019 style): "
             "a scope probe's hook or a mini-grabber clips onto it",
        alt=["RH-5015 / C5199798 (276k): the smaller 2.7 x 1.0 mm loop, same idea"]),
    # ---- power entry ---------------------------------------------------------
    "DSCH": dict(
        value="B5819W", mpn="B5819W SL", lcsc="C8598", jlc_type="basic",
        process="SMT", stock=589077, price=0.026,
        footprint="Diode_SMD:D_SOD-123", symbol="Device:D_Schottky",
        desc="1 A 40 V Schottky in series with each supply: a reversed supply "
             "does nothing instead of forward-biasing six transistors. "
             "Drops about 0.35 V at this board's 3 mA",
        alt=["B5819W / C64885 (Preferred, 751k)"]),
    "DSW": dict(
        value="1N4148W", mpn="1N4148W", lcsc="C81598", jlc_type="basic",
        process="SMT", stock=4130788, price=0.0124,
        footprint="Diode_SMD:D_SOD-123", symbol="Device:D",
        desc="anti-parallel pair across the two inputs: holds the differential "
             "input under 0.7 V, as a real op-amp's clamps do, so no base-emitter "
             "junction sees its 6 V reverse breakdown"),
    "LED": dict(
        value="GREEN", mpn="KT-0805G", lcsc="C2297", jlc_type="basic",
        process="SMT", stock=2421532, price=0.0164,
        footprint="LED_SMD:LED_0805_2012Metric", symbol="Device:LED",
        desc="green 0805 LED, one per rail, 1.2 mA through 10k: rails at a glance "
             "(JLCPCB rotation 0 on KiCad's LED_0805, read in GPiBridge's preview)"),
    # ---- nothing to buy -----------------------------------------------------
    "MH": dict(value="", process="THT", in_bom=False,
               footprint="MountingHole:MountingHole_3.2mm_M3",
               symbol="Mechanical:MountingHole",
               desc="M3 mounting hole, one per corner"),
}

# Resistor and capacitor order codes, keyed by the value printed on the sheet.
PASSIVES = {
    "1k":    dict(lcsc="C17513", mpn="0805W8F1001T5E", jlc_type="basic",
                  price=0.0035, stock=43103445),
    "1k_1206": dict(lcsc="C4410", mpn="1206W4F1001T5E", jlc_type="basic",
                    price=0.0085, stock=1945919, note="1206, 0.25 W: the input series resistors"),
    "1.5k":  dict(lcsc="C4310", mpn="0805W8F1501T5E", jlc_type="basic",
                  price=0.0028, stock=1272825),
    "330R":  dict(lcsc="C17630", mpn="0805W8F3300T5E", jlc_type="basic",
                  price=0.0044, stock=1939287),
    "10k":   dict(lcsc="C17414", mpn="0805W8F1002T5E", jlc_type="basic",
                  price=0.0034, stock=54300842),
    "12k":   dict(lcsc="C17444", mpn="0805W8F1202T5E", jlc_type="basic",
                  price=0.0028, stock=694664),
    "62k":   dict(lcsc="C17783", mpn="0805W8F6202T5E", jlc_type="preferred",
                  price=0.0021, stock=230472),
    "100pF": dict(lcsc="C1790", mpn="CL21C101JBANNNC", jlc_type="basic",
                  price=0.0101, stock=663951, note="C0G/NP0 50V 0805"),
    "100nF": dict(lcsc="C49678", mpn="CC0805KRX7R9BB104", jlc_type="basic",
                  price=0.0205, stock=22490642, note="X7R 50V 0805"),
    "10uF":  dict(lcsc="C15850", mpn="CL21A106KAYNNNE", jlc_type="basic",
                  price=0.0426, stock=9138516, note="X5R 25V 0805"),
}

# --------------------------------------------------------- JLCPCB rotations
# JLCPCB places from its own drawing of each part, and for some parts that
# drawing is turned from KiCad's footprint.  Degrees counter-clockwise to ADD
# to the KiCad rotation, written into the *_cpl_jlcpcb_upload.csv.
# "read": seen in a JLCPCB "Confirm Parts Placement" preview on a real order.
# "predicted": from fitting their land pattern on ours by pin number
# (scripts/easyeda.py); listed in PLACEMENT_CHECKS.txt for the order day.
JLC_ROTATION = {
    "C41416668": (90, "read", "BNC-KYWE-295-W4-N: Lorenz board rev A/B preview, built and working"),
    "C20526": (180, "predicted", "SOT-23: their pad 1 is at (+1.0,+0.95), KiCad's at (-0.94,-0.95); "
                                 "the SOT-23-5 on GPSDO needed +180 on 59 placements"),
    "C53444": (180, "predicted", "SOT-23, same drawing as the NPN"),
    "C54949": (270, "predicted", "DSIC02LSGET: JLCPCB draws the DSIC06 lying along x, KiCad standing; "
                                 "the Lorenz DSIC06 needed +270 (read)"),
    "C2297": (0, "read", "KT-0805G on KiCad's LED_0805: GPiBridge rev A preview, cathode at pad 1"),
    "C8598": (0, "predicted", "B5819W SOD-123: their pad 1 at -1.7 as KiCad's; cathode band end to be seen"),
    "C81598": (0, "predicted", "1N4148W SOD-123F: as the Schottky"),
    "C52754333": (0, "predicted", "3362P: their pads 1/3 at y=+1.25 and 2 at y=-1.25, as drawn here"),
    "C474881": (0, "predicted", "KF301-2P: pins along x at +/-2.5, as drawn here; wire entry side to be seen"),
    "C474882": (0, "predicted", "KF301-3P: pins along x at -5/0/+5, as drawn here"),
    "C5199800": (0, "predicted", "RH-5019 test loop: one 4.0 x 2.2 pad, as drawn here; the loop lies along x"),
}
