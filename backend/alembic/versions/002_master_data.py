"""create master data tables

Revision ID: 002_master_data
Revises: 001_auth
Create Date: 2024-01-02
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_master_data"
down_revision: Union[str, None] = "001_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
_uuid_default = sa.text("uuid_generate_v4()")
_now = sa.func.now()


def _base_cols():
    return [
        sa.Column("id", UUID, primary_key=True, server_default=_uuid_default),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_now, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_now, nullable=False),
    ]


def upgrade() -> None:
    # ── Enums ─────────────────────────────────────────────────────────────────
    enums = {
        "gender": ["male", "female", "other"],
        "employmenttype": ["permanent", "contract", "visiting", "adjunct"],
        "designation": ["professor", "associate_professor", "assistant_professor",
                        "lecturer", "hod", "dean", "director", "other"],
        "qualification": ["phd", "mtech", "me", "mba", "mphil", "mpharm", "btech", "be", "other"],
        "studentcategory": ["general", "obc", "sc", "st", "ews", "pwd"],
        "admissiontype": ["regular", "lateral", "nri", "management"],
        "programlevel": ["diploma", "ug", "pg", "phd", "certificate"],
        "publicationcategory": ["journal", "conference", "book", "book_chapter", "patent"],
        "indexingtype": ["scopus", "wos", "sci", "esci", "ugc_care", "other"],
        "patentstatus": ["filed", "published", "granted", "abandoned"],
        "placementtype": ["campus", "off_campus", "higher_studies", "entrepreneurship"],
        "fundingagency": ["dst", "dbt", "icmr", "ugc", "aicte", "csir",
                          "isro", "drdo", "industry", "international", "other"],
        "moutype": ["academic", "industry", "research", "international", "government"],
        "eventtype": ["conference", "workshop", "seminar", "fdp",
                      "webinar", "cultural", "sports", "other"],
        "wastetype": ["solid", "biomedical", "ewaste", "hazardous", "recyclable"],
    }
    bind = op.get_bind()
    for name, values in enums.items():
        postgresql.ENUM(*values, name=name).create(bind)

    # ── programs ──────────────────────────────────────────────────────────────
    op.create_table("programs",
        *_base_cols(),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("level", postgresql.ENUM("diploma","ug","pg","phd","certificate", name="programlevel", create_type=False), nullable=False),
        sa.Column("duration_years", sa.Integer, nullable=False),
        sa.Column("intake_sanctioned", sa.Integer, nullable=False, server_default="0"),
        sa.Column("intake_actual", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_nba_accredited", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("nba_valid_until", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.UniqueConstraint("code", "academic_year", name="uq_program_code_year"),
    )
    op.create_index("ix_programs_dept_year", "programs", ["department_id", "academic_year"])

    # ── faculty ───────────────────────────────────────────────────────────────
    op.create_table("faculty",
        *_base_cols(),
        sa.Column("employee_id", sa.String(50), nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("gender", postgresql.ENUM("male","female","other", name="gender", create_type=False), nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("aadhaar_last4", sa.String(4), nullable=True),
        sa.Column("designation", postgresql.ENUM("professor","associate_professor","assistant_professor","lecturer","hod","dean","director","other", name="designation", create_type=False), nullable=False),
        sa.Column("qualification", postgresql.ENUM("phd","mtech","me","mba","mphil","mpharm","btech","be","other", name="qualification", create_type=False), nullable=False),
        sa.Column("specialization", sa.String(255), nullable=True),
        sa.Column("phd_awarded", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("phd_year", sa.Integer, nullable=True),
        sa.Column("phd_university", sa.String(255), nullable=True),
        sa.Column("employment_type", postgresql.ENUM("permanent","contract","visiting","adjunct", name="employmenttype", create_type=False), nullable=False),
        sa.Column("date_of_joining", sa.Date, nullable=True),
        sa.Column("date_of_leaving", sa.Date, nullable=True),
        sa.Column("experience_teaching", sa.Float, nullable=False, server_default="0"),
        sa.Column("experience_industry", sa.Float, nullable=False, server_default="0"),
        sa.Column("experience_research", sa.Float, nullable=False, server_default="0"),
        sa.Column("is_sanctioned_post", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("pan_number", sa.String(10), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("remarks", sa.Text, nullable=True),
        sa.UniqueConstraint("employee_id", "academic_year", name="uq_faculty_emp_year"),
    )
    op.create_index("ix_faculty_dept_year", "faculty", ["department_id", "academic_year"])
    op.create_index("ix_faculty_email", "faculty", ["email"])

    # ── students ──────────────────────────────────────────────────────────────
    op.create_table("students",
        *_base_cols(),
        sa.Column("enrollment_no", sa.String(50), nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("program_id", UUID, sa.ForeignKey("programs.id"), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("gender", postgresql.ENUM("male","female","other", name="gender", create_type=False), nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("category", postgresql.ENUM("general","obc","sc","st","ews","pwd", name="studentcategory", create_type=False), nullable=False, server_default="general"),
        sa.Column("is_pwd", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("state_of_domicile", sa.String(100), nullable=True),
        sa.Column("admission_type", postgresql.ENUM("regular","lateral","nri","management", name="admissiontype", create_type=False), nullable=False, server_default="regular"),
        sa.Column("year_of_admission", sa.Integer, nullable=False),
        sa.Column("current_year", sa.Integer, nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("sgpa_last", sa.Float, nullable=True),
        sa.Column("cgpa", sa.Float, nullable=True),
        sa.Column("backlogs", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_lateral", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("remarks", sa.Text, nullable=True),
        sa.UniqueConstraint("enrollment_no", "academic_year", name="uq_student_enroll_year"),
    )
    op.create_index("ix_students_dept_year", "students", ["department_id", "academic_year"])

    # ── research_publications ─────────────────────────────────────────────────
    op.create_table("research_publications",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("category", postgresql.ENUM("journal","conference","book","book_chapter","patent", name="publicationcategory", create_type=False), nullable=False),
        sa.Column("journal_conference_name", sa.String(500), nullable=True),
        sa.Column("publisher", sa.String(255), nullable=True),
        sa.Column("publication_year", sa.Integer, nullable=False),
        sa.Column("publication_month", sa.Integer, nullable=True),
        sa.Column("volume", sa.String(20), nullable=True),
        sa.Column("issue", sa.String(20), nullable=True),
        sa.Column("pages", sa.String(30), nullable=True),
        sa.Column("doi", sa.String(255), nullable=True),
        sa.Column("isbn_issn", sa.String(50), nullable=True),
        sa.Column("scopus_id", sa.String(100), nullable=True),
        sa.Column("indexing", postgresql.ENUM("scopus","wos","sci","esci","ugc_care","other", name="indexingtype", create_type=False), nullable=False, server_default="other"),
        sa.Column("impact_factor", sa.Float, nullable=True),
        sa.Column("citations", sa.Integer, nullable=False, server_default="0"),
        sa.Column("h_index_contribution", sa.Integer, nullable=True),
        sa.Column("authors", sa.Text, nullable=False),
        sa.Column("faculty_employee_ids", sa.Text, nullable=True),
        sa.Column("sdg_goals", sa.Text, nullable=True),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("remarks", sa.Text, nullable=True),
    )
    op.create_index("ix_pub_dept_year", "research_publications", ["department_id", "academic_year"])
    op.create_index("ix_pub_doi", "research_publications", ["doi"])

    # ── patents ───────────────────────────────────────────────────────────────
    op.create_table("patents",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("application_number", sa.String(100), nullable=False),
        sa.Column("filing_date", sa.Date, nullable=True),
        sa.Column("grant_date", sa.Date, nullable=True),
        sa.Column("status", postgresql.ENUM("filed","published","granted","abandoned", name="patentstatus", create_type=False), nullable=False, server_default="filed"),
        sa.Column("inventors", sa.Text, nullable=False),
        sa.Column("faculty_employee_ids", sa.Text, nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="India"),
        sa.Column("patent_office", sa.String(255), nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── funded_projects ───────────────────────────────────────────────────────
    op.create_table("funded_projects",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("principal_investigator", sa.String(255), nullable=False),
        sa.Column("co_investigators", sa.Text, nullable=True),
        sa.Column("faculty_employee_ids", sa.Text, nullable=True),
        sa.Column("funding_agency", postgresql.ENUM("dst","dbt","icmr","ugc","aicte","csir","isro","drdo","industry","international","other", name="fundingagency", create_type=False), nullable=False),
        sa.Column("funding_agency_name", sa.String(255), nullable=True),
        sa.Column("scheme", sa.String(255), nullable=True),
        sa.Column("amount_sanctioned", sa.Float, nullable=False, server_default="0"),
        sa.Column("amount_received", sa.Float, nullable=False, server_default="0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="INR"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("is_ongoing", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("sdg_goals", sa.Text, nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── placements ────────────────────────────────────────────────────────────
    op.create_table("placements",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("program_id", UUID, sa.ForeignKey("programs.id"), nullable=True),
        sa.Column("student_name", sa.String(255), nullable=False),
        sa.Column("enrollment_no", sa.String(50), nullable=True),
        sa.Column("gender", postgresql.ENUM("male","female","other", name="gender", create_type=False), nullable=False),
        sa.Column("category", postgresql.ENUM("general","obc","sc","st","ews","pwd", name="studentcategory", create_type=False), nullable=False, server_default="general"),
        sa.Column("placement_type", postgresql.ENUM("campus","off_campus","higher_studies","entrepreneurship", name="placementtype", create_type=False), nullable=False, server_default="campus"),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("designation", sa.String(255), nullable=True),
        sa.Column("package_lpa", sa.Float, nullable=True),
        sa.Column("placement_date", sa.Date, nullable=True),
        sa.Column("company_city", sa.String(100), nullable=True),
        sa.Column("company_state", sa.String(100), nullable=True),
        sa.Column("is_international", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("remarks", sa.Text, nullable=True),
    )
    op.create_index("ix_placements_dept_year", "placements", ["department_id", "academic_year"])

    # ── higher_studies ────────────────────────────────────────────────────────
    op.create_table("higher_studies",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("program_id", UUID, sa.ForeignKey("programs.id"), nullable=True),
        sa.Column("student_name", sa.String(255), nullable=False),
        sa.Column("enrollment_no", sa.String(50), nullable=True),
        sa.Column("gender", postgresql.ENUM("male","female","other", name="gender", create_type=False), nullable=False),
        sa.Column("admitted_program", sa.String(255), nullable=False),
        sa.Column("admitted_institute", sa.String(255), nullable=False),
        sa.Column("admitted_university", sa.String(255), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="India"),
        sa.Column("entrance_exam", sa.String(100), nullable=True),
        sa.Column("entrance_score", sa.Float, nullable=True),
        sa.Column("scholarship_received", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("scholarship_amount", sa.Float, nullable=True),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── infrastructure ────────────────────────────────────────────────────────
    op.create_table("infrastructure",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("facility_type", sa.String(100), nullable=False),
        sa.Column("facility_name", sa.String(255), nullable=False),
        sa.Column("area_sqmt", sa.Float, nullable=True),
        sa.Column("capacity", sa.Integer, nullable=True),
        sa.Column("count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_lab", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("equipment_value", sa.Float, nullable=True),
        sa.Column("computers_count", sa.Integer, nullable=True),
        sa.Column("internet_speed_mbps", sa.Float, nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── budgets ───────────────────────────────────────────────────────────────
    op.create_table("budgets",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("head", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("sub_category", sa.String(100), nullable=True),
        sa.Column("amount_budgeted", sa.Float, nullable=False, server_default="0"),
        sa.Column("amount_actual", sa.Float, nullable=False, server_default="0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="INR"),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── mous ──────────────────────────────────────────────────────────────────
    op.create_table("mous",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("partner_name", sa.String(255), nullable=False),
        sa.Column("partner_country", sa.String(100), nullable=False, server_default="India"),
        sa.Column("partner_type", postgresql.ENUM("academic","industry","research","international","government", name="moutype", create_type=False), nullable=False),
        sa.Column("mou_type", sa.String(100), nullable=True),
        sa.Column("signed_date", sa.Date, nullable=True),
        sa.Column("valid_until", sa.Date, nullable=True),
        sa.Column("purpose", sa.Text, nullable=True),
        sa.Column("activities_conducted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("document_path", sa.String(500), nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── events ────────────────────────────────────────────────────────────────
    op.create_table("events",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("event_type", postgresql.ENUM("conference","workshop","seminar","fdp","webinar","cultural","sports","other", name="eventtype", create_type=False), nullable=False),
        sa.Column("is_organized", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("duration_days", sa.Integer, nullable=True),
        sa.Column("venue", sa.String(255), nullable=True),
        sa.Column("participants_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("faculty_participants", sa.Integer, nullable=False, server_default="0"),
        sa.Column("student_participants", sa.Integer, nullable=False, server_default="0"),
        sa.Column("external_participants", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_international", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("funding_amount", sa.Float, nullable=True),
        sa.Column("sdg_goals", sa.Text, nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── energy_consumption ────────────────────────────────────────────────────
    op.create_table("energy_consumption",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("month", sa.Integer, nullable=True),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("electricity_kwh", sa.Float, nullable=False, server_default="0"),
        sa.Column("electricity_cost_inr", sa.Float, nullable=True),
        sa.Column("solar_kwh", sa.Float, nullable=False, server_default="0"),
        sa.Column("wind_kwh", sa.Float, nullable=False, server_default="0"),
        sa.Column("other_renewable_kwh", sa.Float, nullable=False, server_default="0"),
        sa.Column("diesel_liters", sa.Float, nullable=False, server_default="0"),
        sa.Column("lpg_kg", sa.Float, nullable=False, server_default="0"),
        sa.Column("cng_kg", sa.Float, nullable=False, server_default="0"),
        sa.Column("ghg_scope1_tco2e", sa.Float, nullable=True),
        sa.Column("ghg_scope2_tco2e", sa.Float, nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── water_consumption ─────────────────────────────────────────────────────
    op.create_table("water_consumption",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("month", sa.Integer, nullable=True),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("municipal_kl", sa.Float, nullable=False, server_default="0"),
        sa.Column("borewell_kl", sa.Float, nullable=False, server_default="0"),
        sa.Column("rainwater_harvested_kl", sa.Float, nullable=False, server_default="0"),
        sa.Column("recycled_treated_kl", sa.Float, nullable=False, server_default="0"),
        sa.Column("cost_inr", sa.Float, nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── waste_management ──────────────────────────────────────────────────────
    op.create_table("waste_management",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("month", sa.Integer, nullable=True),
        sa.Column("waste_type", postgresql.ENUM("solid","biomedical","ewaste","hazardous","recyclable", name="wastetype", create_type=False), nullable=False),
        sa.Column("generated_kg", sa.Float, nullable=False, server_default="0"),
        sa.Column("recycled_kg", sa.Float, nullable=False, server_default="0"),
        sa.Column("disposed_kg", sa.Float, nullable=False, server_default="0"),
        sa.Column("disposal_method", sa.String(255), nullable=True),
        sa.Column("vendor_name", sa.String(255), nullable=True),
        sa.Column("cost_inr", sa.Float, nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── green_initiatives ─────────────────────────────────────────────────────
    op.create_table("green_initiatives",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("trees_planted", sa.Integer, nullable=True),
        sa.Column("area_covered_sqmt", sa.Float, nullable=True),
        sa.Column("investment_inr", sa.Float, nullable=True),
        sa.Column("sdg_goals", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── awards ────────────────────────────────────────────────────────────────
    op.create_table("awards",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("awarding_body", sa.String(255), nullable=False),
        sa.Column("recipient_name", sa.String(255), nullable=False),
        sa.Column("recipient_type", sa.String(50), nullable=False),
        sa.Column("award_date", sa.Date, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("is_national", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_international", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("prize_amount", sa.Float, nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── accreditations ────────────────────────────────────────────────────────
    op.create_table("accreditations",
        *_base_cols(),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("awarding_body", sa.String(255), nullable=False),
        sa.Column("program_department", sa.String(255), nullable=True),
        sa.Column("grade_score", sa.String(50), nullable=True),
        sa.Column("valid_from", sa.Date, nullable=True),
        sa.Column("valid_until", sa.Date, nullable=True),
        sa.Column("cycle", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("certificate_path", sa.String(500), nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── consultancies ─────────────────────────────────────────────────────────
    op.create_table("consultancies",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column("faculty_names", sa.Text, nullable=False),
        sa.Column("faculty_employee_ids", sa.Text, nullable=True),
        sa.Column("amount_inr", sa.Float, nullable=False, server_default="0"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("is_ongoing", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("remarks", sa.Text, nullable=True),
    )

    # ── sdg_activities ────────────────────────────────────────────────────────
    op.create_table("sdg_activities",
        *_base_cols(),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("activity_type", sa.String(100), nullable=False),
        sa.Column("sdg_primary", sa.Integer, nullable=False),
        sa.Column("sdg_secondary", sa.Text, nullable=True),
        sa.Column("beneficiaries_count", sa.Integer, nullable=True),
        sa.Column("investment_inr", sa.Float, nullable=True),
        sa.Column("outcome", sa.Text, nullable=True),
        sa.Column("evidence_path", sa.String(500), nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
    )
    op.create_index("ix_sdg_primary", "sdg_activities", ["sdg_primary"])


def downgrade() -> None:
    tables = [
        "sdg_activities", "consultancies", "accreditations", "awards",
        "green_initiatives", "waste_management", "water_consumption",
        "energy_consumption", "events", "mous", "budgets", "infrastructure",
        "higher_studies", "placements", "funded_projects", "patents",
        "research_publications", "students", "faculty", "programs",
    ]
    for t in tables:
        op.drop_table(t)

    enums = [
        "wastetype", "eventtype", "moutype", "fundingagency", "placementtype",
        "patentstatus", "indexingtype", "publicationcategory", "programlevel",
        "admissiontype", "studentcategory", "qualification", "designation",
        "employmenttype", "gender",
    ]
    bind = op.get_bind()
    for e in enums:
        postgresql.ENUM(name=e).drop(bind, checkfirst=True)
