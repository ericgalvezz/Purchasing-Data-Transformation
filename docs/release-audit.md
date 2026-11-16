# Release audit — portfolio demonstration

## Scope

This audit covers the **public-facing, sanitized showcase**. It does not evaluate or publish the original company's private supplier records or accounting material.

## Functional validation

- Python extraction engine and demo configuration retained.
- Seven fictional PDFs: **5 processed, 1 manual review, 1 deliberately invalid failure**.
- Automated smoke tests checked output routing, workbook creation, source-file hashes and repeat runs.
- Windows 11 / Python 3.13 end-user validation completed: installer worked; a second execution preserved the first run's output folder.
- README diagrams, sample files and linked documentation were checked for existing repository paths.

See [Validation Results](validation-results.md) for exact scope. The fictional seven-file result must not be represented as a production automation success rate.

## Confidentiality safeguards

- Sample supplier names, invoices, amounts and account codes are fictional.
- The repository uses an independent, sanitized source and demo dataset; no original supplier PDFs are committed.
- Targeted scans of source, configuration and written materials found no known real supplier or operating-company identifiers.
- Git history and file inventory were reviewed. The source engine and demonstration assets were not modified during the final editorial changes.
- Private input/output directories are excluded through `.gitignore`.

## Operational evidence versus demo evidence

An observed minimum of **16 hours/week** of manual supplier-document entry was compared with a maximum of **4 hours/week** of reviewing and correcting automated outputs. This indicates approximately **75% less hands-on effort for that activity**. The underlying business records are private and not part of this release.

The seven fictional PDFs and Windows smoke test demonstrate the **public software's behavior**, not the origin of the business time-savings data.

## Publication decision

The project owner confirmed authorization to publish the anonymous case study and requested public release. The initial repository is provided **without an open-source license**; rights remain reserved. GitHub visibility is managed by the repository owner.

Further enhancements and deeper supplier, OCR, costing or inventory integration are optional roadmap items, not required for this showcase.
