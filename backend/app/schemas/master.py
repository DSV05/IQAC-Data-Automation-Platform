"""
Pydantic schemas for all master data entities.
Each entity has: Base → Create → Update → Read pattern.
"""
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.enums import (
    AdmissionType, Designation, EmploymentType, EventType,
    FundingAgency, Gender, IndexingType, MoUType, PatentStatus,
    PlacementType, ProgramLevel, PublicationCategory, Qualification,
    StudentCategory, WasteType,
)


# ── Shared ────────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    page: int
    size: int
    pages: int


# ── Faculty ───────────────────────────────────────────────────────────────────

class FacultyBase(BaseModel):
    employee_id: str = Field(..., max_length=50)
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    department_id: uuid.UUID
    full_name: str = Field(..., max_length=255)
    institute: Optional[str] = Field(None, max_length=255)
    gender: Gender
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    designation: Designation
    qualification: Qualification
    specialization: Optional[str] = None
    phd_awarded: bool = False
    phd_year: Optional[int] = None
    phd_university: Optional[str] = None
    employment_type: EmploymentType
    date_of_joining: Optional[date] = None
    date_of_leaving: Optional[date] = None
    experience_teaching: float = 0.0
    experience_industry: float = 0.0
    experience_research: float = 0.0
    is_sanctioned_post: bool = True
    is_active: bool = True
    pan_number: Optional[str] = None
    remarks: Optional[str] = None


class FacultyCreate(FacultyBase):
    pass


class FacultyUpdate(BaseModel):
    department_id: Optional[uuid.UUID] = None
    full_name: Optional[str] = None
    institute: Optional[str] = Field(None, max_length=255)
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[Designation] = None
    qualification: Optional[Qualification] = None
    specialization: Optional[str] = None
    phd_awarded: Optional[bool] = None
    phd_year: Optional[int] = None
    phd_university: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    date_of_joining: Optional[date] = None
    date_of_leaving: Optional[date] = None
    experience_teaching: Optional[float] = None
    experience_industry: Optional[float] = None
    experience_research: Optional[float] = None
    is_sanctioned_post: Optional[bool] = None
    is_active: Optional[bool] = None
    pan_number: Optional[str] = None
    remarks: Optional[str] = None


class FacultyRead(FacultyBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PaginatedFaculty(PaginatedResponse):
    items: list[FacultyRead]


# ── Programs ──────────────────────────────────────────────────────────────────

class ProgramBase(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=255)
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    department_id: uuid.UUID
    level: ProgramLevel
    duration_years: int = Field(..., ge=1, le=7)
    intake_sanctioned: int = Field(0, ge=0)
    intake_actual: int = Field(0, ge=0)
    is_nba_accredited: bool = False
    nba_valid_until: Optional[date] = None
    is_active: bool = True


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(BaseModel):
    intake_sanctioned: Optional[int] = None
    intake_actual: Optional[int] = None
    is_nba_accredited: Optional[bool] = None
    nba_valid_until: Optional[date] = None
    is_active: Optional[bool] = None


class ProgramRead(ProgramBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Students ──────────────────────────────────────────────────────────────────

class StudentBase(BaseModel):
    enrollment_no: str = Field(..., max_length=50)
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    program_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    full_name: str = Field(..., max_length=255)
    gender: Gender
    date_of_birth: Optional[date] = None
    category: StudentCategory = StudentCategory.GENERAL
    is_pwd: bool = False
    state_of_domicile: Optional[str] = None
    admission_type: AdmissionType = AdmissionType.REGULAR
    year_of_admission: int
    current_year: int = Field(..., ge=1, le=7)
    email: Optional[str] = None
    phone: Optional[str] = None
    sgpa_last: Optional[float] = None
    cgpa: Optional[float] = None
    backlogs: int = 0
    is_lateral: bool = False
    is_active: bool = True
    remarks: Optional[str] = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    department_id: Optional[uuid.UUID] = None
    full_name: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    category: Optional[StudentCategory] = None
    is_pwd: Optional[bool] = None
    state_of_domicile: Optional[str] = None
    admission_type: Optional[AdmissionType] = None
    current_year: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    sgpa_last: Optional[float] = None
    cgpa: Optional[float] = None
    backlogs: Optional[int] = None
    is_lateral: Optional[bool] = None
    is_active: Optional[bool] = None
    remarks: Optional[str] = None


class StudentRead(StudentBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedStudents(PaginatedResponse):
    items: list[StudentRead]


# ── Research ──────────────────────────────────────────────────────────────────

class ResearchPublicationBase(BaseModel):
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    department_id: uuid.UUID
    title: str
    category: PublicationCategory
    journal_conference_name: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: int
    publication_month: Optional[int] = Field(None, ge=1, le=12)
    doi: Optional[str] = None
    isbn_issn: Optional[str] = None
    scopus_id: Optional[str] = None
    indexing: IndexingType = IndexingType.OTHER
    impact_factor: Optional[float] = None
    citations: int = 0
    authors: str
    faculty_employee_ids: Optional[str] = None
    sdg_goals: Optional[str] = None
    is_verified: bool = False
    remarks: Optional[str] = None


class ResearchPublicationCreate(ResearchPublicationBase):
    pass


class ResearchPublicationUpdate(BaseModel):
    department_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    category: Optional[PublicationCategory] = None
    journal_conference_name: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    publication_month: Optional[int] = Field(None, ge=1, le=12)
    doi: Optional[str] = None
    isbn_issn: Optional[str] = None
    scopus_id: Optional[str] = None
    indexing: Optional[IndexingType] = None
    impact_factor: Optional[float] = None
    citations: Optional[int] = None
    authors: Optional[str] = None
    is_verified: Optional[bool] = None
    remarks: Optional[str] = None


class ResearchPublicationRead(ResearchPublicationBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedResearch(PaginatedResponse):
    items: list[ResearchPublicationRead]


# ── Patents ───────────────────────────────────────────────────────────────────

class PatentBase(BaseModel):
    academic_year: str
    department_id: uuid.UUID
    title: str
    application_number: str
    filing_date: Optional[date] = None
    grant_date: Optional[date] = None
    status: PatentStatus = PatentStatus.FILED
    inventors: str
    faculty_employee_ids: Optional[str] = None
    country: str = "India"
    patent_office: Optional[str] = None
    remarks: Optional[str] = None


class PatentCreate(PatentBase):
    pass


class PatentUpdate(BaseModel):
    department_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    filing_date: Optional[date] = None
    grant_date: Optional[date] = None
    status: Optional[PatentStatus] = None
    inventors: Optional[str] = None
    country: Optional[str] = None
    patent_office: Optional[str] = None
    remarks: Optional[str] = None


class PatentRead(PatentBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedPatents(PaginatedResponse):
    items: list[PatentRead]


# ── Funded Projects ───────────────────────────────────────────────────────────

class FundedProjectBase(BaseModel):
    academic_year: str
    department_id: uuid.UUID
    title: str
    principal_investigator: str
    co_investigators: Optional[str] = None
    faculty_employee_ids: Optional[str] = None
    funding_agency: FundingAgency
    funding_agency_name: Optional[str] = None
    scheme: Optional[str] = None
    amount_sanctioned: float = 0.0
    amount_received: float = 0.0
    currency: str = "INR"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_ongoing: bool = True
    sdg_goals: Optional[str] = None
    remarks: Optional[str] = None


class FundedProjectCreate(FundedProjectBase):
    pass


class FundedProjectUpdate(BaseModel):
    amount_received: Optional[float] = None
    is_ongoing: Optional[bool] = None
    end_date: Optional[date] = None
    remarks: Optional[str] = None


class FundedProjectRead(FundedProjectBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedProjects(PaginatedResponse):
    items: list[FundedProjectRead]


# ── Placements ────────────────────────────────────────────────────────────────

class PlacementBase(BaseModel):
    academic_year: str
    department_id: uuid.UUID
    program_id: Optional[uuid.UUID] = None
    student_name: str
    enrollment_no: Optional[str] = None
    gender: Gender
    category: StudentCategory = StudentCategory.GENERAL
    placement_type: PlacementType = PlacementType.CAMPUS
    company_name: Optional[str] = None
    designation: Optional[str] = None
    package_lpa: Optional[float] = None
    placement_date: Optional[date] = None
    company_city: Optional[str] = None
    company_state: Optional[str] = None
    is_international: bool = False
    is_verified: bool = False
    remarks: Optional[str] = None


class PlacementCreate(PlacementBase):
    pass


class PlacementUpdate(BaseModel):
    department_id: Optional[uuid.UUID] = None
    student_name: Optional[str] = None
    gender: Optional[Gender] = None
    category: Optional[StudentCategory] = None
    placement_type: Optional[PlacementType] = None
    company_name: Optional[str] = None
    designation: Optional[str] = None
    package_lpa: Optional[float] = None
    placement_date: Optional[date] = None
    company_city: Optional[str] = None
    company_state: Optional[str] = None
    is_international: Optional[bool] = None
    is_verified: Optional[bool] = None
    remarks: Optional[str] = None


class PlacementRead(PlacementBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedPlacements(PaginatedResponse):
    items: list[PlacementRead]


# ── Higher Studies ────────────────────────────────────────────────────────────

class HigherStudyBase(BaseModel):
    academic_year: str
    department_id: uuid.UUID
    program_id: Optional[uuid.UUID] = None
    student_name: str
    enrollment_no: Optional[str] = None
    gender: Gender
    admitted_program: str
    admitted_institute: str
    admitted_university: Optional[str] = None
    country: str = "India"
    entrance_exam: Optional[str] = None
    entrance_score: Optional[float] = None
    scholarship_received: bool = False
    scholarship_amount: Optional[float] = None
    is_verified: bool = False
    remarks: Optional[str] = None


class HigherStudyCreate(HigherStudyBase):
    pass


class HigherStudyUpdate(BaseModel):
    is_verified: Optional[bool] = None
    scholarship_received: Optional[bool] = None
    scholarship_amount: Optional[float] = None
    remarks: Optional[str] = None


class HigherStudyRead(HigherStudyBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedHigherStudies(PaginatedResponse):
    items: list[HigherStudyRead]


# ── MoU ───────────────────────────────────────────────────────────────────────

class MoUBase(BaseModel):
    academic_year: str
    department_id: Optional[uuid.UUID] = None
    partner_name: str
    partner_country: str = "India"
    partner_type: MoUType
    mou_type: Optional[str] = None
    signed_date: Optional[date] = None
    valid_until: Optional[date] = None
    purpose: Optional[str] = None
    activities_conducted: int = 0
    is_active: bool = True
    remarks: Optional[str] = None


class MoUCreate(MoUBase):
    pass


class MoUUpdate(BaseModel):
    partner_name: Optional[str] = None
    partner_country: Optional[str] = None
    partner_type: Optional[MoUType] = None
    mou_type: Optional[str] = None
    signed_date: Optional[date] = None
    valid_until: Optional[date] = None
    purpose: Optional[str] = None
    activities_conducted: Optional[int] = None
    is_active: Optional[bool] = None
    remarks: Optional[str] = None


class MoURead(MoUBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedMoUs(PaginatedResponse):
    items: list[MoURead]


# ── Events ────────────────────────────────────────────────────────────────────

class EventBase(BaseModel):
    academic_year: str
    department_id: Optional[uuid.UUID] = None
    title: str
    event_type: EventType
    is_organized: bool = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None
    venue: Optional[str] = None
    participants_count: int = 0
    faculty_participants: int = 0
    student_participants: int = 0
    external_participants: int = 0
    is_international: bool = False
    funding_amount: Optional[float] = None
    sdg_goals: Optional[str] = None
    remarks: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    event_type: Optional[EventType] = None
    is_organized: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None
    venue: Optional[str] = None
    participants_count: Optional[int] = None
    faculty_participants: Optional[int] = None
    student_participants: Optional[int] = None
    external_participants: Optional[int] = None
    is_international: Optional[bool] = None
    funding_amount: Optional[float] = None
    remarks: Optional[str] = None


class EventRead(EventBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedEvents(PaginatedResponse):
    items: list[EventRead]


# ── Energy ────────────────────────────────────────────────────────────────────

class EnergyBase(BaseModel):
    academic_year: str
    month: Optional[int] = Field(None, ge=1, le=12)
    department_id: Optional[uuid.UUID] = None
    electricity_kwh: float = 0.0
    electricity_cost_inr: Optional[float] = None
    solar_kwh: float = 0.0
    wind_kwh: float = 0.0
    other_renewable_kwh: float = 0.0
    diesel_liters: float = 0.0
    lpg_kg: float = 0.0
    cng_kg: float = 0.0
    ghg_scope1_tco2e: Optional[float] = None
    ghg_scope2_tco2e: Optional[float] = None
    remarks: Optional[str] = None


class EnergyCreate(EnergyBase):
    pass


class EnergyUpdate(BaseModel):
    month: Optional[int] = Field(None, ge=1, le=12)
    electricity_kwh: Optional[float] = None
    electricity_cost_inr: Optional[float] = None
    solar_kwh: Optional[float] = None
    wind_kwh: Optional[float] = None
    other_renewable_kwh: Optional[float] = None
    diesel_liters: Optional[float] = None
    lpg_kg: Optional[float] = None
    cng_kg: Optional[float] = None
    ghg_scope1_tco2e: Optional[float] = None
    ghg_scope2_tco2e: Optional[float] = None
    remarks: Optional[str] = None


class EnergyRead(EnergyBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedEnergy(PaginatedResponse):
    items: list[EnergyRead]


# ── Water ─────────────────────────────────────────────────────────────────────

class WaterBase(BaseModel):
    academic_year: str
    month: Optional[int] = Field(None, ge=1, le=12)
    department_id: Optional[uuid.UUID] = None
    municipal_kl: float = 0.0
    borewell_kl: float = 0.0
    rainwater_harvested_kl: float = 0.0
    recycled_treated_kl: float = 0.0
    cost_inr: Optional[float] = None
    remarks: Optional[str] = None


class WaterCreate(WaterBase):
    pass


class WaterUpdate(BaseModel):
    month: Optional[int] = Field(None, ge=1, le=12)
    municipal_kl: Optional[float] = None
    borewell_kl: Optional[float] = None
    rainwater_harvested_kl: Optional[float] = None
    recycled_treated_kl: Optional[float] = None
    cost_inr: Optional[float] = None
    remarks: Optional[str] = None


class WaterRead(WaterBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedWater(PaginatedResponse):
    items: list[WaterRead]


# ── Waste ─────────────────────────────────────────────────────────────────────

class WasteBase(BaseModel):
    academic_year: str
    month: Optional[int] = Field(None, ge=1, le=12)
    waste_type: WasteType
    generated_kg: float = 0.0
    recycled_kg: float = 0.0
    disposed_kg: float = 0.0
    disposal_method: Optional[str] = None
    vendor_name: Optional[str] = None
    cost_inr: Optional[float] = None
    remarks: Optional[str] = None


class WasteCreate(WasteBase):
    pass


class WasteUpdate(BaseModel):
    month: Optional[int] = Field(None, ge=1, le=12)
    waste_type: Optional[WasteType] = None
    generated_kg: Optional[float] = None
    recycled_kg: Optional[float] = None
    disposed_kg: Optional[float] = None
    disposal_method: Optional[str] = None
    vendor_name: Optional[str] = None
    cost_inr: Optional[float] = None
    remarks: Optional[str] = None


class WasteRead(WasteBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedWaste(PaginatedResponse):
    items: list[WasteRead]


# ── Awards ────────────────────────────────────────────────────────────────────

class AwardBase(BaseModel):
    academic_year: str
    department_id: Optional[uuid.UUID] = None
    title: str
    awarding_body: str
    recipient_name: str
    recipient_type: str  # faculty / student / institution
    award_date: Optional[date] = None
    category: Optional[str] = None
    is_national: bool = True
    is_international: bool = False
    prize_amount: Optional[float] = None
    remarks: Optional[str] = None


class AwardCreate(AwardBase):
    pass


class AwardUpdate(BaseModel):
    title: Optional[str] = None
    awarding_body: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_type: Optional[str] = None
    award_date: Optional[date] = None
    category: Optional[str] = None
    is_national: Optional[bool] = None
    is_international: Optional[bool] = None
    prize_amount: Optional[float] = None
    remarks: Optional[str] = None


class AwardRead(AwardBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedAwards(PaginatedResponse):
    items: list[AwardRead]


# ── Accreditations ────────────────────────────────────────────────────────────

class AccreditationBase(BaseModel):
    name: str
    awarding_body: str
    program_department: Optional[str] = None
    grade_score: Optional[str] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    cycle: Optional[int] = None
    is_active: bool = True
    remarks: Optional[str] = None


class AccreditationCreate(AccreditationBase):
    pass


class AccreditationUpdate(BaseModel):
    grade_score: Optional[str] = None
    valid_until: Optional[date] = None
    is_active: Optional[bool] = None
    remarks: Optional[str] = None


class AccreditationRead(AccreditationBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Consultancy ───────────────────────────────────────────────────────────────

class ConsultancyBase(BaseModel):
    academic_year: str
    department_id: uuid.UUID
    title: str
    client_name: str
    faculty_names: str
    faculty_employee_ids: Optional[str] = None
    amount_inr: float = 0.0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_ongoing: bool = False
    remarks: Optional[str] = None


class ConsultancyCreate(ConsultancyBase):
    pass


class ConsultancyUpdate(BaseModel):
    amount_inr: Optional[float] = None
    is_ongoing: Optional[bool] = None
    end_date: Optional[date] = None
    remarks: Optional[str] = None


class ConsultancyRead(ConsultancyBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedConsultancy(PaginatedResponse):
    items: list[ConsultancyRead]


# ── SDG Activities ────────────────────────────────────────────────────────────

class SDGActivityBase(BaseModel):
    academic_year: str
    department_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    activity_type: str
    sdg_primary: int = Field(..., ge=1, le=17)
    sdg_secondary: Optional[str] = None
    beneficiaries_count: Optional[int] = None
    investment_inr: Optional[float] = None
    outcome: Optional[str] = None
    remarks: Optional[str] = None


class SDGActivityCreate(SDGActivityBase):
    pass


class SDGActivityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    activity_type: Optional[str] = None
    sdg_primary: Optional[int] = Field(None, ge=1, le=17)
    sdg_secondary: Optional[str] = None
    beneficiaries_count: Optional[int] = None
    investment_inr: Optional[float] = None
    outcome: Optional[str] = None
    remarks: Optional[str] = None


class SDGActivityRead(SDGActivityBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedSDG(PaginatedResponse):
    items: list[SDGActivityRead]
