# Local pre-publication audit

**Scope:** Only the newly created `supplier-document-automation/` folder. The original business source and supplier test archives were not included or modified.

## Static privacy controls
- No copied original invoices or supplier source PDFs.
- Fixture PDFs were generated programmatically from fictitious text and amounts.
- Hard-coded known suppliers replaced with fictitious aliases from `config/demo_rules.json`.
- Original chart-of-account numbers replaced with demo codes.
- Scan and error fixtures contain only deliberately fabricated content.
- `input/`, `output/`, `private_config/` and `private_data/` configured to be excluded from Git.
- Source code and written case documentation reviewed for real vendor names and known operating-company identifiers.

## Automated local validation
- `python -m py_compile src/extract_pdf_fields.py`: passed.
- `python -m unittest discover -s tests -v`: passed.
- Synthetic demo batch: 7 total; 5 processed; 1 manual review; 1 intentional failure.
- Two independent runs: original inputs unmodified, earlier output retained.
- Spreadsheet import and inspection: README, Summary, Detailed Extraction, supplier views, Account Rules.

## GitHub private staging and Windows validation — 2026-11-13
- Sanitized showcase uploaded to the private repository `ericgalvezz/supplier-document-automation`.
- File tree, synthetic fixtures, demo Excel, README image links and Git attributes checked after push.
- `.gitattributes` corrected and verified in the repository.
- User ran the installer successfully on Windows 11 with Python 3.13.
- User ran the batch extractor twice on the seven fictional fixtures. Second CMD run reported **7 input / 5 successful / 1 manual review / 1 intentional failure**.
- Windows Explorer confirmed two preserved run folders; user verified workbook and output-folder content.
- Screenshots were provided privately for validation, not included as public repository assets.

## Remaining release gates
- Windows `.bat` smoke testing is **complete** for the tested Windows 11 setup; additional platform combinations are untested.
- Final human review of disclosure and choice of code license.
- Private GitHub staging is **complete**; public visibility has **not** been enabled.

## Final pre-publication file and history inspection — 2026-11-13
- Reviewed the current private repository tree and all 11 commit summaries. History begins with a newly authored showcase README; source and fixtures entered through a sanitized showcase upload, not a copied operational Git repository.
- Scanned 18 text-based repository files for known real-supplier names, the operating company's name, internal family references, email addresses, secret-like strings, local user paths, and original material-account codes. No matches were found for those identifiers. The only URLs surfaced were public XML/OpenXML namespace URIs used for file formats.
- Verified local binary fixture/image/workbook Git blob hashes match the versions on GitHub. The five readable supplier-style PDFs explicitly identify themselves as fictional; the image-only fixture has no selectable text; the seventh fixture is intentionally invalid.
- Inspected synthetic XLSX package components: no external-link parts and no matches for known private identifiers. The README links point to paths present in the repository.
- **Caveat:** This is a targeted privacy review of known identifiers and supplied test artifacts, not a legal warranty that no commercially sensitive facts could be inferred. Final human disclosure approval and license decision remain open.
