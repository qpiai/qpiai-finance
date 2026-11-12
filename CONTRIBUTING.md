# Contributing to QpiAI Finance

Development takes place in [qpiai/qpiai-finance](https://github.com/qpiai/qpiai-finance). Search existing issues before reporting a [bug](REPORTING_BUGS.md) or proposing a [feature](FEATURE_REQUESTS.md). Fork the repository, create a branch from `main`, and submit a pull request describing the problem, resulting behavior, and validation.

## Development setup

Use a Python version supported by the package and its dependencies. Create and activate a virtual environment, then install the checkout and documentation dependencies:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
source .venv/bin/activate
```

```bash
python -m pip install -e ".[dev]"
python -m pip install -r docs/_build_html/_sources/requirements.txt
python -m pip check
```

Include tests and validation needed to assess your change in the pull request.

Optional Git hooks use the repository's pre-commit configuration:

```bash
python -m pip install pre-commit
python -m pre_commit install
```

## Code changes

Keep financial semantics, solver execution, and result verification consistent. Before implementing a formulation, state its decision variables, units, feasible set, objective, and assumptions. Reuse existing finance calculations and QpiAI Opt representations where they fit. Changes to a solver route must preserve the original financial problem and expose any required transformation.

Follow PEP 8 and the repository's Ruff configuration. Use conventional financial terminology and concise public docstrings. Changes to public signatures, supported inputs, solver options, results, or failure behavior require corresponding documentation.

Validate the behavior changed, including relevant numerical boundaries and failure paths. For financial formulations, compare source objectives, constraints, and accounting with an independent calculation. Performance claims require the same financial problem, hardware, tolerances, and resource budget for every method compared. Include model construction and verification when reporting end-to-end latency.

Every Finance solve requires Opt authentication. Gate-based execution additionally requires QCloud authentication. Keep credentials outside source, documentation, reports, and serialized models. Paid platform work must be explicitly selected and authorized; ordinary contribution checks must not submit it automatically.

Reason thoroughly as to what is naturally the responsibility of this library and what components it shall build and enforce, versus what it shall reuse.

```bash
python -m ruff check qpiai_finance docs/_build_html/_sources
python -m build
```

## Documentation changes

Markdown is the editable source. Keep the financial task, mathematical contract, parameters, results, and failure behavior on the relevant reference page; link to shared conventions instead of duplicating them.

```bash
python docs/_build_html/_sources/build.py
```

The builder checks registered Markdown pages, local links, fragments, and duplicate HTML identifiers. Review search, code copying, equations, navigation, light and dark themes, and narrow layouts. `docs/_build_html/_sources/pages.json` defines navigation order. Include new pages there. HTML build tools, templates, and source assets are kept in `docs/_build_html/_sources/`; editable Markdown chapters are directly in `docs/`. The build publishes Markdown copies and a `llms.txt` index alongside HTML.

## Pull requests

Describe the concrete problem and the behavior after the change. Include relevant mathematical assumptions, compatibility effects, validation results, and any changed execution costs. Keep changes focused so reviewers can assess the formulation and implementation together.

By submitting a contribution, you agree to license it under the [Apache License 2.0](LICENSE).

## Community guidelines

Discuss technical disagreements respectfully, accept constructive feedback, and protect contributors' privacy. Harassment, personal attacks, and disclosure of private information are unacceptable. Maintainers may remove inappropriate content or restrict participation to protect the community.

Report suspected vulnerabilities through the private process in [Reporting bugs and security issues](REPORTING_BUGS.md).
