# Changelog

All notable changes to fab-jlcpcb-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## [0.1.1] — 2026-11-25

### Fixed

- The rotation of a `SOT-23-5` footprint. The table row `^SOT-23` gave 180 degrees to the three-lead and the five-lead package alike, and JLCPCB's preview drew the five-lead parts a quarter turn off. The row `^SOT-23-5` at 270 degrees stands before `^SOT-23`, which keeps 180 for the other footprints it matches.
- The order sheet names the PCBA Type to select on the form (Economic or Standard) in its first lines and says that the form may preselect the other type. A quote taken with the type left alone was priced as Standard assembly.

### Known

- The preview has shown `SOT-23` at 180 and `SOT-23-5` at 270. It has not shown `SOT-23-5_HandSoldering`, which the new row matches on the ground that its pads are those of `SOT-23-5`; nor `SOT-23-6`, `SOT-23-8`, `SOT-23W`, `SOT-23_Handsoldering`, `TSOT-23-5`, `TSOT-23-6` or `D_SOT-23`, whose rows are the Toolkit's.

## [0.1.0] — 2026-11-24

The package is the one published as fab-package-nv 0.1.0 on 2026-11-24, under the name that says which manufacturer it is for, with the changes that a first dry run on JLCPCB's form called for.

### Added

- `fjpack.prepare`, the JLCPCB order package of a revision that passed its gates: the Gerber and drill zip, the bill of materials, the placement file, the list of corrections, the order sheet and a manifest with hashes.
- `fjcpl`, the placement file with the rotation and position corrections of the Fabrication Toolkit, and `fjdata`, the Toolkit's rotation table and the manufacturer's limits as data with their sources.
- `fjcheck`, nineteen checks of the design against the manufacturer's published limits and against itself; `fjbom`, `fjboard`, `fjsheet` and `fjzip`.
- `fjoverlay`, the check `placement-on-gerber`: every numbered pad of every placed part, laid out from its placement row, must lie on its own flash in the copper layers, and `positions-agree` compares the rows with KiCad's own position export. A placement file that does not share the Gerbers' origin cannot be written.
- `fjcatalog`, the saved public part pages: library, assembly class, and the checks `part-pages`, `part-assembly-class` and `extended-parts`. A part that only Standard assembly places forces the order into Standard and is an error on a board that is Economic by itself.
- A part with no part number is never left to JLCPCB's matcher: it is an error and the package writes only the sheet, or it is listed under `[do_not_place]` in the policy with its reason and is in neither file.

### Fixed

- The origin of the placement file and the Gerber files: the Gerbers and the drill files are now written relative to the auxiliary axis origin (hardware-gates-nv 0.1.1), the same origin as the placement file. A first order drew every part about 12 mm off.
- A via is held to the drill and diameter limits (0.15 mm hole, 0.25 mm across, 0.1 mm over its drill); the annular ring limit is for plated pads, as the capability page states it.

### Known

- Nothing was uploaded to the manufacturer by the package or by its author. A person ran a first dry run on the form by hand on 2026-11-24 and stopped before the cart.
- The placements in the preview have not been seen after the origin fix, and no board with parts on the bottom has been through the form.
