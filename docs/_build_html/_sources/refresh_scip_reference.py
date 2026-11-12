"""Refresh the native parameter catalogue from an installed PySCIPOpt build."""

from __future__ import annotations

import re
import tempfile
from collections import defaultdict
from pathlib import Path


def main() -> None:
    from pyscipopt import Model

    model = Model()
    with tempfile.TemporaryDirectory(
        prefix="finance-scip-reference-"
    ) as directory:
        source = Path(directory) / "parameters.set"
        model.writeParams(str(source), comments=True, onlychanged=False)
        lines = source.read_text(encoding="utf-8").splitlines()

    metadata = re.compile(
        r"# \[type: (.*?), advanced: (TRUE|FALSE), "
        r"(?:range: (.*), )?default: (.*)\]$"
    )
    comments = []
    groups = defaultdict(list)
    seen = set()
    for line in lines[1:]:
        if not line:
            comments = []
            continue
        if line.startswith("#"):
            comments.append(line)
            continue
        name, separator, _ = line.partition(" = ")
        if not separator or not comments:
            raise ValueError(f"Unrecognized parameter record: {line!r}")
        match = metadata.fullmatch(comments[-1])
        if match is None or name in seen:
            raise ValueError(f"Missing or repeated parameter metadata: {name}")
        seen.add(name)
        kind, advanced, allowed, default = match.groups()
        allowed = allowed or "String; interpretation stated in description"
        description = " ".join(
            item.removeprefix("# ") for item in comments[:-1]
        )
        groups[name.split("/", 1)[0]].append(
            (name, kind, allowed, default, advanced, description)
        )
        comments = []
    if seen != set(model.getParams()):
        raise ValueError(
            "The documented catalogue does not cover all native parameters"
        )

    version = ".".join(
        str(value)
        for value in (
            model.getMajorVersion(),
            model.getMinorVersion(),
            model.getTechVersion(),
        )
    )
    output = [
        "# SCIP parameter catalogue",
        "",
        f"This catalogue covers all {len(seen):,} native parameters "
        f"in SCIP {version}. "
        "Pass values through `scip_params` as described in the "
        "[solver option reference](solver-options.md#scip-controls). "
        "The native build determines available plugins and parameter names; "
        "another installed build can have a different catalogue.",
        "",
        "Each row gives the native type, allowed range, default, "
        "advanced flag, "
        "and parameter description. `bool` maps to Python `bool`; `int` and "
        "`longint` to Python `int`; `real` to Python `float`; `char` to a "
        "one-character string; `string` to Python `str`. Character sets list "
        "allowed individual characters. Brackets give inclusive "
        "numeric endpoints. Special sentinels such as `-1` retain "
        "the meaning stated in the description. "
        "Defaults below are native defaults; Finance and CVXPY overrides are "
        "listed in the solver reference.",
        "",
        "Descriptions and metadata follow the installed solver's "
        "public parameter "
        "records. The [SCIP parameter documentation]"
        "(https://www.scipopt.org/doc/html/PARAMETERS.php) explains "
        "the native "
        "configuration model.",
        "",
    ]

    def escape(value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("|", "&#124;")
            .replace("`", "&#96;")
        )

    for group, records in sorted(groups.items()):
        output.extend(
            [
                f"## {group}",
                "",
                "| Parameter | Type | Allowed values | Default "
                "| Advanced | Meaning |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for name, kind, allowed, default, advanced, description in records:
            output.append(
                f"| `{name}` | `{kind}` | {escape(allowed)} | "
                f"{escape(default)} | {advanced.title()} | "
                f"{escape(description)} |"
            )
        output.append("")
    destination = Path(__file__).resolve().parents[2] / "scip-parameters.md"
    destination.write_text("\n".join(output), encoding="utf-8")
    print(f"Documented {len(seen)} SCIP {version} parameters")


if __name__ == "__main__":
    main()
