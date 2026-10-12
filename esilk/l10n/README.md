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
  upstream po and fill in its msgstr; plural entries (`msgid_plural`) are not
  supported by the check.
- Keep all entries of one source file together. Never put a `# ` comment
  inside an entry: the parser stops there and l10ntools skips the whole file.
  `#.` comments are fine.
- Configuration strings merged by `cfgex` (`gb_XcuMergeTarget`, e.g. the filter
  UI names) take overlays like `ulfex`; `check_overlays.py` compares them with
  the en-US value of the node/prop in the `.xcu` fragment. Menu labels in
  `officecfg/.../UI.po` use the same merge, but their msgctxt is a nested node
  path that `check_overlays.py` does not resolve yet: extend `en_us_xcu` before
  adding such an overlay.
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
| `instsetoo_native/.../msi_languages/Property.ulf` | `OOO_ARPCONTACTTEMPLATE` | Apps and Features, support contact |
| `readlicense_oo/docs/readme.xrm` | `esilkBasedOn` | `readmes/readme_<lang>.txt` |
| `ru/sfx2/messages.po` | all 31 strings left untranslated upstream, including `STR_NEW_FROM_TEMPLATE` | File > New > Templates button, style panel, infobars, safe mode query |

| `{kk,ru}/{cui,desktop,sc,sd,sfx2,svtools,svx,sw,uui,xmlsecurity}/messages.po` | en-US strings rewritten without LibreOffice, OpenOffice.org or The Document Foundation (owner decision 12.10.2026): About "Licenses" link, Help > License Information, HTML options "%PRODUCTNAME Basic", extension dependency errors, Calc legacy key bindings and WEEKNUM_OOO, Impress Remote tooltip, ODF 1.1 signature messages, safe mode profile export, Basic library warning, Writer "legacy" compatibility options, "StarOffice XML" object and document type names | the dialogs named |
| `{kk,ru}/filter/source/config/fragments/filters.po` | 16 filter UI names "OpenOffice.org 1.0 …" → "StarOffice XML …" (merged by `cfgex`, see `gb_XcuMergeTarget` in `solenv/gbuild/Configuration.mk`) | Open/Save As file types |

The kk UI translation has no untranslated strings in the modules esilkOffice
ships (checked against the `translations` submodule on 12.10.2026); ru still has
about 750 untranslated UI strings, mostly in Writer, Calc and Impress
(sw, sc, sd, cui, svx), and 39 menu labels in `officecfg/.../UI.po`.
