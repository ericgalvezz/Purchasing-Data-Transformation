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

## What this does *not* validate

These fixtures do not demonstrate OCR performance, accuracy over a large supplier population, a representative production success rate, time savings, integration with QuickBooks or accounting correctness. The Windows launcher has not been executed in a Windows environment as part of this local build and still requires Windows smoke testing before publication.
