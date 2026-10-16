# Draft: built-in PivotTable fills on XLSX import

**Compile-only research prototype. Keep PR#14 DRAFT/UNMERGED.** No runtime import, CppunitTest,
Office/Excel comparison, screenshot or round trip has been performed. This is not complete pivot
styling: in particular, Dark backgrounds without the corresponding font colors can be unreadable.

The original prototype covered35solid-band Light/Medium presets. The16.10run7 design now inventories
**all84 built-in presets** (Light1–28, Medium1–28, Dark1–28), all28 style-element slots and
**406 solid theme/tint fills**. The flat-layout C++ prototype consumes base/band/header/total fills;
complex page/subtotal/subheading slots remain data/design only, never guessed from cell text.

## Sources and reproducible data

Upstream26.8 imports/stores/exports `pivotTableStyleInfo`, but does not consume stripe flags in
the output path. Ordinary database table styles are a separate implementation:

- [import](https://github.com/LibreOffice/core/blob/e155df48174bf3e64426fb1b912b9c15fa375704/sc/source/filter/oox/pivottablefragment.cxx),
  [model](https://github.com/LibreOffice/core/blob/e155df48174bf3e64426fb1b912b9c15fa375704/sc/inc/dpobject.hxx),
  [export](https://github.com/LibreOffice/core/blob/e155df48174bf3e64426fb1b912b9c15fa375704/sc/source/filter/excel/xepivotxml.cxx),
  [output geometry](https://github.com/LibreOffice/core/blob/e155df48174bf3e64426fb1b912b9c15fa375704/sc/source/core/data/dpoutput.cxx).
- [ECMA-376 Part1](https://ecma-international.org/publications-and-standards/standards/ecma-376/),
  `OfficeOpenXML-SpreadsheetMLStyles.zip/presetTableStyles.xml` inside the Part1 download;
  source XML SHA256 `74c6cf73d551bb2bd33a51690d4922095260b6647b2a38fcbc0d6da6c6275d7e`.
- [TableStyleElement / pivot precedence](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.tablestyleelement?view=openxml-3.0.1)
  and [pivot-region meanings](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/5c1d12a9-01db-4471-897a-e2d2875980c5).
- [Office's applicable pivot elements](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oi29500/af86bfea-020b-45aa-8faa-4ad272fe6617)
  and [style flags](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.pivottablestyle?view=openxml-3.0.1).

`sc/workben/generate_pivot_stripe_fills.py INPUT sc/source/filter/inc/pivotstripefills.hxx
esilk/repro/pivot-banding/preset-fill-inventory.md` produces both the full numeric C++ data and a
[review matrix](preset-fill-inventory.md). No standard prose, user document or government text is
copied. The extractor requires all84names, unit stripe widths, unique/known regions, valid dxf
indices and solid theme colors with finite tint in−1..1. It rejects unsupported input rather than
silently substituting another style. Equally numbered TableStyle and PivotStyle are not interchangeable.

Absence of a fill is represented by theme−1: **inherit the previous layer**, not white, transparent
or a fill inferred from the dxf's font/border. Dark1–7 have row stripe fills but no corresponding
column stripe fills; they must not use the old equal-axis shortcut. All84presets have no explicit
`lastColumn` fill: no grand-total-column color is fabricated from `totalRow` or subtotal styles.

## Flat-layout prototype and layering

The importer looks up the exact built-in name, gets the actual TABLE and RESULT rectangles after
creating the pivot, and requires TABLE to equal the imported location. RESULT must share its end
and start exactly one row/column later, matching both imported offsets. It accepts one row field,
one column field and one measure, with no page fields or explicit pivot formats. Rebuilt/moved
geometry, unknown/custom presets and wider/deeper header layouts skip the entire style operation.

The fill-only layers are applied in this order:

1. `wholeTable` covers the validated table, including labels/headers/totals.
2. Enabled first/second column stripes cover the data body, excluding grand totals.
3. Enabled first/second row stripes cover that same body; a specified row fill takes precedence
   at a crossing. A missing row fill inherits any column/base fill.
4. `firstColumn` covers the flat row-label area when row-header styling is enabled.
5. `headerRow` covers the single header row when column-header styling is enabled;
   `firstHeaderCell` then covers its intersection with the row-label area when both flags are on.
6. An existing grand-total column receives `lastColumn` only with the stored last-column flag
   (currently no built-in supplies a fill). An existing grand-total row receives `totalRow` last,
   including its bottom-right intersection. Totals are independent of the stripe toggles.

This follows the relevant pivot-element precedence in the primary references; the flat region/flag
mapping is a **prototype hypothesis requiring later Excel comparison**. The body stripe scope is
deliberately narrower than all possible label/subheading applications. Only `ATTR_BACKGROUND` is
applied, with theme/tint preserved as a complex color; number formats, borders and font items are
not supplied by this patch. Header flags off do not erase a base fill. No stripes does not mean
no table style: base/header/total layers still apply where defined.

## Full-region design beyond this prototype

The generated header retains page labels/values, three subtotal levels in each axis, three
subheading levels in each axis and blank-row fill data. Implementing these needs semantic regions
from `ScDPOutput`/result-member flags, with item hierarchy and total intersection identity, rather
than inferring regions from display strings or reusing ordinary table styles. Apply those layers
between headers and grand totals in the standard's pivot order. The three ordinary-table-only
corner elements are retained as data slots but ignored for pivots.

Before enabling those regions, resolve grouped/compact/outline/multiple-measure layouts, inserted
blank rows, collapsed members, custom/explicit-format precedence and differential font/border
merging. Refresh and XLSX/ODS persistence require a proper persistent pivot style/output model;
this first-import cell formatting does not implement them. In particular, **full Dark fidelity
requires its light font colors** and cannot be inferred from successful compilation.

## Hand-made reproducers and fast checks

`make_reproducers.py` creates **95 deterministic XLSX files from raw XML**. Content is only groups
A–D, quartersQ1–Q4 and integers10–43, with fixed ZIP metadata and no author/private data/external
relationships. Each of84built-in presets has its own both-axis fixture in `presets/`. The original
seven specimens remain, plus header-disabled, no-grand-totals, unknown-custom-style and changed-offset
controls. `dark-control.xlsx` is now a supported Dark1 probe; `disabled-control` disables only bands,
and `both-axes-control` now exercises layering rather than an intentional skip.

Hand-computed values: bodyC4:F7 totals424; row totals46/86/126/166; column totals100/104/108/112.
The normal table isB3:G8, headerrow3, labelsB, grand totalsG/8; the no-totals table isB3:F7.
The deliberately changed firstDataRow=2 control must skip painting even though its cached table
has the original geometry. The custom-style control must skip the built-in approximation.

Representative deferred expected **fill-only** observations (theme indices, before fonts/borders):

| Specimen | Body | Header/total | Important distinction |
|---|---|---|---|
| Light16 rows | rows4/6: T0@−0.14999847407452621 | row3/8: T4@0.79998168889431442 | header/total remain when bands disabled |
| Medium23 both axes | baseT4@0.79998168889431442; rows5/7 and columnsD/F: T4@0.59999389629810485 | header/total have no own fill | row-label fill is also the darker tint |
| Dark1 rows | baseT0@−0.249977111117893; rows5/7: T0@−0.34998626667073579 | row3/8: T1@0.499984740745262 | column-only bands have no fill |
| Dark28 both axes | baseT9; rows5/7 and columnsD/F: T9@0.39997558519241921 | header/labels:T9@−0.249977111117893; total inherits base | missing total fill must not erase base |

Eleven fast Python units check self-contained relationships/XML, deterministic source parity,
hand-calculated values, fixture flags/offsets, all84presets, extractor rejection cases and known
asymmetric/header/total data. They run in under a second without opening the documents.

## Compile-only acceptance boundary

The16.10run7 production compile and baseline-restore evidence is recorded in the private project's
`docs/research/pivot-banding.md`; it is not a rendering result. Use the official launcher with
`-Module sc`, the unchanged configured OXT/brand inputs and an outer atomic build.lock. Restore
the original two sources, remove the generated draft header and touch/recompile originals before
releasing the lock. Never use default make, make−n or hand object compilation for this check.

Before any merge, owner-authorized runtime checks must cover all84presets, custom themes,
independent/both/no bands, header flags, every total combination, changed geometry, negative
controls, fonts/borders, refresh and round trips in Calc and Excel, followed by native regression
tests using established expectations. Compile success and XML consistency do not prove those results.
