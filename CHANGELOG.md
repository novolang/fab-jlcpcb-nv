# Changelog

All notable changes to fab-jlcpcb-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## [0.1.1] — 2026-11-25

### Added

- `fjdata.part_rotations`, a table of rotations keyed by JLCPCB part number: for a part number, the rotation to add, the offset, a status (`verified` when the preview of the order form drew the part right with the value, `proposed` when the preview drew it wrong with the family value and the entry holds the value read from the picture), the sides seen and the date. The preview draws each part from its own model, so the rotation a part needs follows its part number. The table holds 29 verified entries and four proposed ones (`C295747`, `C2895249`, `C2652978`, `C404280`), all from the dry runs of 2026-11-25.
- The lookup order for a part: its part-number entry when it has one, otherwise the family table. `fjcpl.rows_for` takes the entries and the bill; `fjcpl.rows` keeps the family table alone. `fjbom.part_of` reads the part number of a designator.
- A source for the rotation of every placed part: verified part, proposed part, part verified on the other side only, family row, rotation field, or the board's own value. `corrections.txt` has a line for every placed part with its source, and the order sheet names it for each part in the section of the rotation of every placed part.
- The order sheet has a section near the top, `Rotations not verified`, that lists the parts whose rotation no preview has shown right with the value written and says to check each in the form's preview before ordering. A board whose every rotation is verified has one line in its place.
- `host_only = true` in the manifest: the package declares itself host-only.

### Changed

- The check `rotations` warns for a proposed part entry, a part entry seen on the other side only, a family row that adds a rotation and a rotation field; a verified part entry is no longer a correction to review.
- `corrections.txt` lists every placed part, not only the parts whose rotation or position changed, and ends with the count of rows for each source.

### Fixed

- The rotation of a `SOT-23-5` footprint. The table row `^SOT-23` gave 180 degrees to the three-lead and the five-lead package alike, and JLCPCB's preview drew the five-lead parts a quarter turn off. The row `^SOT-23-5` at 270 degrees stands before `^SOT-23`, which keeps 180 for the other footprints it matches.
- The rotation of the parts that the family table drew wrong in the preview of 2026-11-25: the nRF52833 QFN-40 (`^QFN-`), the JST PH connector (`^JST_PH_S`), a VQFN-16 level shifter and an RGB LED that have no row. Each has a proposed part entry.
- The order sheet names the PCBA Type to select on the form (Economic or Standard) in its first lines and says that the form may preselect the other type. A quote taken with the type left alone was priced as Standard assembly.

### Known

- The four proposed entries are read from pictures and not yet seen right; each is named in the order sheet of a board that has the part.
- The preview has shown `SOT-23` at 180 and `SOT-23-5` at 270. It has not shown `SOT-23-5_HandSoldering`, which the row `^SOT-23-5` matches on the ground that its pads are those of `SOT-23-5`; nor `SOT-23-6`, `SOT-23-8`, `SOT-23W`, `SOT-23_Handsoldering`, `TSOT-23-5`, `TSOT-23-6` or `D_SOT-23`, whose rows are the Toolkit's.
- Three parts of the 8-layer board were not drawn in the preview (the module, the nPM1300 and the flash) and a crystal had no model; they have no entry.

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
