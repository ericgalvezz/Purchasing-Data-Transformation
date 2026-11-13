# Limitations and roadmap

## Known limitations

- Text-layer extraction only: image-only PDFs are not automatically OCR'd.
- Some parsing logic is format-oriented and requires adjustment for new supplier templates.
- Supplier recognition depends on illustrative aliases in the demo configuration.
- Material/account suggestions use keywords and are not accounting or tax advice.
- Inventory treatment cannot be inferred reliably from a supplier invoice alone.
- No direct QuickBooks integration, customer Project matching, or complete job costing.
- Error handling in workbook generation can fall back to reduced workbook formats if rich formatting fails.
- No production-scale accuracy benchmark or measured savings.
- Public demo contains synthetic documents only; it is not real business data.

## Recommended next stages

**Operational:** Collect voluntary user feedback and measure baseline handling time, exception rates and data accuracy on a consented private dataset.

**Extraction:** Extend supplier layouts with tests, add optional local OCR, strengthen line-item accuracy and make field-level confidence explicit.

**Accounting readiness:** Add approved project IDs, cost-category review/approval, controlled export formatting and duplicate checks.

**Inventory:** Define a material master, consistent units, actual stock-receipt/release records and reconciliation steps; accounting setup requires review by the business accountant.

**Productization:** Add optional lightweight UI, clearer onboarding, error logs, release versioning and a regression test suite.

## Value-engineering checkpoints

Measure the workflow before claiming ROI: time per document, time to retrieve files, percentage of manual-review cases, field completeness, classification acceptance and downstream project assignment coverage. Express results as measured vs. hypothesized.
