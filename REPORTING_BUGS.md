# Reporting bugs and security issues

## Bug reports

Search [existing issues](https://github.com/qpiai/qpiai-finance/issues), then use the [bug report form](https://github.com/qpiai/qpiai-finance/issues/new?template=bug_report.yml). Include:

- Finance, Opt, Python, and relevant solver versions; operating system and architecture.
- A reproducible financial model using data that you are permitted to publish.
- Expected and observed behavior, including the financial units and horizon.
- Execution mode, selected solver or algorithm, options, and relevant inspection output.
- A redacted traceback or result diagnostics.

For an incorrect decision, include the affected source constraint or accounting identity and an independent calculation of the discrepancy. For a performance report, include input dimensions, sparsity, hardware, solver settings, timing boundaries, and the required solution quality.

Do not publish credentials, confidential positions, customer information, account identifiers, or private model data. Inspection reports and result records can contain the complete source inputs; inspect and redact them before attaching them. A credential-free reproducer does not need to execute a paid job to explain a formulation or decoding defect.

## Security policy

Use the repository's [private vulnerability reporting page](https://github.com/qpiai/qpiai-finance/security/advisories/new) for suspected authentication, authorization, credential handling, unsafe interchange, or dependency vulnerabilities.

Include the affected versions, impact, reproduction conditions, and mitigations if known. Do not include live credentials. Coordinate disclosure with the maintainers before opening a public report containing exploit details.
