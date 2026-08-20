"""
Module 6 — AI Natural Language Search
======================================
Builds a compact textual description of the whitelisted tables and
columns for the LLM's prompt, and holds a few worked examples that
steer it toward the query patterns this platform actually needs
(joins to departments, filtering by academic_year, etc).
"""
from app.db.session import Base
from app.utils.sql_guard import ALLOWED_TABLES

# Import all model modules once so Base.metadata is fully populated —
# this module may be the first thing to touch metadata in a fresh process.
from app.models import user, faculty, student, research, placement  # noqa: F401
from app.models import institutional, green, awards  # noqa: F401


def build_schema_description() -> str:
    """Returns a human/LLM-readable description of every allowed table."""
    lines: list[str] = []
    for table in Base.metadata.sorted_tables:
        if table.name not in ALLOWED_TABLES:
            continue
        col_descriptions = []
        for col in table.columns:
            col_type = str(col.type)
            flags = []
            if col.primary_key:
                flags.append("PK")
            if col.foreign_keys:
                fk_targets = ", ".join(sorted(fk.target_fullname for fk in col.foreign_keys))
                flags.append(f"FK->{fk_targets}")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            col_descriptions.append(f"{col.name} ({col_type}){flag_str}")
        lines.append(f"TABLE {table.name}:\n  " + "\n  ".join(col_descriptions))
    return "\n\n".join(lines)


EXAMPLE_QUESTIONS: list[str] = [
    "How many faculty members are there in each department?",
    "List all research publications indexed in Scopus for 2023-24",
    "Which students have a CGPA above 9 this year?",
    "Total placements by company for the current academic year",
    "How many patents were granted in the last 3 years?",
    "Show total energy consumption by month for 2023-24",
    "List active MoUs signed with international partners",
]

FEW_SHOT_EXAMPLES = """
Example 1
Question: How many faculty members are there in each department?
SQL:
SELECT d.name AS department, COUNT(f.id) AS faculty_count
FROM faculty f
JOIN departments d ON f.department_id = d.id
GROUP BY d.name
ORDER BY faculty_count DESC;

Example 2
Question: List research publications indexed in Scopus for 2023-24
SQL:
SELECT title, journal_conference_name, publication_year, citations
FROM research_publications
WHERE indexing = 'scopus' AND academic_year = '2023-24'
ORDER BY publication_year DESC
LIMIT 200;

Example 3
Question: Total placement package by department for 2023-24
SQL:
SELECT d.name AS department, COUNT(p.id) AS placed_students, AVG(p.package_lpa) AS avg_package_lpa
FROM placements p
JOIN departments d ON p.department_id = d.id
WHERE p.academic_year = '2023-24'
GROUP BY d.name
ORDER BY avg_package_lpa DESC;

Example 4
Question: give me details of student name jagarlamudi samba in 2023-24
SQL:
SELECT enrollment_no, full_name, academic_year, gender, category, cgpa
FROM students
WHERE full_name ILIKE '%jagarlamudi%' AND full_name ILIKE '%samba%' AND academic_year = '2023-24'
LIMIT 200;
-- Note how each word became its own ILIKE '%word%' condition, ANDed
-- together, instead of one ILIKE '%jagarlamudi samba%' on the whole
-- phrase. The user may not know or remember someone's full name, so
-- matching every word independently finds "Jagarlamudi Samba Siva" even
-- though the phrase itself is a partial, reordered, or incomplete name.
""".strip()


def build_system_prompt() -> str:
    schema = build_schema_description()
    return f"""You are a PostgreSQL expert helping IQAC (Internal Quality Assurance Cell) staff
at Ganpat University query their institutional data using plain English.

You must respond with ONLY a single valid PostgreSQL SELECT statement — no prose,
no explanation, no markdown code fences. Never generate INSERT, UPDATE, DELETE,
DROP, ALTER, or any statement that is not a read-only SELECT.

Rules:
- Only use the tables and columns listed below. Never invent a table or column.
- Always join to `departments` (via department_id) when the question asks about a department by name.
- Prefer filtering by `academic_year` (format "YYYY-YY", e.g. "2023-24") when a year is mentioned or implied.
- For person/title name searches (full_name, title, partner_name, company_name, etc.),
  NEVER match the whole phrase as one ILIKE pattern. Instead, split the search phrase
  into individual words and require each word to appear somewhere in the field,
  independently, with a separate `column ILIKE '%word%'` per word, ANDed together.
  This finds the right record even if the user only remembers part of a name, gets
  the word order wrong, or the phrase is a subset of the real value — see Example 4.
  Skip filler words like "name", "the", "of", "student", "faculty" when splitting;
  only use the actual name/title words the user gave.
- Always include a LIMIT clause (200 rows by default) unless the question clearly asks for an aggregate (COUNT, SUM, AVG) with a small number of groups.
- Enum columns (gender, designation, category, indexing, etc.) store lowercase snake_case string values.

DATABASE SCHEMA:
{schema}

{FEW_SHOT_EXAMPLES}

Respond with the SQL only.
"""
