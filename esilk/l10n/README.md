# esilk l10n overlays

Po files here replace single kk/ru translations of installer and readme
strings, and add or replace kk/ru translations of user interface strings
(`.mo` files), without changing the upstream `translations` submodule.

## Why

l10ntools merges translations by source file, group and id
(`MergeDataFile::CreateKey` in `l10ntools/source/merge.cxx`); the msgid is not
part of the key. So when esilk changes an en-US string in a `.ulf` or `.xrm`,
the merge keeps the old upstream translation. Checked with the built `ulfex`:
after the en-US shortcut tooltip was changed, kk still read
"LibreOffice - The Document Foundation жасаған…". A string with a new id has no
translation at all, so it is missing from the kk/ru readmes.

User interface strings are a different case: the upstream kk/ru po files leave
some strings untranslated (for example ru `STR_NEW_FROM_TEMPLATE`, the
"New From Template" button of File > New > Templates), and the office then shows
the English text.

## How it works

UI strings (`<module>/messages.po`, compiled to `.mo` files):

- `solenv/gbuild/AllLangMoTarget.mk`: when an overlay
  `translations/source/<lang>/<module>/messages.po` exists, `merge_po.py`
  (the build's python, after `check_overlays.py`) writes the po that msgfmt
  compiles: the upstream header, every overlay entry, and the upstream entries
  the overlay does not replace. gettext keys messages by msgctxt and msgid, so
  an overlay entry with the same msgctxt and msgid replaces the upstream
  translation, and an untranslated upstream message gets the overlay
  translation. The `.mo` file depends on its overlay and on `merge_po.py`.
- When esilk rewrites an en-US string, its overlay entry has the new msgid and a
  comment `#. esilk-replaces: "<old msgid>"`; `merge_po.py` then drops the old
  upstream entry, so the old text does not stay in the `.mo`, and
  `check_overlays.py` fails if no upstream entry has that msgctxt and msgid.
- Start an overlay with the header of the upstream po (`check_overlays.py`
  compares `Content-Type` and `Plural-Forms`).

Installer and readme strings (`ulfex`/`xrmex`):

- `solenv/gbuild/TargetLocations.mk`: `gb_POOVERLAYLOCATION` (this directory)
  and `gb_POLOCATION_get_overlays`, which returns the overlays that exist for
  a list of upstream po files.
- `solenv/gbuild/CustomTarget.mk` (`ulfex`: scp2 strings, MSI tables, ...),
  `solenv/gbuild/InstallModuleTarget.mk` and
  `readlicense_oo/CustomTarget_readme.mk` (`xrmex`) pass the overlays after
  the upstream po files, depend on them, and run `check_overlays.py` before
  the merge.
- For the same key, a later po file replaces the text of its language
  (`MergeEntrys::InsertEntry`); an entry with a new id is added.

## Rules

- Path: `translations/source/<lang>/<same path as the upstream po file>`.
  Keep the `translations/source/<lang>/` part: l10ntools reads the language
  from it.
- Copy the upstream entry format: `#: <source file>`, the msgctxt (three
  lines for `.ulf`/`.xrm`, one line for UI strings), msgid = the current en-US
  text, msgstr = the translation. For a UI overlay, copy the entry from the
  upstream po and fill in its msgstr. A plural entry (`msgid_plural`, from
  `NNC_` in the `.hrc` file) keeps all its `msgstr[n]` forms (ru has three);
  the check compares the msgid with the en-US singular and fails when a form
  is empty.
- Keep all entries of one source file together. Never put a `# ` comment
  inside an entry: the parser stops there and l10ntools skips the whole file.
  `#.` comments are fine.
- Configuration strings merged by `cfgex` (`gb_XcuMergeTarget`, e.g. the filter
  UI names) take overlays like `ulfex`; `check_overlays.py` compares them with
  the en-US value of the node/prop in the `.xcu` fragment. Menu and command
  labels in `officecfg/.../Office/UI.po` use the same merge; their msgctxt is the
  nested node path of a complete `.xcu` file (`..CalcCommands.UserInterface.
  Commands..uno:Foo`, prop `Label`), which `check_overlays.py` resolves with
  `en_us_xcu_tree`.
- After changing an en-US string or an overlay, update the overlay msgid and
  msgstr together. `esilk/l10n/check_overlays.py` fails when an overlay names
  a missing string, cannot be parsed, or its msgid differs from the en-US text
  (for UI strings: no `NC_("<msgctxt>", "<msgid>")` in the `.hrc` file or no
  translatable element with that context and text in the `.ui` file).
  The build runs it with its own python (`--quiet`) before every merge that
  uses overlays (`gb_POLOCATION_check_overlays` in
  `solenv/gbuild/TargetLocations.mk`), so a stale overlay stops the build
  instead of shipping an outdated kk/ru text. To check by hand:
  `python esilk/l10n/check_overlays.py`.

## Current entries

| Source | Key | Shown in |
|---|---|---|
| `scp2/source/ooo/folderitem_ooo.ulf` | `STR_FI_TOOLTIP_SOFFICE` | Start menu and desktop shortcut tooltip |
| `scp2/source/ooo/registryitem_ooo.ulf` | `STR_REG_VAL_APPCAPABILITY_DESCRIPTION_OOO` | Windows Default apps description |
| `instsetoo_native/.../msi_languages/Property.ulf` | `OOO_ARPCONTACTTEMPLATE`; `OOO_ARPHELPLINKTEMPLATE`, `OOO_ARPURLINFOABOUTTEMPLATE`, `OOO_ARPURLUPDATEINFOTEMPLATE` (esilk website) | Apps and Features, support contact and links |
| `instsetoo_native/.../msi_languages/Property.ulf` | `OOO_ESILK_MSG_LIBREOFFICE_CONFLICT`, `OOO_ESILK_MSG_LOCATION_REQUIRED`, `OOO_ESILK_MSG_ROLLBACK_REQUIRED` (en-US is kk / ru / en in one line; kk and ru give one language) | installer refusals (Type 19 actions in `scp2/source/ooo/windowscustomaction_ooo.scp`) |
| `ru/scp2/source/ooo.po` | `STR_FI_NAME_SAFEMODE` (empty upstream) | Start menu shortcut "esilkOffice (Безопасный режим)" |
| `ru/svx/messages.po` | `docrecoveryrecoverdialog\|desc`: the text names the button "Отклонить все", as the button reads | document recovery dialog |
| `readlicense_oo/docs/readme.xrm` | `esilkBasedOn`, `esilkWebsite` | `readmes/readme_<lang>.txt` |
| `ru/sfx2/messages.po` | all 31 strings left untranslated upstream, including `STR_NEW_FROM_TEMPLATE` | File > New > Templates button, style panel, infobars, safe mode query |
| `{kk,ru}/{cui,desktop,sc,sd,sfx2,svtools,svx,sw,uui,xmlsecurity}/messages.po` | en-US strings rewritten without LibreOffice, OpenOffice.org, StarOffice or The Document Foundation (owner decision 12.10.2026): About "Licenses" link, Help > License Information, HTML options "%PRODUCTNAME Basic", extension dependency errors, Calc legacy key bindings and WEEKNUM_OOO, Impress Remote tooltip, ODF 1.1 signature messages, safe mode profile export, Basic library warning, Writer "legacy" compatibility options, neutral object and document type names for the old formats ("Legacy Office XML …" for .sx*, "Legacy office …" for the StarOffice 3–5 database, image and template types) | the dialogs named |
| `{kk,ru}/filter/source/config/fragments/filters.po` | 20 filter UI names without OpenOffice.org or StarOffice: 16 "Legacy Office XML …" (.sx* formats), 4 "Legacy binary office …" (StarOffice 3–5 formats) (merged by `cfgex`, see `gb_XcuMergeTarget` in `solenv/gbuild/Configuration.mk`) | Open/Save As file types |
| `{kk,ru}/filter/source/config/fragments/types.po` | type UI name `StarBaseReportChart` → "Legacy Office XML report chart" (merged by `cfgex`) | file type names |
| `ru/{sd,sc,sw,cui,svx,starmath,svtools,chart2,filter,dbaccess,formula,sdext,framework}/messages.po` | all 714 UI strings left untranslated or empty upstream (12.10.2026): sd 223, sc 215, sw 177, cui 42, svx 21, starmath 18, svtools 5, chart2 3, filter 3, dbaccess 2, formula 2, sdext 2 (plural), framework 1 | Tabbed (notebookbar) UI of Writer/Calc/Impress/Draw, Impress presenter console keys and slide sections, Calc pivot calculated fields and function arguments, quick find panel, Options pages, troubleshoot (safe) mode dialog |
| `ru/officecfg/registry/data/org/openoffice/Office/UI.po` | all 39 menu/command labels left untranslated upstream (Calc/Draw/Impress/Writer/Generic commands, merged by `cfgex`) | menus, context menus, tooltips |

The kk UI translation has no untranslated strings in the modules esilkOffice
ships (checked against the `translations` submodule on 12.10.2026). The ru
overlays above cover every UI string the upstream ru po files leave empty or
fuzzy (784: 745 in `messages.po` files, 39 menu labels); recheck after a
`translations` submodule update.
