# Draft: built-in PivotTable solid band fills on XLSX import

**Compile-only prototype; keep the PR a draft. No runtime import, CppunitTest or Office/Excel
comparison has been performed.** The patch is deliberately narrower than complete PivotTable styling.

Verification on16.10.2026: Windows production `make sc` completed with exit0 (10s); after removing
the draft overlay, the original sources were recompiled with exit0 (12s). The build tree was restored
to core main58c57dba. Three fast Python ZIP/XML fixture checks pass (0.09s). None of this proves rendering.

## Upstream behavior and source

The 26.8 baseline reads `pivotTableStyleInfo`, stores its name/row/column flags on `ScDPObject`
and writes them back on XLSX export. None of the stored stripe flags is consumed by the drawing/output
path. By contrast, ordinary database tables have a separate `ScTableStyle` implementation.
The existing default-table-style generator explicitly skips pivot definitions. References:

- [import](https://github.com/LibreOffice/core/blob/e155df48174bf3e64426fb1b912b9c15fa375704/sc/source/filter/oox/pivottablefragment.cxx),
  [stored model](https://github.com/LibreOffice/core/blob/e155df48174bf3e64426fb1b912b9c15fa375704/sc/inc/dpobject.hxx),
  [export](https://github.com/LibreOffice/core/blob/e155df48174bf3e64426fb1b912b9c15fa375704/sc/source/filter/excel/xepivotxml.cxx).
- [upstream generator](https://github.com/LibreOffice/core/blob/e155df48174bf3e64426fb1b912b9c15fa375704/sc/workben/generate_ooxml_tablestyle_info.py),
  `parse_pivot_style`/`parse_style`.
- [ECMA-376 Part1](https://ecma-international.org/publications-and-standards/standards/ecma-376/),
  `OfficeOpenXML-SpreadsheetMLStyles.zip/presetTableStyles.xml` in the Part1 download.
  These pivot presets are not interchangeable with equally numbered `TableStyleLight/Medium` styles.
- [Microsoft row stripes](https://learn.microsoft.com/en-us/office/vba/api/excel.pivottable.showtablestylerowstripes)
  and [table style elements](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/5c1d12a9-01db-4471-897a-e2d2875980c5).

## Minimal design

After creating the imported pivot, obtain its actual `RESULT` rectangle and exclude its grand total
row/column. Apply background-only `ScPatternAttr` items on alternating rows **or** columns of that
data body; preserve number formats, borders and fonts. Use `XlsColor` for the workbook theme/tint
and preserve the complex theme color on `SvxBrushItem`.

The generated table contains the **35** Light/Medium presets whose band definitions have a solid
fill. Light1–7 and Light15–28 use first-stripe fills; Medium15–21 use first-stripe fills and a base
fill; Medium22–28 use a second-stripe fill and a base fill. Some Medium first-stripe/base colors
are equal: their remaining band distinction is border/font formatting, outside this prototype.
Light8–14 and Medium1–14 have no solid band fill and are intentionally left unchanged.

Guardrails: exactly one row field, one column field, one data field; no page fields, explicit pivot
formats or both-axis stripes. Unknown/custom/Dark styles are skipped. The data body must fit entirely
inside the imported location rectangle; changed geometry is skipped. Labels, headers, subtotals,
grand totals, refresh-time styling, full preset borders/fonts and persistent ODF style semantics
are outside this first import. These exclusions avoid guessing precedence or repainting other cells.

Regenerate the compact data header from the published preset XML using
`sc/workben/generate_pivot_stripe_fills.py INPUT sc/source/filter/inc/pivotstripefills.hxx`.
The extractor rejects non-theme/unequal-axis fills and non-unit stripe widths instead of approximating them.

## Hand-made reproducers and deferred runtime check

`make_reproducers.py` creates all seven XLSX files from raw XML and fixed ZIP metadata. Content is
only groups A–D, quarters Q1–Q4, integers 10–43; no user file, private text, author, external link or
office automation was used. Source/cache/cached-output values agree: row totals46/86/126/166,
column totals100/104/108/112 and grand total424. `test_fixtures.py` checks XML/relationships and these
independent hand-calculated totals in milliseconds.

Intended data body: C4:F7, with header row3, row labelsB and grand totalsG/8.

| File | Deferred expected fill-only change |
|---|---|
| `light16-rows.xlsx` | Rows4/6: theme0 with tint−0.14999847407452621 |
| `light23-columns.xlsx` | ColumnsC/E: accent1(theme4), tint0.79998168889431442 |
| `medium23-rows.xlsx` | Whole body accent1 tint0.79998168889431442; rows5/7 tint0.59999389629810485 |
| `medium24-columns.xlsx` | Whole body accent2 tint0.79998168889431442; columnsD/F tint0.59999389629810485 |
| `disabled-control.xlsx` | No fill import |
| `both-axes-control.xlsx` | No fill import: precedence deferred |
| `dark-control.xlsx` | No fill import: unsupported preset family |

Before considering merge: import each fixture in Calc and Excel, check actual geometry/values/fills,
unchanged labels/totals, custom themes, refresh, XLSX/ODS round trips and no-change controls; add
native import regressions after those expectations are established. A successful compile or static
ZIP check does not establish those results.
