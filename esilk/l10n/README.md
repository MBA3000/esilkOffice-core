# esilk l10n overlays

Po files here replace single kk/ru translations of installer and readme
strings without changing the upstream `translations` submodule.

## Why

l10ntools merges translations by source file, group and id
(`MergeDataFile::CreateKey` in `l10ntools/source/merge.cxx`); the msgid is not
part of the key. So when esilk changes an en-US string in a `.ulf` or `.xrm`,
the merge keeps the old upstream translation. Checked with the built `ulfex`:
after the en-US shortcut tooltip was changed, kk still read
"LibreOffice - The Document Foundation жасаған…". A string with a new id has no
translation at all, so it is missing from the kk/ru readmes.

## How it works

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
- Copy the upstream entry format: `#: <source file>`, the three-line msgctxt,
  msgid = the current en-US text, msgstr = the translation.
- Keep all entries of one source file together. Never put a `# ` comment
  inside an entry: the parser stops there and l10ntools skips the whole file.
  `#.` comments are fine.
- Only strings merged by `ulfex`/`xrmex` (installer, readme) use the overlays,
  not the UI `.mo` files.
- After changing an en-US string or an overlay, update the overlay msgid and
  msgstr together. `esilk/l10n/check_overlays.py` fails when an overlay names
  a missing string, cannot be parsed, or its msgid differs from the en-US text.
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
