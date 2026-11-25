# fab-jlcpcb-nv

A board that passed its checks is turned into the files JLCPCB asks for when a board is ordered with assembly: the Gerber and drill zip, the bill of materials in JLCPCB's columns, and the placement file (CPL) with the rotation corrections the assembly machines need. The package also writes an order sheet that a person reads before ordering, and runs nineteen checks of the design against the manufacturer's published limits, against the part pages the manufacturer publishes, and against itself. One of them lays every placed part over the Gerber copper, so a placement file that does not share the Gerbers' origin cannot be written.

The package places no order and calls no service. It reads the revision directory that `hardware-gates-nv` wrote, and it refuses a revision whose gates did not pass or whose files changed after the gates ran.

## Install

```
novo pkg add fab-jlcpcb-nv
```

The package depends on `hardware-gates-nv` 0.1.1 or later, `kicad-pcb-nv`, `sexpr-nv` and `stl-nv`. It does not start KiCad itself; the revision it reads was made by `hardware-gates-nv`, which does.

## Example

```novo
use std.env
use hgcli
use hgrun
use fjpack
use fjcheck

fn main() [io, fs]
    let args = env.args()            // the project root, the revision, the design's name, the quantity
    match hgcli.locate()
        Err(e) => println(e.message())
        Ok(k)  =>
            match hgrun.run(args[1], args[2], k)
                Err(e) => println(e.message())
                Ok(_)  =>
                    match fjpack.prepare(args[1], args[2], args[3], str.to_int(args[4]) ?? 0)
                        Err(e) => println(e.message())
                        Ok(p)  =>
                            println("${p.dir}: ready=${p.ready}, class ${p.class}, ${list.len(p.rows)} placed")
                            for line in fjcheck.report(p.checks)
                                println(line)
```

On `tests/fixtures/ok`, a board of three resistors, one on the bottom, with two mounting holes, this writes `hardware/fab/rev-A/jlcpcb/` and prints a line for each check. Seventeen hold and start with `ok`; two do not, and both are warnings: the board is below the minimum of the Standard class, and the three part numbers have no saved part page:

```
warning  assembly-class  Standard assembly takes a single board of 70 by 70 mm at the least, the board is 30 by 20: it needs a panel, which this package does not make
warning  part-pages  3 of 3 part number(s) have no saved part page in hardware/parts, so their library and assembly class are unknown: C25804, C21190, C23162
```

## Never left to the matcher

JLCPCB's form fills a part that has no number from its comment and its footprint text. On 2026-11-24 it gave a 1N5819 diode a number out of the text `1N5819`, a USB-C connector one out of the footprint name, and an RF module one that only the Standard class places. A part the form matched on its own is not what the designer chose, so the package never leaves a part to it: a placed part with no part number is an error, and the package then writes **only** `order-sheet.md` and the manifest, with a line at the top that says REFUSED, and no zip, bill or placement file. A part is either numbered (the symbol field `LCSC`, or the field the policy names) or listed with its reason in `hardware/gates.toml`:

```toml
[do_not_place]
U1 = "the module is soldered by hand"
```

A listed part is in neither the bill nor the placement file and is named, with its reason, in the sheet. A part with the KiCad attribute `dnp` or `exclude_from_pos_files` is left out too. The default is to refuse.

## The part pages

The package calls no service. A person saves the public page of each part number once, `https://jlcpcb.com/partdetail/<number>`, as `hardware/parts/<number>.html`:

```
mkdir -p hardware/parts
for n in $(awk -F, 'NR > 1 { print $NF }' hardware/fab/rev-A/jlcpcb/bom.csv | sort -u); do
  curl -sS -A 'Mozilla/5.0' -o "hardware/parts/$n.html" "https://jlcpcb.com/partdetail/$n"
done
```

`fjcatalog` reads the library of each part (Basic, Extended or Preferred), the assembly class that places it (`Economic and Standard` or `Standard Only`), the manufacturer part number and the package. A part that only Standard assembly places forces the order into Standard, and on a board that the board alone would make Economic that is an error: the form says "Due to limits in package and other certain conditions, this part is only available for Standard PCBA service", charges a setup fee of $25 for each assembly side, and enlarges the board to at least 70 by 70 mm with edge rails. The stock is not on the page and is not read; the form shows it, with the quantity it will order, which is its own minimum and attrition and not the count times the boards.

## One origin

The Gerber files, the drill files and the position file that `hardware-gates-nv` writes are all relative to the board's auxiliary axis origin, as the Fabrication Toolkit writes them, and the placement file is too: X from the origin, Y the origin's Y minus the board's Y. A first order on 2026-11-24 had the Gerbers at the page origin and the placement file at the auxiliary origin, and the preview drew every part about 12 mm off. The check `placement-on-gerber` reads the copper layers, where KiCad writes the pad of every flash (`%TO.P,<reference>,<pad number>*%`), computes where each pad of each placed part lies from the placement row with its offsets taken off, and fails when a pad's flash is more than 0.01 mm away. Pad 1 is among the pads, so a part turned or mirrored in the row is found. `positions-agree` compares the same rows with KiCad's own position export.

## What is written

`hardware/fab/<rev>/jlcpcb/`:

| File | Content |
| --- | --- |
| `<name>-<rev>-gerbers.zip` | every file of `gerber/`, stored without compression, with a fixed date, so that the same revision gives the same bytes |
| `bom.csv` | `Comment,Designator,Footprint,JLCPCB Part #`, one line for each group of parts, the part number taken from the symbol field the policy names (default `LCSC`) |
| `cpl.csv` | `Designator,Mid X,Mid Y,Rotation,Layer`, in millimetres, the board's auxiliary origin as zero, y upward |
| `corrections.txt` | every part whose rotation or position is not the board's own, with the rule that changed it |
| `order-sheet.md` | the PCBA Type to select on the form, the size, layers, assembly class and quantity, what to choose on the web form, the corrections, the checks and the open questions |
| `package-manifest.json` | the files above with their SHA-256 |

A package whose checks hold an error is written all the same, so that the person can read what is wrong, and `Package.ready` is false.

## Placement file

The rows follow the Fabrication Toolkit (https://github.com/bennymeg/Fabrication-Toolkit, Apache-2.0), the maintained public KiCad plugin for this order. A part is placed at the centre of its pads, not at its anchor, with the board's auxiliary origin subtracted and y flipped. A part on the bottom has its rotation taken from 180. The rotation table of the Toolkit, `plugins/transformations.csv` at commit `7f627b6be76081b962161b9eb9fe3a326a18c915`, is carried in `fjdata` row for row, with one row added, `^SOT-23-5` at 270 degrees, before `^SOT-23`; the first row whose pattern matches a footprint's name adds its rotation and moves the part by its offset, turned with the part. A footprint field `FT Rotation Offset` or `FT Position Offset` adds to that, and `FT Origin = Anchor` places the part at its anchor. Every part that changes is listed in `corrections.txt` and the order sheet, so that a person checks it in JLCPCB's preview.

The row `^SOT-23-5` is there because the Toolkit's 180 degrees for `^SOT-23` draws a five-lead part a quarter turn off in JLCPCB's preview. On 2026-11-25 the preview showed `SOT-23` parts (AO3407A, three leads) right at 180 and `SOT-23-5` parts (AP2112K-3.3, TP4054) a quarter turn off at the 90 degrees that the 180 of the row `^SOT-23` gave, and 180 is right; the addition to KiCad's rotation is therefore 270. The other footprints that `^SOT-23` matches keep 180, as does `^TSOT-23`; see "What is not verified".

The one row of the table with a negative look-ahead, `^SOP-(?!18_)`, is written as two rows, `^SOP-18_` and `^SOP-`, which give the same answer.

## The checks

| Check | Severity | What it measures |
| --- | --- | --- |
| designators-unique | error | no designator twice on the board or in the bill |
| part-numbers | error | every placed part has a part number; a part marked do-not-populate or left out of the position file is not placed on purpose |
| part-number-format | error | a part number is `C` and digits |
| bom-cpl-agree | error | the bill and the placement file name the same parts |
| footprints-agree | warning | the bill's footprint is the board's |
| positions-agree | error | KiCad's own position file gives the anchors the placement file starts from |
| assembly-class | warning | Economic or Standard assembly, and the sizes and quantities of that class |
| board-size, layers, thickness | error | within the manufacturer's range |
| track-width | error | the narrowest track against the least for the layer count |
| clearance-setting | warning | the project's rule minimums against the manufacturer's least |
| drill | error | via, plated and non-plated drills, a via's diameter over its drill and not below 0.25 mm |
| annular-ring | error | the smallest ring of a plated pad (a via is held to the drill check) |
| rotations | warning | how many parts have a correction to review |
| placement-on-gerber | error | every numbered pad of every placed part, laid out from its row, lies on its own flash in the copper layers |
| part-pages | warning | every part number has a saved part page |
| part-assembly-class | error | no part number is Standard only on a board that is Economic by itself |
| extended-parts | warning | how many part numbers are Extended parts |

## Read from JLCPCB's pages

The figures were read on 23 November 2026 and are a statement of what the pages said that day.

- The columns of the bill, from the manufacturer's sample file `Sample-BOM_JLCSMT.xlsx`: `Comment`, `Designator`, `Footprint`, `JLCPCB Part #`. The sample carries `(optional)` after the last.
- The columns of the placement file, from https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly: `Designator`, `Mid X`, `Mid Y`, `Rotation`, `Layer`.
- The limits, from https://jlcpcb.com/capabilities/pcb-capabilities and https://jlcpcb.com/capabilities/pcb-assembly-capabilities, for a 1 oz board: tracks and gaps 0.10 mm on two layers and 0.09 mm on more, drills from 0.15 mm, plated-pad annular ring 0.18 mm (0.25 mm recommended) on two layers and 0.15 mm (0.20 mm recommended) on more, a via of at least 0.25 mm over a hole of 0.15 mm, a non-plated hole from 0.5 mm, thickness 0.4 to 4.5 mm, up to 32 layers, the largest board by layer count. Economic assembly: one side, 2 to 6 layers, 0.8 to 1.6 mm, 10 by 10 to 470 by 500 mm, 2 to 50 pieces. Standard assembly: both sides, 70 by 70 to 460 by 500 mm, 2 to 80000 pieces.
- The steps of the order, from https://jlcpcb.com/help/article/how-do-i-place-a-pcba-order.
- The library and the assembly class of a part number, from its public part page, as the person saved it.

## Seen on the form

On 2026-11-24 a person put a package of 0.1.0's predecessor through the form by hand and stopped before the cart. Seen: the bill and the placement file were accepted with the headers as written (15 parts detected, 10 confirmed); the form took the part numbers written in the bill; every part it filled on its own came from the comment or the footprint text; the Gerbers were taken as they were; and the preview drew every part about 12 mm too low, the cause being the origins described above. Not yet seen after the fix: a board with parts on the bottom.

On 2026-11-25 a second run showed every placed part on its footprint, the three-lead `SOT-23` parts and the diodes and resistors in the right orientation, and the `SOT-23-5` parts a quarter turn off (fixed in 0.1.1 by the row `^SOT-23-5`). The quote came out as Standard assembly because the PCBA Type was left on the form's own choice; the order sheet names the type to select, and the quote page shows the type that was taken.

## What is not verified

- The rotations of the parts that the preview has not shown. Seen right: `SOT-23` at 180 and `SOT-23-5` at 270 added to KiCad's rotation, and the resistor, LED and diode rows of the board of 2026-11-25. Not seen: `SOT-23-5_HandSoldering`, which `^SOT-23-5` matches and so turns 270 on the ground that its pads are those of `SOT-23-5`; and `SOT-23-6`, `SOT-23-8`, `SOT-23W`, `SOT-23_Handsoldering`, `TSOT-23-5` and the other `TSOT-23` footprints, and `D_SOT-23`, which keep the Toolkit's 180. A part the table does not list can still face the wrong way; the preview is the check.
- Whether JLCPCB takes the plated and non-plated holes in one drill file, as the gates' export produces, was not read on a JLCPCB page; the form took the Gerbers and the drill files of the first dry run without a remark.
- Stock, price and the size of the extended-part fee are not looked up.
- Copper weight, surface finish and solder mask colour are not in a board file and are left to the form.
- A board below the minimum size of its assembly class needs a panel; the package says so and does not make one.

## Tests

```bash
novo test tests/fj_zip_tests.nv        # CRC-32 and the stored archive, read back by unzip when it is installed
novo test tests/fj_data_tests.nv       # the tables and their figures
novo test tests/fj_board_tests.nv      # the facts read from a board
novo test tests/fj_cpl_tests.nv        # the placement file and its corrections
novo test tests/fj_bom_tests.nv        # the bill read and written
novo test tests/fj_check_tests.nv      # every check, passing and failing
novo test tests/fj_sheet_tests.nv      # the order sheet and its questions
novo test tests/fj_overlay_tests.nv    # the placement laid over the Gerber copper, on recorded Gerbers and on written ones
novo test tests/fj_catalog_tests.nv    # the saved part pages and the checks over them
novo test tests/fj_pack_tests.nv       # recorded revisions made into packages, and every refusal
novo test tests/fj_fault_tests.nv      # messages and codes
bash tests/coverage.sh                 # line coverage over src/, merged across the suites
```

`tests/fixtures/rev_ok` and `tests/fixtures/rev_aux` are the output of the gates, run once with KiCad 10.0.8 (the second on a board whose auxiliary origin is not the page origin), so no test needs KiCad. Each test makes its own directory with `mktemp`.

## Licence

Apache-2.0. See `LICENSE`. The rotation table is the Fabrication Toolkit's, Apache-2.0.
