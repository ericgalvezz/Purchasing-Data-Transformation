# Solution architecture and design decisions

This is the **technical companion** to the [business-first README](../README.md). It maps requirements to design choices, code and verification.

## Processing flow

```text
Input PDFs on the local computer
          |
          v
Locate PDF payload (including supported wrapped PDFs)
          |
          v
Extract selectable text with pdfplumber
          |
          v
Parse supplier, document references, dates, totals and items
          |
          v
Apply confidence checks and illustrative material-category rules
          |
          +-- sufficient required fields and acceptable text --> processed/<supplier>/
          |
          +-- missing fields / scan-like or low-confidence ----> manual_review/
          |
          +-- parse or extraction exception -------------------> failed/
          |
          v
Excel workbook: README | Summary | Detailed Extraction
                | Supplier tabs | Account Rules
```

The tool reads locally stored files and creates copies plus a workbook. It does not upload documents or post transactions to an accounting system.

## Requirements → implementation → evidence

| Requirement | Implemented through | How to verify |
|---|---|---|
| Preserve the input PDFs | `copy_success()`, `copy_for_review()` use `shutil.copy2` | `tests/test_demo.py` compares input hashes |
| Avoid overwriting files | `sanitize_filename_part()` and `unique_path()` | Collision-handling code; filename tests are a possible extension |
| Keep previous batch results | Timestamped `run_...` folders with collision handling in `Run PDF Extraction.bat` | Windows second run retained first output |
| Process without an external document service | Local file reads and `pdfplumber`; no cloud API dependency | Inspect dependencies and source |
| Separate uncertain and invalid files | `process_pdf()` and `--scan-policy manual_review` | Synthetic image-only and invalid PDF fixtures |
| Continue after a single-document failure | Per-document exception handling inside `process_pdf()` | Batch test completes despite one intentionally invalid file |
| Offer familiar output | `write_excel()` and the sheet-building functions | Inspect the generated workbook |
| Avoid unsupported accounting decisions | `classify_account()` and `possible_inventory_account()` supply suggestions, not postings | Check columns and fictional `config/demo_rules.json` |
| Support Windows users without code commands | `Install Requirements.bat` and `Run PDF Extraction.bat` | Windows 11 installation and smoke test |

## PDF and text extraction

`find_pdf_payload()` locates the `%PDF` and `%%EOF` markers and can recover the specific case of a valid embedded PDF surrounded by extra wrapper bytes. This is not a general-purpose PDF repair service.

`extract_text_with_pdfplumber()` reads the **existing text layer**. The OCR hook is inactive. Image-only PDFs cannot be fully read by the current version and should be reviewed manually.

The parser uses field labels and text patterns to identify suppliers, invoice/order numbers, dates, amounts, descriptions, product identifiers and line items. The workbook uses **34 data and control columns**, including confidence and processing status.

## Routing logic

In the Windows default demonstration mode (`--scan-policy manual_review`):

- **`processed/`**: required supplier, description and invoice/order reference are present, and the document is not marked scan-like or low-confidence under this policy.
- **`manual_review/`**: required fields are missing, or the PDF is scan-like/has low-confidence line items.
- **`failed/`**: a technical exception prevents ordinary processing.

Confidence is rule-based; a document routed to `processed` is **not guaranteed semantically accurate**.

## Output safety and structure

Source PDFs are never moved, renamed or deleted. The program creates copies, sanitizes names for Windows, and applies suffixes to avoid collisions.

The Windows runner writes to a new timestamped folder, so earlier outputs remain. The CLI accepts an explicit `--output-root`; callers should use a new root for an independent run.

Normal Excel output includes:

- **README** — operating guidance
- **Summary** — totals by supplier, status and classification
- **Detailed Extraction** — all extracted fields and control notes
- **Supplier tabs** — simplified supplier-specific records
- **Account Rules** — examples used for category suggestions

The tool includes a minimal XLSX fallback if rich workbook creation fails; it does not have the full normal multi-sheet experience. `safe_excel_text()` helps prevent extracted data from becoming spreadsheet formulas.

## Test coverage and evidence

The public demo has seven fictional PDF files covering supplier recognition, different document formats, a wrapped PDF, an image-only document and an intentionally invalid file.

`tests/test_demo.py` checks the expected **5 processed / 1 manual review / 1 failed**, workbook creation, source-file hash preservation and repeatability. The Windows launcher was also exercised twice on Windows 11 with Python 3.13, retaining both run directories.

Detailed outcomes: [Validation Results](validation-results.md).

### Run automated tests

```bash
python -m unittest discover -s tests -v
```

### Run the CLI

```bash
python src/extract_pdf_fields.py \
  --input demo/fixtures \
  --output-root output/demo-run \
  --output extraction_report.xlsx \
  --scan-policy manual_review
```

## System boundaries

The configuration in `config/demo_rules.json` has entirely fictional supplier aliases and account codes. They are **not** a real chart of accounts.

This is a local MVP, not an ERP or a hardened enterprise document service. It has no OCR, user authentication, central audit database, automatic project matching, QuickBooks posting or complete inventory tracking. See [Limitations and Roadmap](limitations-and-roadmap.md).
