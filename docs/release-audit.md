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

## Remaining release gates
- Windows `.bat` files were reviewed but **not executable-tested on Windows** here.
- Final human review of disclosure and choice of code license.
- No private GitHub repository created during local artifact preparation.
