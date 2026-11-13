# Validation — synthetic release candidate

## Synthetic fixtures only

All fixtures were fabricated for this showcase and contain no invoices, names, invoice references or commercial amounts from the operating company. The generated workbook is based exclusively on those fixtures.

| Fixture | What it tests | Expected outcome |
|---|---|---|
| `01_oakridge_invoice.pdf` | Recognized fictional supplier; sheet goods | processed |
| `02_coastal_panel_invoice.pdf` | Different fictional supplier; MDF | processed |
| `03_summit_hardware_invoice.pdf` | Hardware rule and document fields | processed |
| `04_summit_sales_order.pdf` | Sales order reference handling | processed |
| `05_westbay_wrapped.pdf` | Embedded PDF payload with surrounding synthetic bytes; unknown supplier | processed |
| `SCAN_06_image_only.pdf` | Image-only PDF without a text layer | manual_review |
| `07_invalid_pdf_fixture.pdf` | Intentionally invalid PDF payload | failed |

## Local validation result

**7 total / 5 processed / 1 manual review / 1 failed.** The one failure is intentional and demonstrates controlled exception handling. At least one example goes through the wrapped-PDF parsing branch. Document output is grouped by fictional supplier and an Excel workbook is generated with 34 columns.

## Reproduction

Copy the fixtures into `input/` and run the Windows launcher, or run the CLI command in the main README. Execute tests with `python -m unittest discover -s tests -v`.

## Windows end-user smoke test — 2026-11-13

A Windows 11 user installed Python 3.13 through Microsoft Store, ran `Install Requirements.bat` to completion, copied all seven synthetic fixtures to `input/`, and executed `Run PDF Extraction.bat` twice.

User-provided CMD screenshot from the second run shows:

- `Processed PDFs: 7`
- `Successful: 5`
- `Manual review: 1`
- `Failed: 1`
- `Done. Results are in: .../output/run_20261113_012431`

User-provided File Explorer screenshot shows **two distinct, retained run directories**: `run_20261113_012050` and `run_20261113_012431`. The user also confirmed that the generated Excel workbook and the routed files in the output folders were inspected and behaved as expected. These screenshots were shared for verification in the private review conversation; they were **not uploaded to the repository**.

**Status: Windows end-user smoke test passed.** This covers the tested Windows environment and synthetic fixtures, not enterprise-wide compatibility or production accuracy.

## What this does *not* validate

These fixtures do not demonstrate OCR performance, accuracy over a large supplier population, a representative production success rate, time savings, integration with QuickBooks or accounting correctness. The Windows launcher has now been exercised on one user's Windows 11 system. The test does not establish compatibility with every Windows/Python configuration.
