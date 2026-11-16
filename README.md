# Purchasing Data Transformation

**Turning hours of manual work into a simpler, automated purchasing process.**

*An independent process-improvement project for a US-based custom manufacturing business.*

Every week, staff spent hours reading supplier PDFs, entering information into spreadsheets and organizing files. **I designed and delivered a tool to handle the repetitive steps automatically**, so people could focus on checking exceptions instead of copying data.

### The result: about 75% less hands-on work

| Before | After | Improvement |
|---|---|---|
| **16+ hours/week** manually entering supplier-document data | **Up to 4 hours/week** reviewing and correcting the output | **At least 12 hours/week** of manual effort reduced (**~75%**) |

These are observed figures for this **specific activity**, not a company-wide productivity claim. The comparison measures hands-on data entry versus hands-on review and corrections, not unattended processing or separate setup time. [See the measurement method](docs/business-case.md#measured-impact-and-method).

## The problem

Supplier invoices and orders arrived as PDFs in different formats. Someone had to open each file, find the important details, enter them into Excel and organize the documents.

It was repetitive work, and the information was difficult to keep consistent and prepare for later purchasing and project-cost reviews.

**My question:** Could we automate most of this work without making the process harder for employees?

## What I built

I developed a Windows tool that:

1. **Reads batches of supplier PDFs** and extracts purchasing details.
2. **Creates an Excel report** with summaries and detailed records.
3. **Organizes document copies** in supplier folders with consistent names.
4. **Flags uncertain results for human review** and separates files that cannot be processed.

Instead of entering every document manually, people can process a batch and concentrate on the files that need attention.

![PDF-to-data workflow](assets/workflow.svg)

## My Approach: Designing Around the Business, Not the Technology

Before building anything, I looked at how the business handled supplier documents and where employees were spending their time.

The challenge wasn't simply extracting information from PDFs. It was finding a way to reduce repetitive work without introducing new complexity or risks for the people using the solution.

I translated that problem into a set of practical requirements: the tool needed to be simple enough for non-technical employees, keep sensitive documents on their computers, preserve original files, and identify uncertain results instead of treating every extraction as accurate.

These requirements guided the design. I chose a local Windows workflow with Excel outputs, automated document organization, and a clear review process for exceptions.

I then used AI-assisted development to build and refine the solution, tested its behavior, and prepared instructions so employees could use it independently.

**The goal was not to automate everything. It was to automate the repetitive work while keeping people in control of decisions that require judgment.**

## See it in action

![Excel report generated with fictional supplier data](assets/summary-demo.png)

This repository contains a **working demonstration using fictional documents created from scratch**. It does not contain real supplier invoices, commercial amounts or private configurations.

| Public demo check | Result |
|---|---:|
| Fictional PDFs tested | 7 |
| Processed automatically | 5 |
| Sent for manual review | 1 |
| Intentionally invalid PDF handled as a failure | 1 |

The demo was also run twice successfully on Windows 11, retaining the output from both runs. **These tests show how the tool works; they are separate from the observed operational time savings.**

[Explore sample PDFs and Excel output](demo/) · [See validation details](docs/validation-results.md)

## Where this could go next

The first goal was to reduce time spent entering supplier data. I also proposed how this could become the starting point for broader operational improvements if the business chooses to expand it.

**Working today:** PDF processing → organized supplier information → Excel report → exception review

**Possible next step:** reviewed material categories and project references → controlled accounting-ready exports

**Longer-term opportunity:** better links between purchasing, inventory movements, project costs and reporting

Those later integrations were **proposals**, not features already delivered. [Explore the roadmap](docs/limitations-and-roadmap.md).

---

## Technical deep dive

This implementation is available for technical review. It uses **Python, pdfplumber, openpyxl, Windows batch files and JSON configuration**.

### Run the demonstration on Windows

1. Install Python 3 so `py` or `python` is available.
2. Double-click `Install Requirements.bat`.
3. Copy the fictional PDFs from `demo/fixtures/` into `input/`.
4. Double-click `Run PDF Extraction.bat`.
5. Open `output/run_.../extraction_report.xlsx` and the `processed/`, `manual_review/` and `failed/` folders.

Each run creates a new output folder. Original input files remain unchanged.

### Run from the command line

```bash
python -m pip install -r requirements.txt
python src/extract_pdf_fields.py \
  --input demo/fixtures \
  --output-root output/demo-run \
  --output extraction_report.xlsx \
  --scan-policy manual_review
```

Use a fresh `--output-root` for an independent CLI run.

### Run the automated test

```bash
python -m unittest discover -s tests -v
```

### Further reading

- **[Architecture, requirements and safeguards](docs/solution-architecture.md):** how the requirements map to code, controls and tests
- **[Business case and decisions](docs/business-case.md):** my role, approach and impact calculation
- **[Validation and reproducibility](docs/validation-results.md):** the fictional test cases and Windows verification
- **[Limitations and roadmap](docs/limitations-and-roadmap.md):** what is and is not implemented
- **[Privacy and release checklist](docs/privacy-checklist.md):** publication controls

**Current boundaries:** No OCR for image-only PDFs, no direct accounting posting and no complete inventory system. Material/account suggestions require human review. The business identity and actual documents remain confidential.

