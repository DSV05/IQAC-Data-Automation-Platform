"""Module 8 — Report Generator — orchestrates data fetch, formatting, and audit logging."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reports import ReportFormat, ReportGenerationLog, ReportType
from app.utils import report_data
from app.utils.report_excel import GENERATORS as EXCEL_GENERATORS
from app.utils.report_pdf import GENERATORS as PDF_GENERATORS
from app.utils.nirf_template import generate_nirf_2026_excel

DATA_FETCHERS = {
    "nirf": report_data.get_nirf_data,
    "naac_ssr": report_data.get_naac_data,
    "aishe": report_data.get_aishe_data,
}

REPORT_TYPE_INFO = [
    {
        "value": "nirf",
        "label": "NIRF Data",
        "description": "Official NIRF Excel workbook, populated from year-wise master data.",
    },
    {
        "value": "naac_ssr",
        "label": "NAAC SSR Data Summary",
        "description": "Criteria-wise institutional data mapped to NAAC's seven SSR criteria.",
    },
    {
        "value": "aishe",
        "label": "AISHE Institutional Data",
        "description": "Program-wise enrollment and faculty/student demographic breakdowns.",
    },
]


class UnknownReportTypeError(Exception):
    pass


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(
        self, user_id: uuid.UUID, report_type: str, report_format: str, academic_year: str | None
    ) -> bytes:
        if report_type not in DATA_FETCHERS:
            raise UnknownReportTypeError(f"Unknown report type: {report_type}")

        if report_type == "nirf" and report_format != "xlsx":
            raise ValueError("NIRF Data is available only as the official Excel workbook.")
        if report_type == "nirf":
            if not academic_year:
                raise ValueError("An academic year is required for the NIRF workbook.")
            file_bytes = await generate_nirf_2026_excel(self.db, academic_year)
        else:
            data = await DATA_FETCHERS[report_type](self.db, academic_year)
            if report_format == "pdf":
                file_bytes = PDF_GENERATORS[report_type](data)
            else:
                file_bytes = EXCEL_GENERATORS[report_type](data)

        log = ReportGenerationLog(
            user_id=user_id,
            report_type=ReportType(report_type),
            report_format=ReportFormat(report_format),
            academic_year=academic_year,
            file_size_bytes=len(file_bytes),
        )
        self.db.add(log)
        await self.db.commit()

        return file_bytes
