# Solution architecture

```text
PDFs in local input folder
        |
        v
Read payload (including simple wrapped PDF payloads)
        |
        v
Extract selectable text using pdfplumber
        |
        v
Parse supplier, order, amounts and line items
        |
        v
Confidence checks + illustrative material suggestions
        |
        +---- complete, adequate confidence ----> processed/<supplier>/
        |
        +---- low confidence or missing fields -> manual_review/
        |
        +---- technical extraction error -------> failed/
        |
        v
Excel: README + Summary + Detailed Extraction + supplier tabs + Account Rules
```

## System boundaries

The system executes locally. There is no hosted service, cloud API, AI inference call or automated QuickBooks posting. Dependencies are installed through Python's package ecosystem. PDF data stays on the computer where it is processed.

## File safety

Input PDFs are not modified or moved. Derived PDFs are copies. Collision-safe filenames add incrementing suffixes rather than overwriting. The Windows launcher creates a timestamped output directory with collision handling. The CLI also avoids replacing an existing workbook filename.

## Configurable demo data

`config/demo_rules.json` defines *fictional* supplier names, aliases, material rules and example account numbers. The numeric account codes are **not** the chart of accounts of any real business. They are illustrative labels used to demonstrate routing and the review workflow.

## Relevant technical decisions

- `pdfplumber` operates on embedded text layers; no OCR is enabled.
- Image-only or low-confidence line items route to `manual_review` under the demo run policy.
- Extraction errors do not abort the rest of the batch.
- The output provides both business details and technical control columns.
- Human accounting judgment remains separate from automatic keyword suggestions.

## Constraints

The program is a local MVP and demo, not an ERP, inventory system, or security-hardened document platform. It has no user authentication or central audit database. Windows batch execution requires validation on the end user's Windows installation.
