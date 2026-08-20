"""
Excel Validation Engine
=======================
Reads an uploaded .xlsx/.xls/.csv file and validates every row.
"""
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.utils.column_maps import ColumnSpec, get_all_aliases, get_column_specs, get_natural_keys, get_required_fields

# Reserved header for the hidden identity column that ties an exported row
# back to its database record. Present in every export/template; recognized
# under a few common spellings in case someone renames the header.
RECORD_ID_ALIASES = {"record id", "recordid", "row id", "rowid", "id", "_id"}

# ── Value normalizers ─────────────────────────────────────────────────────────

GENDER_MAP = {
    "m": "male", "male": "male", "boy": "male",
    "f": "female", "female": "female", "girl": "female",
    "o": "other", "other": "other", "transgender": "other",
}

DESIGNATION_MAP = {
    "professor": "professor", "prof": "professor",
    "associate professor": "associate_professor",
    "assoc professor": "associate_professor",
    "assoc. professor": "associate_professor",
    "assistant professor": "assistant_professor",
    "asst professor": "assistant_professor",
    "asst. professor": "assistant_professor",
    "lecturer": "lecturer",
    "hod": "hod", "head": "hod", "head of department": "hod",
    "dean": "dean", "director": "director",
}

EMPLOYMENT_MAP = {
    "permanent": "permanent", "regular": "permanent", "full time": "permanent",
    "contract": "contract", "contractual": "contract",
    "visiting": "visiting", "guest": "visiting",
    "adjunct": "adjunct",
}

QUALIFICATION_MAP = {
    "ph.d": "phd", "ph.d.": "phd", "phd": "phd", "doctorate": "phd",
    "m.tech": "mtech", "mtech": "mtech",
    "m.e.": "me", "me": "me",
    "mba": "mba", "m.b.a": "mba",
    "m.phil": "mphil", "mphil": "mphil",
    "m.pharm": "mpharm", "mpharm": "mpharm",
    "b.tech": "btech", "btech": "btech",
    "b.e": "be", "be": "be",
}

CATEGORY_MAP = {
    "general": "general", "gen": "general", "open": "general",
    "obc": "obc", "other backward class": "obc",
    "sc": "sc", "scheduled caste": "sc",
    "st": "st", "scheduled tribe": "st",
    "ews": "ews",
    "pwd": "pwd", "physically handicapped": "pwd",
}

INDEXING_MAP = {
    "scopus": "scopus", "elsevier": "scopus",
    "wos": "wos", "web of science": "wos",
    "sci": "sci", "esci": "esci",
    "ugc": "ugc_care", "ugc care": "ugc_care", "ugc-care": "ugc_care",
    "other": "other",
}

PATENT_STATUS_MAP = {
    "filed": "filed", "application filed": "filed",
    "published": "published",
    "granted": "granted", "grant": "granted",
    "abandoned": "abandoned", "lapsed": "abandoned",
}

PLACEMENT_TYPE_MAP = {
    "campus": "campus", "campus placement": "campus",
    "off campus": "off_campus", "off-campus": "off_campus",
    "higher studies": "higher_studies", "higher education": "higher_studies",
    "entrepreneurship": "entrepreneurship", "self employed": "entrepreneurship",
}

EVENT_TYPE_MAP = {
    "conference": "conference", "workshop": "workshop",
    "seminar": "seminar", "fdp": "fdp", "faculty development": "fdp",
    "webinar": "webinar", "online": "webinar",
    "cultural": "cultural", "sports": "sports", "other": "other",
}

MOU_TYPE_MAP = {
    "academic": "academic", "university": "academic",
    "industry": "industry", "company": "industry",
    "research": "research", "r&d": "research",
    "international": "international",
    "government": "government", "govt": "government",
}

PUBLICATION_TYPE_MAP = {
    "journal": "journal", "journal article": "journal",
    "conference": "conference", "conference paper": "conference",
    "book": "book",
    "book chapter": "book_chapter", "chapter": "book_chapter",
    "patent": "patent",
}

VALUE_MAPS: dict[str, dict] = {
    "gender": GENDER_MAP,
    "designation": DESIGNATION_MAP,
    "employment_type": EMPLOYMENT_MAP,
    "qualification": QUALIFICATION_MAP,
    "category": CATEGORY_MAP,
    "indexing": INDEXING_MAP,
    "status": PATENT_STATUS_MAP,
    "placement_type": PLACEMENT_TYPE_MAP,
    "event_type": EVENT_TYPE_MAP,
    "partner_type": MOU_TYPE_MAP,
    "category_pub": PUBLICATION_TYPE_MAP,
}


@dataclass
class RowError:
    row: int
    field: str
    value: Any
    error: str


@dataclass
class ValidationResult:
    valid_rows: list[dict] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)
    column_mapping: dict[str, str] = field(default_factory=dict)
    total_rows: int = 0
    skipped_rows: int = 0


class ExcelValidator:
    def __init__(self, entity_type: str, academic_year: str, mode: str = "insert"):
        self.entity_type = entity_type
        self.academic_year = academic_year
        self.mode = mode
        self.specs = get_column_specs(entity_type)
        self.aliases = get_all_aliases(entity_type)
        self.required = get_required_fields(entity_type)
        self.natural_keys = get_natural_keys(entity_type)

        # In "update" mode, only the natural key(s) (e.g. enrollment_no) are
        # required — every other column becomes optional, so a file containing
        # just the key plus (say) CGPA validates and updates only that field.
        # Entities with no registered natural key fall back to normal behavior.
        if self.mode == "update" and self.natural_keys:
            self.effective_required = self.natural_keys
        else:
            self.effective_required = self.required

    def validate(self, file_path: str) -> ValidationResult:
        result = ValidationResult()
        try:
            df = self._read_file(file_path)
        except Exception as e:
            raise ValueError(f"Cannot read file: {e}")

        df, mapping = self._normalise_headers(df)
        result.column_mapping = mapping

        missing = [r for r in self.effective_required if r not in df.columns]
        if missing:
            raise ValueError(
                f"Required columns missing: {', '.join(missing)}. "
                f"Found columns: {', '.join(df.columns.tolist())}"
            )

        df = df.dropna(how="all")
        result.total_rows = len(df)

        for idx, row in df.iterrows():
            row_num = int(idx) + 2
            row_errors: list[RowError] = []
            clean: dict[str, Any] = {"academic_year": self.academic_year}

            # Carry the Record ID straight through, no validation — it's an
            # internal identity marker, not user-entered data. A malformed
            # or stray value is handled downstream (treated as a new row),
            # never as a validation error the operator has to fix.
            record_id_raw = row.get("_record_id")
            if record_id_raw is not None and str(record_id_raw).strip() not in ("", "nan", "NaN", "None"):
                clean["_record_id"] = str(record_id_raw).strip()

            for spec in self.specs:
                if spec.db_field not in df.columns:
                    continue
                raw = row.get(spec.db_field)
                try:
                    value = self._coerce(spec, raw, row_num)
                    if value is not None:
                        clean[spec.db_field] = value
                    elif spec.db_field in self.effective_required:
                        row_errors.append(RowError(row_num, spec.db_field, raw, "Required field is empty"))
                except ValueError as e:
                    row_errors.append(RowError(row_num, spec.db_field, raw, str(e)))

            if row_errors:
                result.errors.extend(row_errors)
                result.skipped_rows += 1
            else:
                result.valid_rows.append(clean)

        return result

    def _read_file(self, file_path: str) -> pd.DataFrame:
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix in (".xlsx", ".xlsm"):
            df = pd.read_excel(file_path, engine="openpyxl", dtype=str)
        elif suffix == ".xls":
            df = pd.read_excel(file_path, engine="xlrd", dtype=str)
        elif suffix == ".csv":
            df = pd.read_csv(file_path, dtype=str, encoding="utf-8-sig")
        else:
            raise ValueError(f"Unsupported file type: {suffix}. Use .xlsx, .xls, or .csv")

        # Safe string stripping — works on all pandas versions
        for col in df.columns:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        return df

    def _normalise_headers(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        mapping: dict[str, str] = {}
        rename: dict[str, str] = {}
        for col in df.columns:
            normalised = str(col).lower().strip().replace("\n", " ").replace("  ", " ")
            normalised = normalised.rstrip("*").strip()
            if normalised in RECORD_ID_ALIASES:
                rename[col] = "_record_id"
                mapping[col] = "_record_id"
            elif normalised in self.aliases:
                db_field = self.aliases[normalised]
                rename[col] = db_field
                mapping[col] = db_field
        df = df.rename(columns=rename)
        return df, mapping

    def _coerce(self, spec: ColumnSpec, raw: Any, row_num: int) -> Any:
        if raw is None or (isinstance(raw, float) and pd.isna(raw)) or str(raw).strip() in ("", "nan", "NaN", "None"):
            return None

        value = str(raw).strip()

        if spec.dtype == "str":
            return self._apply_value_map(spec.db_field, value)
        elif spec.dtype == "int":
            try:
                return int(float(value))
            except (ValueError, TypeError):
                raise ValueError(f"Expected a whole number, got '{value}'")
        elif spec.dtype == "float":
            try:
                return float(value.replace(",", ""))
            except (ValueError, TypeError):
                raise ValueError(f"Expected a number, got '{value}'")
        elif spec.dtype == "bool":
            return value.lower() in ("yes", "true", "1", "y", "✓")
        elif spec.dtype == "date":
            return self._parse_date(value)
        elif spec.dtype == "email":
            if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", value):
                raise ValueError(f"'{value}' is not a valid email address")
            return value.lower()
        elif spec.dtype == "year":
            try:
                yr = int(float(value))
                if not (1900 <= yr <= 2100):
                    raise ValueError
                return yr
            except (ValueError, TypeError):
                raise ValueError(f"Expected a 4-digit year, got '{value}'")
        return value

    def _apply_value_map(self, field: str, value: str) -> str:
        vmap = VALUE_MAPS.get(field)
        if not vmap:
            return value
        normalised = value.lower().strip()
        mapped = vmap.get(normalised)
        if mapped:
            return mapped
        for k, v in vmap.items():
            if k in normalised or normalised in k:
                return v
        return value

    def _parse_date(self, value: str) -> date | None:
        formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
            "%d/%m/%y", "%d-%m-%y", "%Y/%m/%d",
            "%m/%d/%Y", "%d %b %Y", "%d %B %Y",
            "%b %d, %Y", "%B %d, %Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date '{value}'. Use DD/MM/YYYY format.")
