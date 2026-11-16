# Limitations and roadmap

## Current capabilities and limits

The local MVP reads selectable PDF text; it does **not** perform OCR on image-only documents. New supplier layouts may require additional parsing rules. Supplier aliases and account codes in the public showcase are fictional, and material/category suggestions require human review.

The tool does not assign purchases to real QuickBooks Projects, post transactions, manage inventory balances, or calculate full project profitability. It is not an ERP replacement.

The **observed hands-on time improvement** for the specific supplier-document entry/review activity is described in [the business case](business-case.md). That is separate from unmeasured full-workflow elapsed time, dollar-denominated ROI and broader business adoption. The public seven-PDF sample demonstrates technical behavior only, not production-scale extraction accuracy.

## Practical improvement path

### 1. Stabilize and measure
- Capture weekly document volume and representative before/after workflow samples.
- Measure human review effort, preparation, machine runtime and exception rates separately.
- Expand field-level accuracy checks on permitted private data.
- Collect end-user feedback and keep installation easy.

### 2. Extend extraction safely
- Add supplier-specific layouts and regression tests.
- Consider optional local OCR for image-only files.
- Improve line-item parsing and confidence reporting.

### 3. Support accounting readiness
- Introduce approved customer Project identifiers and duplicate checks.
- Make material classification review and approval explicit.
- Create controlled exports only after accounting-owner review.

### 4. Explore inventory and reporting
- Define materials and units consistently.
- Link documented stock receipt and release events to jobs.
- Build purchasing, exceptions and cost-visibility reporting if business priorities justify it.

These are **potential stages**, not features already delivered. The business should prioritize them based on adoption, costs, data readiness and value.
