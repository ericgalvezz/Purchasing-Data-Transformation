# Privacy and release review

## Local audit performed

- [x] No uploaded real supplier PDFs copied into the showcase.
- [x] Supplier names and aliases in code replaced by fictitious demonstration names.
- [x] Example account codes are clearly fictitious and distinct from the original source configuration.
- [x] Invoice numbers, amounts and document texts fabricated from scratch.
- [x] Generated output workbook produced from synthetic fixture input only.
- [x] Input, output and private configuration directories ignored by Git.
- [x] Repository assembled in a new working folder rather than copied from the source project's Git history.

## Publication requirements

- [ ] Business owner confirms that public disclosure of the solution description is acceptable (where applicable).
- [ ] Review source ownership and choose whether to add an open-source license.
- [ ] Run a clean Windows installation + execution smoke test.
- [ ] Run a full last-pass file/content inspection immediately before changing repository visibility to public.
- [ ] Confirm no sensitive data in Git commit history, issues, releases, or screenshots.

## Never commit

Customer or supplier invoices, tax identifiers, business banking details, project estimates, operational accounting ledgers, original private config files, credentials or private user feedback.

`gitignore` protection is helpful but insufficient: inspect staged changes before committing, and keep sensitive inputs outside the repo whenever possible.
