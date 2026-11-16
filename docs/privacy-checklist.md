# Privacy and public-release checklist

This repository is a portfolio demonstration of an independently developed business-process solution. The actual operating company remains confidential.

## Data and source review

- [x] No real supplier or customer PDFs are included.
- [x] Demonstration PDFs, names, invoice numbers, amounts and account codes were created with fictional values.
- [x] Public supplier rules use `config/demo_rules.json` instead of the private business configuration.
- [x] The example workbook is generated from synthetic documents only.
- [x] Original source files and private operational records were not transferred into this Git repository.
- [x] `input/`, `output/`, `private_config/` and `private_data/` are ignored by Git.
- [x] The code, demo assets and available repository history were checked for known confidential identifiers.
- [x] Windows 11 execution and preserved output runs were validated.

## Disclosure and rights

- [x] Approval to publish the **anonymous business case** was confirmed by the project owner.
- [x] For the first portfolio release, no open-source license is offered; no license file is included.
- [x] The project documentation distinguishes observed operational results, reproducible synthetic tests and future proposals.

## Ongoing safeguard

Do not commit customer/supplier invoices, prices from actual transactions, bank or tax identifiers, internal accounting exports, confidential user feedback, real project references or credentials. Always review new files before pushing changes.

The targeted privacy audit is a documented control, not a guarantee that every possible disclosure risk has been eliminated.
