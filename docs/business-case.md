# Business case: from a manual task to a working solution

## The setting

This was an independent process-improvement project for a **US-based custom manufacturing business**. The business uses supplier documents to manage purchases of materials for customer jobs. Its identity and underlying commercial records remain confidential.

The project addressed a specific operational problem: getting useful purchasing information out of supplier PDFs without manually re-entering it document by document. It was not a company-wide ERP transformation.

## The problem and the opportunity

Supplier invoices and orders used different PDF layouts. Employees had to open documents, locate details, enter them into spreadsheets and keep the files organized. The **measured minimum workload was 16 hours per week of manual data entry** for this activity.

I saw two opportunities:

- **Immediate:** reduce repetitive entry and allow staff to focus on checking exceptions.
- **Future:** establish more consistent purchasing records that could support job costing, inventory and reporting later.

The second was a proposal for future development, not part of the initial delivered system.

## My role and approach

I worked across business analysis, solution design and implementation:

1. **Understand:** examined the purchasing-document process and its relationship to materials, customer projects and cost information.
2. **Define:** specified the information to extract, output format, document handling, error routes and operating instructions.
3. **Design:** prioritized an easy local Windows/Excel workflow and transparent human review instead of a complex new platform.
4. **Implement:** guided development with AI coding tools, reviewed the logic and outputs, and iterated on the identified issues.
5. **Validate:** tested the functional workflow with documents and prepared instructions for nontechnical users.
6. **Look ahead:** proposed how structured purchasing data might later support project-cost assignment and inventory visibility.

This engagement demonstrates ownership of a **focused operational improvement**, not ownership of a full digital transformation program.

## Requirements and design choices

| Requirement or constraint | Design decision | Why it mattered |
|---|---|---|
| Easy for nontechnical employees | Double-click Windows files and Excel output | Reduce training burden and avoid a new business system |
| Keep supplier information private | Local PDF processing | Avoid sending documents to an outside processing API |
| Never lose source records | Copy documents instead of moving or deleting originals | Traceability and recovery |
| Uncertain PDFs need human judgment | `manual_review` route and confidence indicators | Avoid silently accepting incomplete extraction |
| One bad PDF should not stop the batch | Separate `failed` route with notes | Continue processing other files |
| Protect earlier output | Timestamped run folders | Avoid overwriting prior results |
| Financial treatment needs approval | Material-account suggestions only | Leave project and inventory accounting decisions to people |

See [Solution Architecture](solution-architecture.md) for the code, controls and tests that implement these requirements.

## The delivered workflow

The user places PDFs in an input folder, runs the tool and reviews the generated Excel workbook. The program reads available text, extracts purchasing fields, creates organized copies and separates uncertain or unparseable documents.

Its Excel output contains supplier details, references, descriptions, amounts, classification suggestions, confidence flags and processing details.

The MVP produces **structured data for review**. It does not automatically allocate costs to a QuickBooks Project, manage inventory balances or post accounting transactions.

## Measured impact and method

The comparison covers the **hands-on supplier-document entry and review activity**, not the entire purchasing or accounting process.

| Measurement | Observed result |
|---|---:|
| Before: manual data entry | **At least 16 hours per week** |
| After: reviewing and correcting automated output | **No more than 4 hours per week** |
| Difference at conservative bounds | **At least 12 hours per week** |
| Reduction in hands-on work | **Approximately 75%** |

**Calculation:** (16 − 4) ÷ 16 = 75%.

The baseline uses the measured minimum for manual entry; the post-automation figure uses the observed maximum for checking and correcting output. These observations were supplied from the operating process; the underlying private records are not included in this repository.

The comparison excludes unattended Python runtime and any separate setup or downstream work. It is **not** a monetary ROI calculation or a claim of a 75% productivity increase across the whole company.

## Original initiative versus public demonstration

**Original operating initiative:** local PDF processing, structured Excel output, supplier file organization, exception routing and user instructions for an actual business problem.

**Public GitHub demonstration:** a working independent showcase with seven entirely fictional PDFs and fictional supplier/account rules. Five sample PDFs process automatically, one goes to manual review, and one deliberately invalid PDF demonstrates controlled failure handling. It was successfully run twice on Windows, with both output folders retained.

The synthetic test counts **do not generate or substantiate the private 16-to-4-hour operational measurement**. They establish reproducible technical behavior.

See [Validation Results](validation-results.md) for exact fixture-level scope.

## The bigger opportunity

I proposed extending the small, working automation in stages if the business wanted to invest further:

- **Current:** consistent document handling, structured purchasing information and visible exceptions.
- **Possible next step:** reviewed material classifications, approved project references and controlled accounting-ready exports.
- **Long-term possibility:** inventory material movements, project cost visibility and management reporting.

These future stages remain proposals. Their actual value would depend on adoption, integration cost, data accuracy and operating needs.

## Additional value measurements

A fuller assessment would capture weekly volumes, setup time, machine runtime, exception and error rates, field accuracy, ongoing maintenance and user adoption. To estimate monetary savings, it would also require verified labor and operating costs.
