"""
Module 9 — Excel Auto-Fill
============================
Builds the flat {{token}} -> value vocabulary that templates can use.
Reuses the exact same aggregation queries as Module 8's report generator
(app/utils/report_data.py) so both features report identical numbers —
there's only one source of truth for "how many faculty" etc.

A token like {{nirf.faculty_total}} in an uploaded template cell gets
replaced with the corresponding value. Only scalar leaves are exposed as
tokens; list-of-dict sections (e.g. faculty_by_department) aren't
individually addressable — those are better suited to Module 8's report
tables directly.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import report_data


def _flatten(prefix: str, value, out: dict[str, object]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            _flatten(f"{prefix}.{k}", v, out)
    elif isinstance(value, list):
        # Lists (e.g. faculty_by_department) aren't flattened into individual
        # tokens — expose only a count, which is still useful in a template.
        out[f"{prefix}_count"] = len(value)
    else:
        out[prefix] = value


async def build_token_registry(db: AsyncSession, academic_year: str | None) -> dict[str, object]:
    """Returns a flat dict of every available {{token}} -> current value."""
    nirf = await report_data.get_nirf_data(db, academic_year)
    naac = await report_data.get_naac_data(db, academic_year)
    aishe = await report_data.get_aishe_data(db, academic_year)

    tokens: dict[str, object] = {}
    _flatten("nirf", nirf, tokens)
    _flatten("naac", naac, tokens)
    _flatten("aishe", aishe, tokens)
    tokens["academic_year"] = academic_year or "All years"
    return tokens


def describe_tokens(tokens: dict[str, object]) -> list[dict]:
    """Turns the flat token dict into a reference list for the frontend (name + sample value)."""
    return [
        {"token": f"{{{{{name}}}}}", "sample_value": value, "group": name.split(".")[0]}
        for name, value in sorted(tokens.items())
    ]
