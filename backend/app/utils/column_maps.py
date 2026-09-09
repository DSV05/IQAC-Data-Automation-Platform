"""
Column Mappings
===============
Maps Excel column headers → database field names for each entity type.

Each entity has:
  - REQUIRED_COLS: columns that must be present (upload fails if missing)
  - OPTIONAL_COLS: nice-to-have columns
  - ALIASES: common alternative spellings (case-insensitive)

The validator normalises all incoming column names against these mappings.
"""
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ColumnSpec:
    db_field: str
    dtype: str          # "str", "int", "float", "date", "bool", "email", "year"
    required: bool = True
    aliases: list[str] = field(default_factory=list)
    validator: Callable | None = None


# ── Faculty ───────────────────────────────────────────────────────────────────

FACULTY_COLUMNS: list[ColumnSpec] = [
    # Virtual import field: resolved to department_id by UploadService.
    ColumnSpec("department",         "str",   False, ["department", "department name", "department code"]),
    ColumnSpec("employee_id",        "str",   True,  ["emp id", "employee id", "emp_id", "staff id", "faculty id"]),
    ColumnSpec("full_name",          "str",   True,  ["name", "faculty name", "teacher name"]),
    ColumnSpec("institute",          "str",   False, ["institute name", "school", "campus"]),
    ColumnSpec("gender",             "str",   True,  ["sex", "gender"]),
    ColumnSpec("designation",        "str",   True,  ["post", "designation", "position", "role"]),
    ColumnSpec("qualification",      "str",   True,  ["highest qualification", "qual", "degree"]),
    ColumnSpec("employment_type",    "str",   True,  ["employment type", "type", "emp type", "contract type"]),
    ColumnSpec("experience_teaching","float", True,  ["teaching exp", "teaching experience", "exp teaching", "t exp"]),
    ColumnSpec("email",              "email", False, ["email id", "email address", "mail"]),
    ColumnSpec("phone",              "str",   False, ["phone", "mobile", "contact", "phone no"]),
    ColumnSpec("date_of_joining",    "date",  False, ["doj", "joining date", "date of joining"]),
    ColumnSpec("date_of_leaving",    "date",  False, ["dol", "leaving date", "date of leaving"]),
    ColumnSpec("date_of_birth",      "date",  False, ["dob", "birth date", "date of birth"]),
    ColumnSpec("specialization",     "str",   False, ["specialization", "specialisation", "subject"]),
    ColumnSpec("phd_awarded",        "bool",  False, ["phd", "ph.d", "phd awarded", "has phd"]),
    ColumnSpec("phd_year",           "int",   False, ["phd year", "year of phd"]),
    ColumnSpec("experience_industry","float", False, ["industry exp", "industry experience"]),
    ColumnSpec("experience_research","float", False, ["research exp", "research experience"]),
    ColumnSpec("pan_number",         "str",   False, ["pan", "pan no", "pan number"]),
]

# ── Students ──────────────────────────────────────────────────────────────────

STUDENT_COLUMNS: list[ColumnSpec] = [
    # Virtual import fields: resolved to department_id/program_id by UploadService.
    ColumnSpec("department",      "str",  False, ["department", "department name", "department code"]),
    ColumnSpec("program",         "str",  False, ["program", "program name", "program code"]),
    ColumnSpec("enrollment_no",   "str",  True,  ["enrollment", "enroll no", "roll no", "student id", "gr no"]),
    ColumnSpec("full_name",       "str",  True,  ["name", "student name"]),
    ColumnSpec("gender",          "str",  True,  ["sex", "gender"]),
    ColumnSpec("year_of_admission","int", True,  ["admission year", "year of joining", "batch"]),
    ColumnSpec("current_year",    "int",  True,  ["year", "current year", "sem year", "class"]),
    ColumnSpec("category",        "str",  False, ["caste", "category", "reservation"]),
    ColumnSpec("admission_type",  "str",  False, ["admission type", "type", "quota"]),
    ColumnSpec("email",           "email",False, ["email", "email id"]),
    ColumnSpec("phone",           "str",  False, ["phone", "mobile", "contact"]),
    ColumnSpec("date_of_birth",   "date", False, ["dob", "birth date"]),
    ColumnSpec("cgpa",            "float",False, ["cgpa", "gpa", "cpi"]),
    ColumnSpec("sgpa_last",       "float",False, ["sgpa", "last sem gpa", "last sgpa"]),
    ColumnSpec("state_of_domicile","str", False, ["state", "home state"]),
    ColumnSpec("is_pwd",          "bool", False, ["pwd", "handicapped", "differently abled"]),
    ColumnSpec("backlogs",        "int",  False, ["backlog", "backlogs", "no of backlogs", "arrears"]),
]

# ── Research Publications ─────────────────────────────────────────────────────

RESEARCH_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("department",     "str",   False, ["department", "department name", "department code"]),
    ColumnSpec("title",          "str",   True,  ["paper title", "title of paper", "publication title"]),
    ColumnSpec("authors",        "str",   True,  ["authors", "author names", "co-authors"]),
    ColumnSpec("category",       "str",   True,  ["type", "publication type", "paper type"]),
    ColumnSpec("publication_year","int",  True,  ["year", "pub year", "year of publication"]),
    ColumnSpec("indexing",       "str",   True,  ["indexed in", "index", "database"]),
    ColumnSpec("journal_conference_name","str", False, ["journal", "journal name", "conference", "venue"]),
    ColumnSpec("doi",            "str",   False, ["doi", "doi number"]),
    ColumnSpec("impact_factor",  "float", False, ["if", "impact factor", "sjr"]),
    ColumnSpec("citations",      "int",   False, ["citations", "cited by", "no of citations"]),
    ColumnSpec("isbn_issn",      "str",   False, ["isbn", "issn", "isbn/issn"]),
    ColumnSpec("publisher",      "str",   False, ["publisher", "published by"]),
]

# ── Patents ───────────────────────────────────────────────────────────────────

PATENT_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("department",          "str",  False, ["department", "department name", "department code"]),
    ColumnSpec("title",              "str",  True,  ["patent title", "title of invention"]),
    ColumnSpec("application_number", "str",  True,  ["application no", "app no", "patent no"]),
    ColumnSpec("inventors",          "str",  True,  ["inventors", "inventor names"]),
    ColumnSpec("status",             "str",  True,  ["status", "patent status", "current status"]),
    ColumnSpec("filing_date",        "date", False, ["filing date", "date of filing", "filed on"]),
    ColumnSpec("grant_date",         "date", False, ["grant date", "granted on", "date of grant"]),
    ColumnSpec("country",            "str",  False, ["country", "patent country"]),
]

# ── Placements ────────────────────────────────────────────────────────────────

PLACEMENT_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("department",     "str",   False, ["department", "department name", "department code"]),
    ColumnSpec("student_name",    "str",   True,  ["name", "student name"]),
    ColumnSpec("gender",          "str",   True,  ["sex", "gender"]),
    ColumnSpec("placement_type",  "str",   True,  ["type", "placement type"]),
    ColumnSpec("company_name",    "str",   False, ["company", "employer", "organization"]),
    ColumnSpec("designation",     "str",   False, ["role", "position", "designation", "job title"]),
    ColumnSpec("package_lpa",     "float", False, ["package", "ctc", "salary", "lpa", "package lpa"]),
    ColumnSpec("enrollment_no",   "str",   False, ["enrollment", "enroll no", "roll no"]),
    ColumnSpec("placement_date",  "date",  False, ["date", "placement date", "joining date"]),
    ColumnSpec("company_city",    "str",   False, ["city", "location", "company city"]),
    ColumnSpec("company_state",   "str",   False, ["state", "company state"]),
    ColumnSpec("category",        "str",   False, ["category", "caste"]),
]

# ── NIRF sponsored research / consultancy ────────────────────────────────────

FUNDED_PROJECT_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("department", "str", False, ["department", "department name", "department code"]),
    ColumnSpec("title", "str", True, ["project title", "title"]),
    ColumnSpec("principal_investigator", "str", True, ["pi", "principal investigator"]),
    ColumnSpec("funding_agency", "str", True, ["agency", "funding agency"]),
    ColumnSpec("funding_agency_name", "str", False, ["agency name", "funding agency name"]),
    ColumnSpec("scheme", "str", False, ["scheme"]),
    ColumnSpec("amount_sanctioned", "float", False, ["sanctioned amount"]),
    ColumnSpec("amount_received", "float", False, ["amount received", "received amount"]),
    ColumnSpec("start_date", "date", False, ["start date"]),
    ColumnSpec("end_date", "date", False, ["end date"]),
    ColumnSpec("is_ongoing", "bool", False, ["ongoing", "is ongoing"]),
]

CONSULTANCY_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("department", "str", False, ["department", "department name", "department code"]),
    ColumnSpec("title", "str", True, ["consultancy title", "title"]),
    ColumnSpec("client_name", "str", True, ["client", "client organization", "client name"]),
    ColumnSpec("faculty_names", "str", True, ["faculty", "faculty names", "consultant names"]),
    ColumnSpec("amount_inr", "float", False, ["amount received", "amount", "amount inr"]),
    ColumnSpec("start_date", "date", False, ["start date"]),
    ColumnSpec("end_date", "date", False, ["end date"]),
    ColumnSpec("is_ongoing", "bool", False, ["ongoing", "is ongoing"]),
]

# ── Energy ────────────────────────────────────────────────────────────────────

ENERGY_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("electricity_kwh",      "float", True,  ["electricity", "grid kwh", "units consumed", "electricity kwh"]),
    ColumnSpec("solar_kwh",            "float", False, ["solar", "solar kwh", "solar units"]),
    ColumnSpec("diesel_liters",        "float", False, ["diesel", "diesel liters", "hsd"]),
    ColumnSpec("month",                "int",   False, ["month", "month no"]),
    ColumnSpec("electricity_cost_inr", "float", False, ["electricity cost", "bill amount", "cost inr"]),
    ColumnSpec("lpg_kg",               "float", False, ["lpg", "lpg kg"]),
    ColumnSpec("ghg_scope1_tco2e",     "float", False, ["scope 1", "ghg scope1", "tco2e scope1"]),
    ColumnSpec("ghg_scope2_tco2e",     "float", False, ["scope 2", "ghg scope2", "tco2e scope2"]),
]

# ── MoUs ──────────────────────────────────────────────────────────────────────

MOU_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("partner_name",    "str",  True,  ["partner", "organization", "institution", "company"]),
    ColumnSpec("partner_type",    "str",  True,  ["type", "mou type", "partner type"]),
    ColumnSpec("partner_country", "str",  False, ["country"]),
    ColumnSpec("signed_date",     "date", False, ["date", "signed date", "mou date"]),
    ColumnSpec("valid_until",     "date", False, ["valid until", "expiry date", "validity"]),
    ColumnSpec("purpose",         "str",  False, ["purpose", "objective", "activities"]),
]

# ── Events ────────────────────────────────────────────────────────────────────

EVENT_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("title",                 "str",  True,  ["title", "event name", "program name"]),
    ColumnSpec("event_type",            "str",  True,  ["type", "event type", "category"]),
    ColumnSpec("participants_count",    "int",  False, ["participants", "total participants", "count"]),
    ColumnSpec("start_date",            "date", False, ["date", "start date", "from date"]),
    ColumnSpec("end_date",              "date", False, ["end date", "to date"]),
    ColumnSpec("duration_days",         "int",  False, ["duration", "days", "no of days"]),
    ColumnSpec("venue",                 "str",  False, ["venue", "place", "location"]),
    ColumnSpec("faculty_participants",  "int",  False, ["faculty count", "faculty participants"]),
    ColumnSpec("student_participants",  "int",  False, ["student count", "student participants"]),
]

# ── Water ─────────────────────────────────────────────────────────────────────

WATER_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("municipal_kl",           "float", False, ["municipal", "municipal water", "municipal kl"]),
    ColumnSpec("borewell_kl",            "float", False, ["borewell", "borewell water", "groundwater"]),
    ColumnSpec("rainwater_harvested_kl", "float", False, ["rainwater", "rainwater harvested", "rwh"]),
    ColumnSpec("recycled_treated_kl",    "float", False, ["recycled", "treated water", "recycled treated"]),
    ColumnSpec("month",                  "int",   False, ["month", "month no"]),
    ColumnSpec("cost_inr",               "float", False, ["cost", "water cost", "cost inr"]),
]

# ── Waste ─────────────────────────────────────────────────────────────────────

WASTE_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("waste_type",       "str",   True,  ["waste type", "type", "category"]),
    ColumnSpec("generated_kg",     "float", False, ["generated", "generated kg", "quantity generated"]),
    ColumnSpec("recycled_kg",      "float", False, ["recycled", "recycled kg"]),
    ColumnSpec("disposed_kg",      "float", False, ["disposed", "disposed kg"]),
    ColumnSpec("disposal_method",  "str",   False, ["disposal method", "method"]),
    ColumnSpec("vendor_name",      "str",   False, ["vendor", "vendor name", "agency"]),
    ColumnSpec("month",            "int",   False, ["month", "month no"]),
    ColumnSpec("cost_inr",         "float", False, ["cost", "cost inr"]),
]

# ── Awards ────────────────────────────────────────────────────────────────────

AWARD_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("recipient_name",  "str",   True,  ["recipient", "recipient name", "name"]),
    ColumnSpec("recipient_type",  "str",   True,  ["recipient type", "type"]),
    ColumnSpec("title",           "str",   True,  ["award", "award title", "title"]),
    ColumnSpec("awarding_body",   "str",   True,  ["awarding body", "given by", "agency"]),
    ColumnSpec("award_date",      "date",  False, ["date", "award date"]),
    ColumnSpec("category",        "str",   False, ["category"]),
    ColumnSpec("is_international","bool",  False, ["international", "is international"]),
    ColumnSpec("prize_amount",    "float", False, ["prize amount", "prize money", "amount"]),
]

# ── SDG Activities ────────────────────────────────────────────────────────────

SDG_COLUMNS: list[ColumnSpec] = [
    ColumnSpec("title",               "str",   True,  ["activity", "activity title", "title"]),
    ColumnSpec("sdg_primary",         "int",   True,  ["sdg", "sdg goal", "primary sdg"]),
    ColumnSpec("activity_type",       "str",   True,  ["type", "activity type"]),
    ColumnSpec("description",         "str",   False, ["description", "details"]),
    ColumnSpec("beneficiaries_count", "int",   False, ["beneficiaries", "beneficiaries count"]),
    ColumnSpec("investment_inr",      "float", False, ["investment", "investment inr", "amount"]),
    ColumnSpec("outcome",             "str",   False, ["outcome", "impact"]),
]

# ── Registry: entity type → column spec list ──────────────────────────────────

ENTITY_COLUMNS: dict[str, list[ColumnSpec]] = {
    "faculty":        FACULTY_COLUMNS,
    "students":       STUDENT_COLUMNS,
    "research":       RESEARCH_COLUMNS,
    "patents":        PATENT_COLUMNS,
    "placements":     PLACEMENT_COLUMNS,
    "funded_projects": FUNDED_PROJECT_COLUMNS,
    "consultancy":    CONSULTANCY_COLUMNS,
    "energy":         ENERGY_COLUMNS,
    "mous":           MOU_COLUMNS,
    "events":         EVENT_COLUMNS,
    "water":          WATER_COLUMNS,
    "waste":          WASTE_COLUMNS,
    "awards":         AWARD_COLUMNS,
    "sdg_activities": SDG_COLUMNS,
}

def get_column_specs(entity_type: str) -> list[ColumnSpec]:
    return ENTITY_COLUMNS.get(entity_type, [])

def get_required_fields(entity_type: str) -> list[str]:
    return [c.db_field for c in get_column_specs(entity_type) if c.required]


# ── Natural keys (Update Mode) ────────────────────────────────────────────────
# When uploading in "update" mode, only these fields are required — everything
# else in the template becomes optional, and only the columns actually present
# get updated on the matching existing record. Entities not listed here don't
# support Update Mode yet and behave exactly as they did before.
NATURAL_KEYS: dict[str, list[str]] = {
    "faculty": ["employee_id"],
    "students": ["enrollment_no"],
}


def get_natural_keys(entity_type: str) -> list[str]:
    return NATURAL_KEYS.get(entity_type, [])

def get_all_aliases(entity_type: str) -> dict[str, str]:
    """Returns lowercase_alias → db_field mapping for header normalisation."""
    mapping: dict[str, str] = {}
    for spec in get_column_specs(entity_type):
        mapping[spec.db_field.lower()] = spec.db_field
        mapping[spec.db_field.replace("_", " ").lower()] = spec.db_field
        for alias in spec.aliases:
            mapping[alias.lower()] = spec.db_field
    return mapping
