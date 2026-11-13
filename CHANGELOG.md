# Changelog

## Portfolio showcase candidate — 2026-11-13
- Forked locally from an existing operational Python PDF extractor without editing the original archive.
- Replaced hard-coded real supplier recognition names and material-account codes with fictional demo configuration.
- Created synthetic documents demonstrating processed, manual-review and failed routes.
- Updated the Windows launcher to create timestamped run folders rather than delete prior output.
- Changed workbook output-folder values to portable relative paths.
- Added text protection to prevent data values beginning with formula-like characters from being written as formulas.
- Added reproducible automated smoke test and release documentation.

All demonstration invoices, account codes, suppliers, quantities and amounts are fictional.

## Windows demo smoke test — 2026-11-13
- Confirmed installation on Windows 11 with Python 3.13 and the Windows requirements launcher.
- User ran seven synthetic PDF fixtures: five processed, one manual review and one intentional invalid-PDF failure.
- Confirmed second run creates a new timestamped output folder while retaining the prior run.
- Recorded user-verified workbook/folder outputs in `docs/validation-results.md`.
- Repository remains private pending final disclosure and licensing review.
