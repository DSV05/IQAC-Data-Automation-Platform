/**
 * MasterDataPage
 * ──────────────
 * Column definitions below now include every field present in the
 * corresponding downloadable template (backend/app/utils/column_maps.py),
 * so what's shown in this table and what's in the template always match.
 *
 * Edit Template modal persists custom column labels to localStorage and
 * passes them to the backend template download as `label_<field>` query
 * params, so the downloaded .xlsx reflects the admin's custom headers
 * (see backend/app/api/v1/endpoints/uploads.py::download_template).
 */

import React, { useState, useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Users, GraduationCap, BookOpen, Lightbulb, Briefcase,
  Zap, Droplets, Trash2, Award, Handshake,
  CalendarDays, Leaf, ChevronRight, Pencil, X, RefreshCw,
  Search, Download, Settings2, AlertCircle,
  CheckCircle2,
} from "lucide-react";
import apiClient from "@/services/api";
import { useAuthStore } from "@/store/auth.store";
import { hasMinimumRole } from "@/utils/roles";
import ExcelFilterTable from "@/components/master/ExcelFilterTable";

// ── Academic years ─────────────────────────────────────────────────────────────
const YEARS = ["2024-25", "2023-24", "2022-23", "2021-22", "2020-21"];

// ── Tab definitions ────────────────────────────────────────────────────────────
const TABS = [
  { key: "faculty",    label: "Faculty",    icon: Users,        color: "text-blue-600 bg-blue-50",       templateKey: "faculty" },
  { key: "students",   label: "Students",   icon: GraduationCap,color: "text-green-600 bg-green-50",     templateKey: "students" },
  { key: "research",   label: "Research",   icon: BookOpen,     color: "text-purple-600 bg-purple-50",   templateKey: "research" },
  { key: "patents",    label: "Patents",    icon: Lightbulb,    color: "text-amber-600 bg-amber-50",     templateKey: "patents" },
  { key: "placements", label: "Placements", icon: Briefcase,    color: "text-teal-600 bg-teal-50",       templateKey: "placements" },
  { key: "funded_projects", label: "Sponsored Research", icon: BookOpen, color: "text-violet-600 bg-violet-50", templateKey: "funded_projects" },
  { key: "consultancy", label: "Consultancy Projects", icon: Handshake, color: "text-sky-600 bg-sky-50", templateKey: "consultancy" },
  { key: "mous",       label: "MoUs",       icon: Handshake,    color: "text-indigo-600 bg-indigo-50",   templateKey: "mous" },
  { key: "events",     label: "Events",     icon: CalendarDays, color: "text-pink-600 bg-pink-50",       templateKey: "events" },
  { key: "energy",     label: "Energy",     icon: Zap,          color: "text-yellow-600 bg-yellow-50",   templateKey: "energy" },
  { key: "water",      label: "Water",      icon: Droplets,     color: "text-cyan-600 bg-cyan-50",       templateKey: "water" },
  { key: "waste",      label: "Waste",      icon: Trash2,       color: "text-red-600 bg-red-50",         templateKey: "waste" },
  { key: "awards",     label: "Awards",     icon: Award,        color: "text-orange-600 bg-orange-50",   templateKey: "awards" },
  { key: "sdg",        label: "SDG",        icon: Leaf,         color: "text-emerald-600 bg-emerald-50", templateKey: "sdg_activities" },
];

// ── Search placeholder hints ───────────────────────────────────────────────────
const SEARCH_HINTS: Record<string, string> = {
  faculty:    "Search by name, employee ID, designation…",
  students:   "Search by name, enrollment no, category…",
  research:   "Search by title, authors, indexing…",
  patents:    "Search by title, application number…",
  placements: "Search by student name, company…",
  funded_projects: "Search by project title or investigator…",
  consultancy: "Search by title or client organization…",
  mous:       "Search by partner name, country…",
  events:     "Search by title, event type…",
  energy:     "Search by month…",
  water:      "Search by month…",
  waste:      "Search by waste type…",
  awards:     "Search by recipient, award title…",
  sdg:        "Search by activity, SDG goal…",
};

// These datasets are institution-wide. Department is intentionally not part
// of their UI, editing, or display flow even though legacy database rows may
// still contain an optional department_id.
const DEPARTMENT_MANAGED_ENTITIES = new Set([
  "faculty", "students", "research", "patents", "placements", "funded_projects", "consultancy",
]);

// ── localStorage helpers for custom template labels ────────────────────────────
const LABEL_STORAGE_KEY = "iqac_template_labels";

function loadCustomLabels(): Record<string, Record<string, string>> {
  try {
    return JSON.parse(localStorage.getItem(LABEL_STORAGE_KEY) || "{}");
  } catch { return {}; }
}

function saveCustomLabels(all: Record<string, Record<string, string>>) {
  localStorage.setItem(LABEL_STORAGE_KEY, JSON.stringify(all));
}

// ── COLUMN DEFINITIONS — mirrors column_maps.py db_fields EXACTLY ─────────────
//    Required(*) columns are marked. Every field present in the template for
//    that entity appears here too, so table and template never drift apart.

const COLUMNS: Record<string, { key: string; label: string; required?: boolean; templated?: boolean; render?: (v: any, row: any) => React.ReactNode }[]> = {
  faculty: [
    { key: "employee_id",          label: "Employee ID",       required: true  },
    { key: "full_name",            label: "Full Name",         required: true  },
    { key: "institute",            label: "Institute" },
    { key: "department_name",      label: "Department",        templated: false },
    { key: "gender",               label: "Gender",            required: true,  render: (v) => <span className="capitalize">{v}</span> },
    { key: "designation",          label: "Designation",       required: true,  render: (v) => <Badge value={v} /> },
    { key: "qualification",        label: "Qualification",     required: true,  render: (v) => <span className="uppercase text-xs font-medium">{v}</span> },
    { key: "employment_type",      label: "Employment Type",   required: true,  render: (v) => <Badge value={v} /> },
    { key: "experience_teaching",  label: "Teaching Exp (Yrs)",required: true,  render: (v) => `${v}y` },
    { key: "email",                label: "Email" },
    { key: "phone",                label: "Phone",                              render: (v) => v ?? "—" },
    { key: "date_of_joining",      label: "Date of Joining",                    render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "date_of_leaving",      label: "Date of Leaving",                    render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "date_of_birth",        label: "Date of Birth",                      render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "specialization",       label: "Specialization" },
    { key: "phd_awarded",          label: "PhD",                                render: (v) => v ? <span className="text-green-600 font-medium">Yes</span> : <span className="text-muted-foreground">No</span> },
    { key: "phd_year",             label: "PhD Year",                           render: (v) => v ?? "—" },
    { key: "experience_industry",  label: "Industry Exp (Yrs)",                 render: (v) => v ?? "—" },
    { key: "experience_research",  label: "Research Exp (Yrs)",                 render: (v) => v ?? "—" },
    { key: "pan_number",           label: "PAN Number",                         render: (v) => v ?? "—" },
    { key: "is_active",            label: "Status",            templated: false,render: (v) => <StatusPill active={v} /> },
  ],
  students: [
    { key: "enrollment_no",        label: "Enrollment No",     required: true },
    { key: "full_name",            label: "Full Name",         required: true },
    { key: "department_name",      label: "Department",        templated: false },
    { key: "gender",               label: "Gender",            required: true, render: (v) => <span className="capitalize">{v}</span> },
    { key: "year_of_admission",    label: "Admission Year",    required: true },
    { key: "current_year",         label: "Current Year",      required: true },
    { key: "category",             label: "Category",                          render: (v) => v ? <span className="uppercase text-xs">{v}</span> : "—" },
    { key: "admission_type",       label: "Admission Type",                    render: (v) => v ? <Badge value={v} /> : "—" },
    { key: "email",                label: "Email",                             render: (v) => v ?? "—" },
    { key: "phone",                label: "Phone",                             render: (v) => v ?? "—" },
    { key: "date_of_birth",        label: "Date of Birth",                     render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "cgpa",                 label: "CGPA",                              render: (v) => v ?? "—" },
    { key: "sgpa_last",            label: "Last SGPA",                         render: (v) => v ?? "—" },
    { key: "state_of_domicile",    label: "State of Domicile",                 render: (v) => v ?? "—" },
    { key: "is_pwd",               label: "PWD",                               render: (v) => v ? "Yes" : "No" },
    { key: "backlogs",             label: "Backlogs",                          render: (v) => v ?? "—" },
    { key: "is_active",            label: "Status",           templated: false,render: (v) => <StatusPill active={v} /> },
  ],
  research: [
    { key: "title",                    label: "Title",              required: true, render: (v) => <span className="max-w-xs truncate block" title={v}>{v}</span> },
    { key: "department_name",          label: "Department",         templated: false },
    { key: "authors",                  label: "Authors",            required: true, render: (v) => <span className="max-w-[120px] truncate block" title={v}>{v}</span> },
    { key: "category",                 label: "Category",           required: true, render: (v) => <Badge value={v} /> },
    { key: "publication_year",         label: "Year",               required: true },
    { key: "indexing",                 label: "Indexing",           required: true, render: (v) => <span className="uppercase text-xs font-medium">{v}</span> },
    { key: "journal_conference_name",  label: "Journal / Conference",              render: (v) => <span className="max-w-[140px] truncate block" title={v}>{v ?? "—"}</span> },
    { key: "doi",                      label: "DOI",                               render: (v) => v ?? "—" },
    { key: "impact_factor",            label: "Impact Factor",                     render: (v) => v ?? "—" },
    { key: "citations",                label: "Citations",                         render: (v) => v ?? "—" },
    { key: "isbn_issn",                label: "ISBN / ISSN",                       render: (v) => v ?? "—" },
    { key: "publisher",                label: "Publisher",                         render: (v) => v ?? "—" },
    { key: "is_verified",              label: "Verified",         templated: false,render: (v) => v ? <span className="text-green-600">✓</span> : <span className="text-muted-foreground">—</span> },
  ],
  patents: [
    { key: "title",              label: "Title",              required: true, render: (v) => <span className="max-w-xs truncate block" title={v}>{v}</span> },
    { key: "department_name",    label: "Department",         templated: false },
    { key: "application_number", label: "Application No",    required: true },
    { key: "inventors",          label: "Inventors",         required: true, render: (v) => <span className="max-w-[120px] truncate block" title={v}>{v}</span> },
    { key: "status",             label: "Status",            required: true, render: (v) => <Badge value={v} /> },
    { key: "filing_date",        label: "Filed On",                          render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "grant_date",         label: "Granted On",                        render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "country",            label: "Country",                           render: (v) => v ?? "—" },
  ],
  placements: [
    { key: "student_name",    label: "Student Name",    required: true },
    { key: "department_name", label: "Department",      templated: false },
    { key: "gender",          label: "Gender",          required: true, render: (v) => <span className="capitalize">{v}</span> },
    { key: "placement_type",  label: "Placement Type",  required: true, render: (v) => <Badge value={v} /> },
    { key: "company_name",    label: "Company",                         render: (v) => v ?? "—" },
    { key: "designation",     label: "Role",                            render: (v) => v ?? "—" },
    { key: "package_lpa",     label: "Package (LPA)",                   render: (v) => v ? `₹${v}L` : "—" },
    { key: "enrollment_no",   label: "Enrollment No",                   render: (v) => v ?? "—" },
    { key: "placement_date",  label: "Placement Date",                  render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "company_city",    label: "Company City",                    render: (v) => v ?? "—" },
    { key: "company_state",   label: "Company State",                   render: (v) => v ?? "—" },
    { key: "category",        label: "Category",                        render: (v) => v ?? "—" },
    { key: "is_verified",     label: "Verified",        templated: false,render: (v) => v ? <span className="text-green-600">✓</span> : "—" },
  ],
  funded_projects: [
    { key: "title", label: "Project Title", required: true },
    { key: "department_name", label: "Department", templated: false },
    { key: "principal_investigator", label: "Principal Investigator", required: true },
    { key: "funding_agency", label: "Funding Agency", required: true, render: (v) => <Badge value={v} /> },
    { key: "funding_agency_name", label: "Agency Name", render: (v) => v ?? "—" },
    { key: "scheme", label: "Scheme", render: (v) => v ?? "—" },
    { key: "amount_sanctioned", label: "Sanctioned (₹)", render: (v) => v?.toLocaleString() ?? "—" },
    { key: "amount_received", label: "Received (₹)", render: (v) => v?.toLocaleString() ?? "—" },
    { key: "start_date", label: "Start Date", render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "end_date", label: "End Date", render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "is_ongoing", label: "Ongoing", render: (v) => v ? "Yes" : "No" },
  ],
  consultancy: [
    { key: "title", label: "Consultancy Title", required: true },
    { key: "department_name", label: "Department", templated: false },
    { key: "client_name", label: "Client Organization", required: true },
    { key: "faculty_names", label: "Faculty / Consultants", required: true },
    { key: "amount_inr", label: "Amount Received (₹)", render: (v) => v?.toLocaleString() ?? "—" },
    { key: "start_date", label: "Start Date", render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "end_date", label: "End Date", render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "is_ongoing", label: "Ongoing", render: (v) => v ? "Yes" : "No" },
  ],
  mous: [
    { key: "partner_name",    label: "Partner Name",    required: true },
    { key: "partner_type",    label: "Partner Type",    required: true, render: (v) => <Badge value={v} /> },
    { key: "partner_country", label: "Country",                         render: (v) => v ?? "—" },
    { key: "signed_date",     label: "Signed Date",                     render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "valid_until",     label: "Valid Until",                     render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "purpose",         label: "Purpose",                         render: (v) => <span className="max-w-xs truncate block" title={v}>{v ?? "—"}</span> },
    { key: "is_active",       label: "Active",          templated: false,render: (v) => <StatusPill active={v} /> },
  ],
  events: [
    { key: "title",                label: "Title",               required: true, render: (v) => <span className="max-w-xs truncate block" title={v}>{v}</span> },
    { key: "event_type",           label: "Event Type",          required: true, render: (v) => <Badge value={v} /> },
    { key: "participants_count",   label: "Participants" },
    { key: "start_date",           label: "Start Date",                          render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "end_date",             label: "End Date",                            render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "duration_days",        label: "Duration (Days)",                     render: (v) => v ?? "—" },
    { key: "venue",                label: "Venue",                               render: (v) => v ?? "—" },
    { key: "faculty_participants", label: "Faculty",                             render: (v) => v ?? "—" },
    { key: "student_participants", label: "Students",                            render: (v) => v ?? "—" },
    { key: "is_organized",         label: "Role",              templated: false, render: (v) => v ? "Organized" : "Attended" },
  ],
  energy: [
    { key: "electricity_kwh",      label: "Grid (kWh)",          required: true, render: (v) => v?.toLocaleString() ?? "—" },
    { key: "solar_kwh",            label: "Solar (kWh)",         render: (v) => v?.toLocaleString() ?? "—" },
    { key: "diesel_liters",        label: "Diesel (L)",          render: (v) => v?.toLocaleString() ?? "—" },
    { key: "month",                label: "Month",               render: (v) => v ? new Date(2024, v - 1).toLocaleString("en", { month: "short" }) : "Annual" },
    { key: "electricity_cost_inr", label: "Bill (₹)",            render: (v) => v ? `₹${v.toLocaleString()}` : "—" },
    { key: "lpg_kg",               label: "LPG (kg)",            render: (v) => v ?? "—" },
    { key: "ghg_scope1_tco2e",     label: "Scope 1 (tCO₂e)",    render: (v) => v?.toFixed(2) ?? "—" },
    { key: "ghg_scope2_tco2e",     label: "Scope 2 (tCO₂e)",    render: (v) => v?.toFixed(2) ?? "—" },
  ],
  water: [
    { key: "municipal_kl",           label: "Municipal (kL)",    render: (v) => v ?? "—" },
    { key: "borewell_kl",            label: "Borewell (kL)",     render: (v) => v ?? "—" },
    { key: "rainwater_harvested_kl", label: "Rainwater (kL)",    render: (v) => v ?? "—" },
    { key: "recycled_treated_kl",    label: "Recycled (kL)",     render: (v) => v ?? "—" },
    { key: "month",                  label: "Month",             render: (v) => v ? new Date(2024, v - 1).toLocaleString("en", { month: "short" }) : "Annual" },
    { key: "cost_inr",               label: "Cost (₹)",          render: (v) => v ? `₹${v.toLocaleString()}` : "—" },
  ],
  waste: [
    { key: "waste_type",      label: "Waste Type",      required: true, render: (v) => <Badge value={v} /> },
    { key: "generated_kg",    label: "Generated (kg)",                  render: (v) => v ?? "—" },
    { key: "recycled_kg",     label: "Recycled (kg)",                   render: (v) => v ?? "—" },
    { key: "disposed_kg",     label: "Disposed (kg)",                   render: (v) => v ?? "—" },
    { key: "disposal_method", label: "Disposal Method",                 render: (v) => v ?? "—" },
    { key: "vendor_name",     label: "Vendor",                          render: (v) => v ?? "—" },
    { key: "month",           label: "Month",                           render: (v) => v ? new Date(2024, v - 1).toLocaleString("en", { month: "short" }) : "Annual" },
    { key: "cost_inr",        label: "Cost (₹)",                        render: (v) => v ? `₹${v.toLocaleString()}` : "—" },
  ],
  awards: [
    { key: "recipient_name",  label: "Recipient",       required: true },
    { key: "recipient_type",  label: "Type",            required: true, render: (v) => <Badge value={v} /> },
    { key: "title",           label: "Award",           required: true, render: (v) => <span className="max-w-xs truncate block" title={v}>{v}</span> },
    { key: "awarding_body",   label: "Awarding Body",   required: true },
    { key: "award_date",      label: "Date",            render: (v) => v ? new Date(v).toLocaleDateString("en-IN") : "—" },
    { key: "category",        label: "Category",        render: (v) => v ?? "—" },
    { key: "is_international",label: "International",   render: (v) => v ? <span className="text-blue-600">✓</span> : "—" },
    { key: "prize_amount",    label: "Prize Amount (₹)",render: (v) => v ? `₹${v.toLocaleString()}` : "—" },
  ],
  sdg: [
    { key: "title",               label: "Activity",      required: true, render: (v) => <span className="max-w-xs truncate block" title={v}>{v}</span> },
    { key: "sdg_primary",         label: "SDG",           required: true, render: (v) => <SDGBadge goal={v} /> },
    { key: "activity_type",       label: "Type",          required: true, render: (v) => <span className="capitalize">{v}</span> },
    { key: "description",         label: "Description",                   render: (v) => <span className="max-w-xs truncate block" title={v}>{v ?? "—"}</span> },
    { key: "beneficiaries_count", label: "Beneficiaries",  render: (v) => v ?? "—" },
    { key: "investment_inr",      label: "Investment",     render: (v) => v ? `₹${(v / 100000).toFixed(1)}L` : "—" },
    { key: "outcome",             label: "Outcome",        render: (v) => <span className="max-w-xs truncate block" title={v}>{v ?? "—"}</span> },
  ],
};

// ── Editable fields per entity ─────────────────────────────────────────────────
type EditFieldType = "number" | "text" | "textarea" | "checkbox" | "date" | "select" | "department";
interface EditFieldDef { key: string; label: string; type: EditFieldType; step?: string; options?: string[] }

const EDITABLE_ENTITY_FIELDS: Record<string, EditFieldDef[]> = {
  faculty: [
    { key: "full_name",           label: "Full Name",             type: "text" },
    { key: "institute",           label: "Institute",             type: "text" },
    { key: "department_id",       label: "Department",            type: "department" },
    { key: "gender",               label: "Gender",                type: "select", options: ["male","female","other"] },
    { key: "date_of_birth",        label: "Date of Birth",         type: "date" },
    { key: "email",                label: "Email",                 type: "text" },
    { key: "phone",                label: "Phone",                 type: "text" },
    { key: "designation",         label: "Designation",           type: "select", options: ["professor","associate_professor","assistant_professor","lecturer","hod","dean","director","other"] },
    { key: "qualification",        label: "Qualification",         type: "select", options: ["phd","mtech","me","mba","mphil","mpharm","btech","be","other"] },
    { key: "specialization",       label: "Specialization",        type: "text" },
    { key: "phd_awarded",          label: "PhD Awarded",           type: "checkbox" },
    { key: "phd_year",             label: "PhD Year",              type: "number" },
    { key: "phd_university",       label: "PhD University",        type: "text" },
    { key: "employment_type",     label: "Employment Type",       type: "select", options: ["permanent","contract","visiting","adjunct"] },
    { key: "date_of_joining",      label: "Date of Joining",       type: "date" },
    { key: "date_of_leaving",      label: "Date of Leaving",       type: "date" },
    { key: "experience_teaching", label: "Teaching Exp (Yrs)",    type: "number", step: "0.1" },
    { key: "experience_industry", label: "Industry Exp (Yrs)",    type: "number", step: "0.1" },
    { key: "experience_research", label: "Research Exp (Yrs)",    type: "number", step: "0.1" },
    { key: "pan_number",           label: "PAN Number",            type: "text" },
    { key: "is_sanctioned_post",   label: "Sanctioned Post",       type: "checkbox" },
    { key: "is_active",           label: "Active",                type: "checkbox" },
    { key: "remarks",             label: "Remarks",               type: "textarea" },
  ],
  students: [
    { key: "full_name",     label: "Full Name",         type: "text" },
    { key: "department_id", label: "Department",        type: "department" },
    { key: "gender",         label: "Gender",            type: "select", options: ["male","female","other"] },
    { key: "date_of_birth",  label: "Date of Birth",     type: "date" },
    { key: "category",       label: "Category",          type: "select", options: ["general","obc","sc","st","ews","pwd"] },
    { key: "is_pwd",         label: "PWD",                type: "checkbox" },
    { key: "state_of_domicile", label: "State of Domicile", type: "text" },
    { key: "admission_type", label: "Admission Type",    type: "select", options: ["regular","lateral","nri","management"] },
    { key: "current_year",  label: "Current Year",      type: "number" },
    { key: "email",          label: "Email",              type: "text" },
    { key: "phone",          label: "Phone",              type: "text" },
    { key: "cgpa",          label: "CGPA",              type: "number", step: "0.01" },
    { key: "sgpa_last",     label: "Last SGPA",         type: "number", step: "0.01" },
    { key: "backlogs",      label: "Backlogs",          type: "number" },
    { key: "is_lateral",    label: "Lateral Entry",     type: "checkbox" },
    { key: "is_active",     label: "Active",            type: "checkbox" },
    { key: "remarks",       label: "Remarks",           type: "textarea" },
  ],
  research: [
    { key: "title",          label: "Title",              type: "text" },
    { key: "department_id",  label: "Department",         type: "department" },
    { key: "category",       label: "Category",           type: "select", options: ["journal","conference","book","book_chapter","patent"] },
    { key: "journal_conference_name", label: "Journal / Conference", type: "text" },
    { key: "publisher",      label: "Publisher",          type: "text" },
    { key: "publication_year", label: "Year",              type: "number" },
    { key: "publication_month", label: "Month",             type: "number" },
    { key: "doi",             label: "DOI",                type: "text" },
    { key: "isbn_issn",      label: "ISBN / ISSN",        type: "text" },
    { key: "scopus_id",      label: "Scopus ID",          type: "text" },
    { key: "indexing",       label: "Indexing",           type: "select", options: ["scopus","wos","sci","esci","ugc_care","other"] },
    { key: "impact_factor", label: "Impact Factor",     type: "number", step: "0.001" },
    { key: "citations",     label: "Citations",         type: "number" },
    { key: "authors",        label: "Authors",            type: "text" },
    { key: "is_verified",   label: "Verified",          type: "checkbox" },
    { key: "remarks",       label: "Remarks",           type: "textarea" },
  ],
  patents: [
    { key: "title",         label: "Title",              type: "text" },
    { key: "department_id", label: "Department",         type: "department" },
    { key: "inventors",     label: "Inventors",          type: "text" },
    { key: "status",        label: "Status",            type: "select", options: ["filed","published","granted","abandoned"] },
    { key: "filing_date",   label: "Filing Date",        type: "date" },
    { key: "grant_date",    label: "Grant Date",        type: "date" },
    { key: "country",       label: "Country",           type: "text" },
    { key: "patent_office", label: "Patent Office",      type: "text" },
    { key: "remarks",       label: "Remarks",           type: "textarea" },
  ],
  placements: [
    { key: "student_name",   label: "Student Name",      type: "text" },
    { key: "department_id",  label: "Department",        type: "department" },
    { key: "gender",          label: "Gender",             type: "select", options: ["male","female","other"] },
    { key: "category",       label: "Category",           type: "select", options: ["general","obc","sc","st","ews","pwd"] },
    { key: "placement_type", label: "Placement Type",    type: "select", options: ["campus","off_campus","higher_studies","entrepreneurship"] },
    { key: "package_lpa",    label: "Package (LPA)",    type: "number", step: "0.01" },
    { key: "designation",    label: "Role",             type: "text" },
    { key: "company_name",   label: "Company",            type: "text" },
    { key: "placement_date", label: "Placement Date",     type: "date" },
    { key: "company_city",   label: "Company City",     type: "text" },
    { key: "company_state",  label: "Company State",      type: "text" },
    { key: "is_international",label: "International",   type: "checkbox" },
    { key: "is_verified",    label: "Verified",         type: "checkbox" },
    { key: "remarks",        label: "Remarks",            type: "textarea" },
  ],
  funded_projects: [
    { key: "amount_received", label: "Amount Received (₹)", type: "number" },
    { key: "end_date", label: "End Date", type: "date" },
    { key: "is_ongoing", label: "Ongoing", type: "checkbox" },
    { key: "remarks", label: "Remarks", type: "textarea" },
  ],
  consultancy: [
    { key: "amount_inr", label: "Amount Received (₹)", type: "number" },
    { key: "end_date", label: "End Date", type: "date" },
    { key: "is_ongoing", label: "Ongoing", type: "checkbox" },
    { key: "remarks", label: "Remarks", type: "textarea" },
  ],
  mous: [
    { key: "partner_name",    label: "Partner Name",      type: "text" },
    { key: "partner_country", label: "Country",            type: "text" },
    { key: "partner_type",    label: "Partner Type",      type: "select", options: ["academic","industry","research","international","government"] },
    { key: "mou_type",        label: "MoU Type",            type: "text" },
    { key: "signed_date",     label: "Signed Date",        type: "date" },
    { key: "purpose",         label: "Purpose",          type: "textarea" },
    { key: "valid_until",     label: "Valid Until",      type: "date" },
    { key: "activities_conducted", label: "Activities Conducted", type: "number" },
    { key: "is_active",       label: "Active",           type: "checkbox" },
    { key: "remarks",         label: "Remarks",            type: "textarea" },
  ],
  events: [
    { key: "title",                label: "Title",               type: "text" },
    { key: "event_type",          label: "Event Type",          type: "select", options: ["conference","workshop","seminar","fdp","webinar","cultural","sports","other"] },
    { key: "is_organized",        label: "Organized (vs Attended)", type: "checkbox" },
    { key: "start_date",          label: "Start Date",          type: "date" },
    { key: "end_date",            label: "End Date",            type: "date" },
    { key: "duration_days",       label: "Duration (Days)",       type: "number" },
    { key: "venue",                label: "Venue",                type: "text" },
    { key: "participants_count",   label: "Participants",         type: "number" },
    { key: "faculty_participants", label: "Faculty Participants", type: "number" },
    { key: "student_participants", label: "Student Participants", type: "number" },
    { key: "external_participants",label: "External Participants",type: "number" },
    { key: "is_international",    label: "International",       type: "checkbox" },
    { key: "funding_amount",      label: "Funding Amount (₹)",  type: "number" },
    { key: "remarks",             label: "Remarks",              type: "textarea" },
  ],
  energy: [
    { key: "month",                  label: "Month (1-12)",        type: "number" },
    { key: "electricity_kwh",      label: "Grid (kWh)",          type: "number", step: "0.01" },
    { key: "electricity_cost_inr", label: "Bill (₹)",            type: "number" },
    { key: "solar_kwh",            label: "Solar (kWh)",         type: "number", step: "0.01" },
    { key: "wind_kwh",              label: "Wind (kWh)",          type: "number", step: "0.01" },
    { key: "other_renewable_kwh",  label: "Other Renewable (kWh)",type: "number", step: "0.01" },
    { key: "diesel_liters",        label: "Diesel (L)",          type: "number", step: "0.01" },
    { key: "lpg_kg",                label: "LPG (kg)",             type: "number", step: "0.01" },
    { key: "cng_kg",                label: "CNG (kg)",             type: "number", step: "0.01" },
    { key: "ghg_scope1_tco2e",     label: "GHG Scope 1",         type: "number", step: "0.001" },
    { key: "ghg_scope2_tco2e",     label: "GHG Scope 2",         type: "number", step: "0.001" },
    { key: "remarks",               label: "Remarks",              type: "textarea" },
  ],
  water: [
    { key: "month",                  label: "Month (1-12)",       type: "number" },
    { key: "municipal_kl",           label: "Municipal (kL)",    type: "number", step: "0.01" },
    { key: "borewell_kl",            label: "Borewell (kL)",     type: "number", step: "0.01" },
    { key: "rainwater_harvested_kl", label: "Rainwater (kL)",    type: "number", step: "0.01" },
    { key: "recycled_treated_kl",    label: "Recycled (kL)",     type: "number", step: "0.01" },
    { key: "cost_inr",               label: "Cost (₹)",           type: "number" },
    { key: "remarks",                label: "Remarks",             type: "textarea" },
  ],
  waste: [
    { key: "month",           label: "Month (1-12)",     type: "number" },
    { key: "waste_type",      label: "Waste Type",       type: "select", options: ["solid","biomedical","ewaste","hazardous","recyclable"] },
    { key: "generated_kg",    label: "Generated (kg)",    type: "number", step: "0.01" },
    { key: "recycled_kg",     label: "Recycled (kg)",    type: "number", step: "0.01" },
    { key: "disposed_kg",     label: "Disposed (kg)",    type: "number", step: "0.01" },
    { key: "disposal_method", label: "Disposal Method",  type: "text" },
    { key: "vendor_name",     label: "Vendor",           type: "text" },
    { key: "cost_inr",        label: "Cost (₹)",          type: "number" },
    { key: "remarks",         label: "Remarks",            type: "textarea" },
  ],
  awards: [
    { key: "title",             label: "Award",              type: "text" },
    { key: "awarding_body",     label: "Awarding Body",      type: "text" },
    { key: "recipient_name",    label: "Recipient",         type: "text" },
    { key: "recipient_type",    label: "Recipient Type",     type: "text" },
    { key: "award_date",        label: "Award Date",        type: "date" },
    { key: "category",          label: "Category",           type: "text" },
    { key: "is_national",       label: "National",           type: "checkbox" },
    { key: "is_international",  label: "International",     type: "checkbox" },
    { key: "prize_amount",      label: "Prize Amount (₹)",  type: "number" },
    { key: "remarks",           label: "Remarks",             type: "textarea" },
  ],
  sdg: [
    { key: "title",               label: "Activity",       type: "text" },
    { key: "description",         label: "Description",     type: "textarea" },
    { key: "activity_type",       label: "Type",             type: "text" },
    { key: "sdg_primary",         label: "SDG Goal (1-17)", type: "number" },
    { key: "sdg_secondary",       label: "Secondary SDGs",   type: "text" },
    { key: "beneficiaries_count", label: "Beneficiaries",   type: "number" },
    { key: "investment_inr",      label: "Investment (₹)", type: "number" },
    { key: "outcome",             label: "Outcome",         type: "textarea" },
    { key: "remarks",             label: "Remarks",           type: "textarea" },
  ],
};

// ── Page ───────────────────────────────────────────────────────────────────────

// ── Error boundary ──────────────────────────────────────────────────────────────
// Safety net: if any future bug throws during render (bad data shape, etc.),
// this shows a recoverable message instead of the blank white screen that
// happens by default when an uncaught error unmounts the whole React tree.

class MasterDataErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("Master Data page crashed:", error, info);
  }
  render() {
    if (this.state.error) {
      return (
        <div className="flex h-full items-center justify-center p-8">
          <div className="max-w-md text-center space-y-3">
            <AlertCircle className="w-8 h-8 text-destructive mx-auto" />
            <h2 className="font-semibold text-foreground">Something went wrong</h2>
            <p className="text-sm text-muted-foreground">
              This page hit an unexpected error and couldn't continue rendering.
              Try again — if it keeps happening on the same record, that record
              likely has a data value the UI doesn't handle yet.
            </p>
            <p className="text-xs font-mono text-muted-foreground bg-muted rounded-lg px-3 py-2 break-words">
              {this.state.error.message}
            </p>
            <button
              onClick={() => this.setState({ error: null })}
              className="px-4 py-2 text-sm font-medium bg-[#003087] hover:bg-[#002266] text-white rounded-lg transition"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function MasterDataPage() {
  return (
    <MasterDataErrorBoundary>
      <MasterDataPageInner />
    </MasterDataErrorBoundary>
  );
}

function MasterDataPageInner() {
  const [activeTab, setActiveTab] = useState("faculty");
  const [year, setYear] = useState("2024-25");
  const [search, setSearch] = useState("");
  const [showTemplateEditor, setShowTemplateEditor] = useState(false);

  const { user } = useAuthStore();
  const isAdmin  = user ? hasMinimumRole(user.role, "iqac_admin") : false;
  const canEdit  = user ? hasMinimumRole(user.role, "data_entry_operator") : false;

  const activeTabDef = TABS.find((t) => t.key === activeTab)!;
  const Icon = activeTabDef.icon;

  useEffect(() => { setSearch(""); }, [activeTab]);

  // Build template download URL — appends custom label overrides as query params.
  // Only fields that are actually in the template (templated !== false) are ever
  // sent, since backend/admin-only fields like is_verified/is_active have no
  // corresponding template column to relabel.
  const handleDownloadTemplate = () => {
    const allLabels = loadCustomLabels();
    const entityLabels = allLabels[activeTab] ?? {};
    const templatedCols = (COLUMNS[activeTab] ?? []).filter((c) => c.templated !== false);
    const params = new URLSearchParams();
    templatedCols.forEach((c) => {
      const v = entityLabels[c.key];
      if (v) params.append(`label_${c.key}`, v);
    });
    // Include current data for the selected year — same unified "download,
    // edit, upload back" flow as the Data Upload module. If there's no data
    // yet for this year, the backend returns a blank template automatically.
    params.append("academic_year", year);
    const qs = params.toString();

    apiClient.get(`/uploads/templates/${activeTabDef.templateKey}${qs ? `?${qs}` : ""}`, {
      responseType: "blob",
    }).then((res) => {
      const blob = new Blob([res.data]);
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${activeTabDef.templateKey}_${year}.xlsx`;
      link.click();
      URL.revokeObjectURL(link.href);
    });
  };

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 border-r border-border bg-muted/20 p-3 space-y-0.5">
        <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Data Categories
        </div>
        {TABS.map((tab) => {
          const TabIcon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? "bg-[#003087] text-white" : "text-foreground hover:bg-muted"
              }`}
            >
              <TabIcon className="w-4 h-4 flex-shrink-0" />
              <span>{tab.label}</span>
              {isActive && <ChevronRight className="w-3.5 h-3.5 ml-auto" />}
            </button>
          );
        })}
      </aside>

      {/* Main */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-4">

          {/* Header */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${activeTabDef.color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">{activeTabDef.label}</h1>
                <p className="text-xs text-muted-foreground">Master data — year-wise records</p>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <label className="text-sm text-muted-foreground">Year:</label>
              <select
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className="rounded-lg border border-input bg-background text-sm px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#003087]"
              >
                {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>

              {/* Download current data (or blank template if none yet) — all roles */}
              <button
                onClick={handleDownloadTemplate}
                title={`Download all ${year} ${activeTabDef.label} records to edit and re-upload`}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#003087] text-[#003087] text-sm font-medium hover:bg-[#003087]/5 transition"
              >
                <Download className="w-3.5 h-3.5" />
                Download Data
              </button>

              {/* Edit template — IQAC Admin + Super Admin only */}
              {isAdmin && (
                <button
                  onClick={() => setShowTemplateEditor(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-amber-400 text-amber-700 bg-amber-50 text-sm font-medium hover:bg-amber-100 transition"
                >
                  <Settings2 className="w-3.5 h-3.5" />
                  Edit Template
                </button>
              )}
            </div>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={SEARCH_HINTS[activeTab] ?? "Search records…"}
              className="w-full pl-9 pr-9 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-[#003087]"
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Table */}
          <EntityTable entity={activeTab} year={year} search={search} canEdit={canEdit} />
        </div>
      </div>

      {/* Template editor modal */}
      {showTemplateEditor && isAdmin && (
        <TemplateEditorModal
          entity={activeTab}
          entityLabel={activeTabDef.label}
          onClose={() => setShowTemplateEditor(false)}
        />
      )}
    </div>
  );
}

// ── Entity table ───────────────────────────────────────────────────────────────

function EntityTable({ entity, year, search, canEdit }: {
  entity: string; year: string; search: string; canEdit: boolean;
}) {
  const [editingRow, setEditingRow] = useState<any | null>(null);
  const qc = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["master", entity, year, search],
    queryFn: async () => {
      const params = { academic_year: year, size: 1000, ...(search.trim() ? { search: search.trim() } : {}) };
      const first = await apiClient.get(`/master/${entity}`, { params: { ...params, page: 1 } });
      const totalPages = first.data.pages ?? 1;
      if (totalPages <= 1) return first.data;

      // Value lists and AND filters must use every matching server page, not
      // just the rows that happen to be visible in the old page view.
      const remaining = await Promise.all(
        Array.from({ length: totalPages - 1 }, (_, index) => apiClient.get(`/master/${entity}`, {
          params: { ...params, page: index + 2 },
        })),
      );
      return { ...first.data, items: [first.data.items ?? [], ...remaining.flatMap((response) => response.data.items ?? [])] };
    },
  });

  // Master-data responses carry department_id. Resolve it once to a readable
  // name/code for every table instead of exposing internal UUIDs in the UI.
  const { data: departments = [] } = useQuery<{ id: string; name: string; code: string }[]>({
    queryKey: ["departments"],
    queryFn: async () => (await apiClient.get("/auth/departments")).data,
    staleTime: 1000 * 60 * 10,
    enabled: DEPARTMENT_MANAGED_ENTITIES.has(entity),
  });
  const departmentNames = useMemo(
    () => new Map(departments.map((department) => [department.id, `${department.name} (${department.code})`])),
    [departments],
  );

  // Apply any custom labels saved by admin
  const allCustomLabels = loadCustomLabels();
  const customLabels = allCustomLabels[entity] ?? {};
  const baseCols = COLUMNS[entity] ?? [];
  const columns = baseCols.map((c) => ({
    ...c,
    label: customLabels[c.key] ?? c.label,
  }));

  const editFields = EDITABLE_ENTITY_FIELDS[entity];

  if (isLoading) return <TableSkeleton />;
  if (error) return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center flex flex-col items-center gap-2">
      <AlertCircle className="w-5 h-5 text-destructive" />
      <p className="text-destructive text-sm">Failed to load data. Ensure the backend is running.</p>
    </div>
  );

  const items = (data?.items ?? []).map((item: any) => ({
    ...item,
    ...(DEPARTMENT_MANAGED_ENTITIES.has(entity) ? {
      department_name: item.department_id ? departmentNames.get(item.department_id) ?? "Unknown department" : "—",
    } : {}),
  }));
  return (
    <div className="space-y-3">
      <ExcelFilterTable
        columns={columns}
        rows={items}
        resetKey={`${entity}:${year}:${search}`}
        emptyMessage={search ? `No records match "${search}" for ${year}.` : `No records for ${year}. Upload via Data Upload module.`}
        renderActions={canEdit && editFields ? (row) => (
          <button onClick={() => setEditingRow(row)} className="inline-flex items-center gap-1 text-xs font-medium text-[#003087] hover:underline">
            <Pencil className="w-3.5 h-3.5" /> Edit
          </button>
        ) : undefined}
      />
      {/* Legacy table markup is retained below only as a reference while the
          reusable ExcelFilterTable owns rendering, filtering and pagination.
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          {search
            ? <><strong>{total}</strong> result{total !== 1 ? "s" : ""} for "<em>{search}</em>" in <strong>{year}</strong></>
            : <><strong>{total}</strong> records for <strong>{year}</strong></>
          }
        </span>
        <span className="text-muted-foreground text-xs">Page {page} of {pages}</span>
      </div>

      <div className="rounded-xl border border-border overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              {columns.map((col) => (
                <th key={col.key} className="text-left px-4 py-3 font-medium text-muted-foreground whitespace-nowrap text-xs uppercase tracking-wide">
                  {col.label}
                  {col.required && <span className="text-destructive ml-0.5">*</span>}
                </th>
              ))}
              {canEdit && editFields && (
                <th className="text-left px-4 py-3 font-medium text-muted-foreground whitespace-nowrap text-xs uppercase tracking-wide">Actions</th>
              )}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (canEdit && editFields ? 1 : 0)} className="px-4 py-12 text-center text-muted-foreground">
                  {search
                    ? `No records match "${search}" for ${year}.`
                    : `No records for ${year}. Upload via Data Upload module.`
                  }
                </td>
              </tr>
            ) : (
              items.map((row: any) => (
                <tr key={row.id} className="border-b border-border last:border-0 hover:bg-muted/20 transition">
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 text-foreground whitespace-nowrap">
                      {col.render ? col.render(row[col.key], row) : (row[col.key] ?? "—")}
                    </td>
                  ))}
                  {canEdit && editFields && (
                    <td className="px-4 py-3 whitespace-nowrap">
                      <button
                        onClick={() => setEditingRow(row)}
                        className="inline-flex items-center gap-1 text-xs font-medium text-[#003087] hover:underline"
                      >
                        <Pencil className="w-3.5 h-3.5" /> Edit
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="flex items-center justify-end gap-2">
          <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border text-sm hover:bg-muted disabled:opacity-40 transition">
            <ChevronLeft className="w-3.5 h-3.5" /> Prev
          </button>
          <span className="text-sm text-muted-foreground px-2">{page} / {pages}</span>
          <button disabled={page === pages} onClick={() => setPage((p) => p + 1)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border text-sm hover:bg-muted disabled:opacity-40 transition">
            Next <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
      */}

      {editingRow && editFields && (
        <RecordEditModal
          entity={entity}
          row={editingRow}
          fields={editFields}
          onClose={() => setEditingRow(null)}
          onSaved={() => {
            setEditingRow(null);
            qc.invalidateQueries({ queryKey: ["master", entity, year] });
          }}
        />
      )}
    </div>
  );
}

// ── Template Editor Modal ──────────────────────────────────────────────────────
// Saves custom column label overrides to localStorage. These labels are then
// applied:
//   1. In the master table column headers (via customLabels above).
//   2. In the downloaded template — passed as ?label_fieldName=CustomLabel
//      query params, read by the backend in uploads.py::download_template.

function TemplateEditorModal({ entity, entityLabel, onClose }: {
  entity: string; entityLabel: string; onClose: () => void;
}) {
  const allLabels = loadCustomLabels();
  const allCols   = COLUMNS[entity] ?? [];
  // Only fields that actually exist in the downloadable template can be
  // relabeled here — admin/DB-only fields (is_verified, is_active, etc.)
  // have no template column, so relabeling them would silently do nothing.
  const baseCols     = allCols.filter((c) => c.templated !== false);
  const excludedCols = allCols.filter((c) => c.templated === false);

  const [labels, setLabels] = useState<Record<string, string>>(() => {
    const saved = allLabels[entity] ?? {};
    return Object.fromEntries(baseCols.map((c) => [c.key, saved[c.key] ?? c.label]));
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    const updated = { ...loadCustomLabels(), [entity]: labels };
    saveCustomLabels(updated);
    setSaved(true);
    setTimeout(() => { setSaved(false); onClose(); }, 1200);
  };

  const handleReset = () => {
    const defaults = Object.fromEntries(baseCols.map((c) => [c.key, c.label]));
    setLabels(defaults);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-xl bg-card border border-border shadow-xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Settings2 className="w-4 h-4 text-amber-600" />
            <div>
              <h3 className="font-semibold text-foreground">Edit Template — {entityLabel}</h3>
              <p className="text-xs text-muted-foreground">Rename column headers in the downloadable template & master table</p>
            </div>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-4 h-4" /></button>
        </div>

        <div className="px-5 py-4 max-h-[55vh] overflow-y-auto space-y-2">
          <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-700 flex gap-2 mb-3">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            Labels update the downloaded template headers and this table's column names. Internal field keys stay unchanged.
          </div>

          {excludedCols.length > 0 && (
            <div className="rounded-lg bg-muted/50 border border-border px-3 py-2 text-xs text-muted-foreground flex gap-2 mb-3">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              <span>
                <strong>{excludedCols.map((c) => c.label).join(", ")}</strong>{" "}
                {excludedCols.length === 1 ? "isn't" : "aren't"} shown here because{" "}
                {excludedCols.length === 1 ? "it's" : "they're"} set by admins in the table itself,
                not filled in via the uploaded file — so there's no template column to rename.
              </span>
            </div>
          )}

          {/* Column header */}
          <div className="grid grid-cols-2 gap-3 px-1 pb-1">
            <span className="text-xs font-semibold text-muted-foreground uppercase">Field Key</span>
            <span className="text-xs font-semibold text-muted-foreground uppercase">Column Label (editable)</span>
          </div>

          {baseCols.map((col) => (
            <div key={col.key} className="grid grid-cols-2 gap-3 items-center">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-mono bg-muted border border-border rounded px-2 py-1 truncate text-foreground" title={col.key}>
                  {col.key}
                </span>
                {col.required && <span className="text-destructive text-xs font-bold" title="Required field">*</span>}
              </div>
              <input
                type="text"
                value={labels[col.key] ?? col.label}
                onChange={(e) => setLabels((l) => ({ ...l, [col.key]: e.target.value }))}
                className="rounded-lg border border-input bg-background text-sm px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#003087]"
              />
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between px-5 py-4 border-t border-border">
          <button onClick={handleReset} className="text-xs text-muted-foreground hover:text-foreground underline">
            Reset to defaults
          </button>
          <div className="flex items-center gap-2">
            <button onClick={onClose} className="px-4 py-2 text-sm text-muted-foreground hover:bg-muted rounded-lg transition">
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-[#003087] hover:bg-[#002266] text-white rounded-lg transition"
            >
              {saved ? <><CheckCircle2 className="w-3.5 h-3.5" /> Saved!</> : "Save Labels"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Record Edit Modal ──────────────────────────────────────────────────────────

// FastAPI error responses come in different shapes depending on the failure:
//   - HTTPException(detail="some string")          -> detail is a string
//   - Pydantic validation error (422)               -> detail is an ARRAY of
//     objects like [{type, loc, msg, input}, ...]
// Rendering that array directly as JSX ({error}) crashes the whole page with
// "Objects are not valid as a React child" — no error boundary catches it,
// so the entire app unmounts to a blank screen. This always converts to a
// plain string first, however the backend responds.
function extractErrorMessage(e: any): string {
  const detail = e?.response?.data?.detail;
  if (!detail) return e?.message || "Failed to save.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: any) => {
        if (typeof d === "string") return d;
        const field = Array.isArray(d?.loc) ? d.loc[d.loc.length - 1] : d?.loc;
        return field ? `${field}: ${d?.msg ?? "invalid value"}` : (d?.msg ?? "invalid value");
      })
      .join("; ");
  }
  if (typeof detail === "object") return detail.msg ?? JSON.stringify(detail);
  return String(detail);
}

function RecordEditModal({ entity, row, fields, onClose, onSaved }: {
  entity: string; row: any; fields: EditFieldDef[]; onClose: () => void; onSaved: () => void;
}) {
  const [values, setValues] = useState<Record<string, any>>(() => {
    const init: Record<string, any> = {};
    for (const f of fields) init[f.key] = row[f.key] ?? (f.type === "checkbox" ? false : "");
    return init;
  });
  const [error, setError] = useState<string | null>(null);
  const needsDepartment = fields.some((field) => field.type === "department");
  const { data: departments = [] } = useQuery<{ id: string; name: string; code: string }[]>({
    queryKey: ["departments"],
    queryFn: async () => (await apiClient.get("/auth/departments")).data,
    staleTime: 1000 * 60 * 10,
    enabled: needsDepartment,
  });

  const mutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, any> = {};
      for (const f of fields) {
        const v = values[f.key];
        if (f.type === "number") {
          payload[f.key] = v === "" || v === null || v === undefined ? null : Number(v);
        } else if (f.type === "date") {
          // Empty date input must be sent as null, not "" — an empty string
          // fails backend date validation and previously crashed the page
          // (see error-rendering fix below for why that happened).
          payload[f.key] = v === "" || v === null || v === undefined ? null : v;
        } else if (f.type === "select" || f.type === "department") {
          payload[f.key] = v === "" ? null : v;
        } else {
          payload[f.key] = v;
        }
      }
      return (await apiClient.put(`/master/${entity}/${row.id}`, payload)).data;
    },
    onSuccess: onSaved,
    onError: (e: any) => setError(extractErrorMessage(e)),
  });

  const displayName = row.full_name || row.title || row.partner_name || row.student_name || row.recipient_name || row.enrollment_no || row.employee_id || "Record";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-xl bg-card border border-border shadow-lg">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <h3 className="font-semibold text-foreground">Edit Record</h3>
            <p className="text-xs text-muted-foreground truncate max-w-[280px]">{displayName}</p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-4 h-4" /></button>
        </div>

        <div className="px-5 py-4 space-y-3 max-h-[60vh] overflow-y-auto">
          {error && <p className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</p>}
          {fields.map((f) => (
            <div key={f.key} className="space-y-1">
              {f.type === "checkbox" ? (
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <input type="checkbox" checked={!!values[f.key]}
                    onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.checked }))}
                    className="rounded border-input" />
                  {f.label}
                </label>
              ) : f.type === "select" || f.type === "department" ? (
                <>
                  <label className="text-xs font-medium text-muted-foreground">{f.label}</label>
                  <select value={values[f.key] ?? ""}
                    onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                    className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#003087]">
                    <option value="">— Select —</option>
                    {f.type === "department"
                      ? departments.map((department) => <option key={department.id} value={department.id}>{department.name} ({department.code})</option>)
                      : f.options?.map((o) => <option key={o} value={o}>{o.replace(/_/g, " ")}</option>)}
                  </select>
                </>
              ) : (
                <>
                  <label className="text-xs font-medium text-muted-foreground">{f.label}</label>
                  {f.type === "textarea"
                    ? <textarea rows={3} value={values[f.key] ?? ""}
                        onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                        className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#003087]" />
                    : <input type={f.type === "number" ? "number" : f.type === "date" ? "date" : "text"}
                        step={f.step} value={values[f.key] ?? ""}
                        onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                        className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#003087]" />
                  }
                </>
              )}
            </div>
          ))}
        </div>

        <div className="flex items-center justify-end gap-2 px-5 py-4 border-t border-border">
          <button onClick={onClose} disabled={mutation.isPending}
            className="px-4 py-2 text-sm text-muted-foreground hover:bg-muted rounded-lg transition">Cancel</button>
          <button onClick={() => mutation.mutate()} disabled={mutation.isPending}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-[#003087] hover:bg-[#002266] text-white rounded-lg transition disabled:opacity-50">
            {mutation.isPending && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Helper components ──────────────────────────────────────────────────────────

function Badge({ value }: { value: string }) {
  return (
    <span className="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-muted text-muted-foreground capitalize">
      {value?.replace(/_/g, " ")}
    </span>
  );
}

function StatusPill({ active }: { active: boolean }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
      {active ? "Active" : "Inactive"}
    </span>
  );
}

const SDG_COLORS: Record<number, string> = {
  1:"bg-red-600",2:"bg-yellow-500",3:"bg-green-600",4:"bg-red-400",5:"bg-orange-500",
  6:"bg-blue-400",7:"bg-yellow-400",8:"bg-red-500",9:"bg-orange-600",10:"bg-pink-600",
  11:"bg-orange-400",12:"bg-amber-600",13:"bg-green-700",14:"bg-blue-600",
  15:"bg-green-500",16:"bg-blue-700",17:"bg-blue-800",
};

function SDGBadge({ goal }: { goal: number }) {
  return (
    <span className={`inline-flex items-center justify-center w-6 h-6 rounded text-white text-xs font-bold ${SDG_COLORS[goal] ?? "bg-gray-400"}`}>
      {goal}
    </span>
  );
}

function TableSkeleton() {
  return (
    <div className="rounded-xl border border-border overflow-hidden">
      <div className="h-10 bg-muted/40 border-b border-border" />
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="h-12 border-b border-border last:border-0 animate-pulse bg-muted/20" />
      ))}
    </div>
  );
}
