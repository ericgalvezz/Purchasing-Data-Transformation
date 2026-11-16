# Business case — Purchasing Data Transformation

## Engagement context

Independent solution-design and operational-improvement work for a **US-based custom manufacturing business**. The business relies on supplier documents for purchasing, material categorization and eventual project-cost review. The company's identity, supplier relationships and financial documents are intentionally not disclosed.

The engagement focused on one concrete activity: turning incoming supplier PDFs into usable purchasing information. It was **not** a company-wide ERP or digital-transformation implementation.

## Business problem and observed baseline

Supplier invoices and orders arrived in varying PDF formats, creating repetitive data entry, inconsistent document naming and fragmented purchasing information.

The **measured minimum baseline was 16 hours of manual data entry per week** for this activity. The larger context is important: material purchases eventually need to be categorized, reviewed and connected with customer jobs or inventory decisions.

## Opportunity and solution approach

The opportunity was to shift from file-by-file transcription toward batch processing, structured outputs and human-led exceptions.

My contribution included:
1. Understanding the purchasing process and its relationship with production and project costing.
2. Translating business needs into field-extraction, routing, file-safety and usability requirements.
3. Choosing a locally runnable workflow that nontechnical Windows users could operate.
4. Using AI-assisted development to accelerate construction while reviewing the implementation and outputs.
5. Validating results and writing user-facing instructions.
6. Proposing a longer-term route to purchasing-data quality, accounting readiness and inventory visibility.

### Key choices and rationale

| Decision | Business rationale |
|---|---|
| Local-first PDF processing | Preserve control of sensitive supplier documents and avoid an external processing dependency |
| Excel as operational output | Deliver a familiar format users can inspect without a new platform |
| `processed`, `manual_review`, `failed` | Focus people on exceptions rather than silently accepting unreliable extraction |
| Copy, never destructively move originals | Protect source documents and improve traceability |
| Suggestions, not accounting postings | Keep project allocation and inventory judgments with authorized reviewers |

## Observed operational impact

| Measure | Evidence and scope |
|---|---|
| Before | **≥16 hours/week** of manual supplier-document data entry (measured minimum) |
| After | **≤4 hours/week** for review and corrections in the automated workflow (observed maximum) |
| Difference | **≥12 hours/week** reduction between these active tasks |
| Relative improvement | **~75% reduction** in hands-on effort at the conservative bounds |

**Method:** (16 − 4) ÷ 16 = 75%. The comparison concerns the defined manual entry/review activity and uses the minimum observed baseline and maximum observed post-automation review effort. It **does not** include unattended machine runtime, potential additional setup overhead or other downstream activities; those should be measured separately for an end-to-end elapsed-time calculation. The figures were reported from operational observation; original internal records are not published.

This is an **observed process-level productivity result**, not a monetary ROI, a company-wide productivity increase or a measured labor-cost saving.

## Delivered capability vs. public recreation

**Delivered private initiative:** local PDF batch-processing workflow, structured Excel output, supplier file organization, confidence-based exception routing and user documentation. Actual business source documents are confidential.

**Public GitHub reproduction:** functioning sanitized implementation with seven **entirely synthetic** PDFs, fictional supplier/account rules and a generated example workbook. Its validation proves reproducible technical behavior: five processed, one manual review and one intentionally invalid failure. The demo counts are not the source of the 16-to-4-hour operational comparison.

## Broader value and future roadmap

The initiative illustrates a potential path from a focused manual-task improvement toward a better purchasing-data foundation:

- **Current capability:** reduce repetitive entry, create consistent document records and surface exceptions.
- **Proposed next step:** approved Project IDs, reviewed material categories and duplicate checks for accounting-ready exports.
- **Longer-term possibility:** inventory-release records, project cost attribution and management reporting.

These downstream steps were **proposed**, not implemented as part of the MVP. The business would need to choose, fund and adopt them.

## Further measurement

For fuller value engineering, document weekly volumes, time spent actively handling exceptions, automated runtime, preparation effort, field-level accuracy, user adoption and any maintenance burden. Monetary benefits would require actual labor-cost and process-cost inputs.

The solution creates review-ready data, **not** final journal entries, inventory balances, tax determinations or complete job margins.
