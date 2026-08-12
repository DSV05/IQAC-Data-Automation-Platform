"""
Shared enums and mixins used across all master data models.
"""
import enum


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class EmploymentType(str, enum.Enum):
    PERMANENT = "permanent"
    CONTRACT = "contract"
    VISITING = "visiting"
    ADJUNCT = "adjunct"


class Designation(str, enum.Enum):
    PROFESSOR = "professor"
    ASSOCIATE_PROFESSOR = "associate_professor"
    ASSISTANT_PROFESSOR = "assistant_professor"
    LECTURER = "lecturer"
    HOD = "hod"
    DEAN = "dean"
    DIRECTOR = "director"
    OTHER = "other"


class Qualification(str, enum.Enum):
    PHD = "phd"
    MTECH = "mtech"
    ME = "me"
    MBA = "mba"
    MPHIL = "mphil"
    MPHARM = "mpharm"
    BTECH = "btech"
    BE = "be"
    OTHER = "other"


class StudentCategory(str, enum.Enum):
    GENERAL = "general"
    OBC = "obc"
    SC = "sc"
    ST = "st"
    EWS = "ews"
    PWD = "pwd"


class AdmissionType(str, enum.Enum):
    REGULAR = "regular"
    LATERAL = "lateral"
    NRI = "nri"
    MANAGEMENT = "management"


class ProgramLevel(str, enum.Enum):
    DIPLOMA = "diploma"
    UG = "ug"
    PG = "pg"
    PHD = "phd"
    CERTIFICATE = "certificate"


class PublicationCategory(str, enum.Enum):
    JOURNAL = "journal"
    CONFERENCE = "conference"
    BOOK = "book"
    BOOK_CHAPTER = "book_chapter"
    PATENT = "patent"


class IndexingType(str, enum.Enum):
    SCOPUS = "scopus"
    WOS = "wos"
    SCI = "sci"
    ESCI = "esci"
    UGC_CARE = "ugc_care"
    OTHER = "other"


class PatentStatus(str, enum.Enum):
    FILED = "filed"
    PUBLISHED = "published"
    GRANTED = "granted"
    ABANDONED = "abandoned"


class PlacementType(str, enum.Enum):
    CAMPUS = "campus"
    OFF_CAMPUS = "off_campus"
    HIGHER_STUDIES = "higher_studies"
    ENTREPRENEURSHIP = "entrepreneurship"


class FundingAgency(str, enum.Enum):
    DST = "dst"
    DBT = "dbt"
    ICMR = "icmr"
    UGC = "ugc"
    AICTE = "aicte"
    CSIR = "csir"
    ISRO = "isro"
    DRDO = "drdo"
    INDUSTRY = "industry"
    INTERNATIONAL = "international"
    OTHER = "other"


class MoUType(str, enum.Enum):
    ACADEMIC = "academic"
    INDUSTRY = "industry"
    RESEARCH = "research"
    INTERNATIONAL = "international"
    GOVERNMENT = "government"


class EventType(str, enum.Enum):
    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    SEMINAR = "seminar"
    FDP = "fdp"
    WEBINAR = "webinar"
    CULTURAL = "cultural"
    SPORTS = "sports"
    OTHER = "other"


class WasteType(str, enum.Enum):
    SOLID = "solid"
    BIOMEDICAL = "biomedical"
    EWASTE = "ewaste"
    HAZARDOUS = "hazardous"
    RECYCLABLE = "recyclable"


class SDGGoal(int, enum.Enum):
    SDG1 = 1
    SDG2 = 2
    SDG3 = 3
    SDG4 = 4
    SDG5 = 5
    SDG6 = 6
    SDG7 = 7
    SDG8 = 8
    SDG9 = 9
    SDG10 = 10
    SDG11 = 11
    SDG12 = 12
    SDG13 = 13
    SDG14 = 14
    SDG15 = 15
    SDG16 = 16
    SDG17 = 17
