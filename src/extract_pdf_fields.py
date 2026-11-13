#!/usr/bin/env python3
"""
Local batch PDF field extraction.

Processes PDFs from an input folder, extracts text-layer fields with pdfplumber,
copies originals into processed/manual_review/failed folders, and writes a local
Excel summary. No files are uploaded and source PDFs are never modified.
"""

from __future__ import annotations

import argparse
import html
import io
import json
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


OUTPUT_COLUMNS = [
    "File Name",
    "Supplier name",
    "Supplier Recognized",
    "Extraction Confidence",
    "Description",
    "Product Numbers",
    "Line Item Confidence",
    "Invoice number",
    "Document Type",
    "Document Date",
    "Sales Order Number",
    "Customer PO / Order Number",
    "Customer Number",
    "Bill of Lading Number",
    "Ship Date",
    "Payment Terms",
    "Subtotal Amount",
    "Sales Tax",
    "Total Amount",
    "Balance Due",
    "Line Items",
    "Recommended Account Code",
    "Recommended Account Name",
    "Classification Confidence",
    "Inventory Candidate",
    "Possible Inventory Account",
    "Classification Notes",
    "Readable Text Characters",
    "Wrapped PDF",
    "Extraction Method",
    "Notes / Errors",
    "Final File Name",
    "Output Folder",
    "Processing Status",
]

OUTPUT_COLUMN_WIDTHS = [
    24,
    28,
    18,
    20,
    70,
    34,
    22,
    18,
    18,
    16,
    20,
    24,
    18,
    22,
    16,
    18,
    16,
    14,
    16,
    16,
    80,
    24,
    28,
    24,
    20,
    28,
    56,
    22,
    14,
    30,
    54,
    32,
    44,
    20,
]

INVALID_FILENAME_CHARS = r'<>:"/\|?*'
# Public demo configuration. These suppliers and account numbers are fictitious.
DEMO_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "demo_rules.json"
with DEMO_CONFIG_PATH.open(encoding="utf-8") as config_file:
    DEMO_CONFIG = json.load(config_file)
KNOWN_SUPPLIERS = {entry["name"] for entry in DEMO_CONFIG["suppliers"]}
ACCOUNT_RULES = DEMO_CONFIG["account_rules"]
ACCOUNT_REFERENCE_ROWS = [
    (entry["code"], entry["name"], entry["use_when"])
    for entry in DEMO_CONFIG["account_reference"]
]
DEMO_CODES = DEMO_CONFIG["codes"]

WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


@dataclass
class PdfPayload:
    bytes_data: bytes
    is_wrapped: bool
    wrapper_note: str


@dataclass
class ExtractedFields:
    supplier_name: str = ""
    supplier_recognized: str = ""
    extraction_confidence: str = ""
    description: str = ""
    product_numbers: str = ""
    line_item_confidence: str = ""
    invoice_number: str = ""
    document_type: str = ""
    document_date: str = ""
    sales_order_number: str = ""
    customer_order_number: str = ""
    customer_number: str = ""
    bill_of_lading_number: str = ""
    ship_date: str = ""
    payment_terms: str = ""
    subtotal_amount: str = ""
    sales_tax: str = ""
    total_amount: str = ""
    balance_due: str = ""
    line_items: str = ""
    recommended_account_code: str = ""
    recommended_account_name: str = ""
    classification_confidence: str = ""
    inventory_candidate: str = ""
    possible_inventory_account: str = ""
    classification_notes: str = ""
    readable_text_characters: str = ""
    wrapped_pdf: str = ""
    notes: list[str] | None = None

    def __post_init__(self) -> None:
        if self.notes is None:
            self.notes = []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract supplier, description, and invoice/order fields from PDFs locally."
    )
    parser.add_argument("--input", required=True, help="Folder containing source PDF files.")
    parser.add_argument(
        "--output",
        default="pdf_extraction_results.xlsx",
        help="Excel output path or filename. Relative filenames are placed under --output-root.",
    )
    parser.add_argument(
        "--output-root",
        default=None,
        help="Root folder for processed, manual_review, failed, and default Excel output.",
    )
    parser.add_argument(
        "--scan-policy",
        choices=("warn", "manual_review"),
        default="manual_review",
        help=(
            "How to handle scan-like PDFs. 'warn' keeps complete files in processed with a note; "
            "'manual_review' copies scan-like files to manual_review even when fields are found."
        ),
    )
    return parser.parse_args()


def sanitize_filename_part(value: str, default: str = "unknown", max_len: int = 120) -> str:
    cleaned = "".join("_" if char in INVALID_FILENAME_CHARS else char for char in value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    cleaned = re.sub(r"_+", "_", cleaned)
    if not cleaned:
        cleaned = default
    if cleaned.upper() in WINDOWS_RESERVED_NAMES:
        cleaned = f"{cleaned}_file"
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip(" ._")
    return cleaned or default


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}__{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def find_pdf_payload(source_path: Path) -> PdfPayload:
    data = source_path.read_bytes()
    pdf_start = data.find(b"%PDF")
    eof_end = data.rfind(b"%%EOF")

    if pdf_start == -1 or eof_end == -1 or eof_end < pdf_start:
        raise ValueError("No embedded PDF payload found (%PDF/%%EOF markers missing).")

    eof_end += len(b"%%EOF")
    while eof_end < len(data) and data[eof_end : eof_end + 1] in (b"\r", b"\n", b" ", b"\t"):
        eof_end += 1

    payload = data[pdf_start:eof_end]
    leading = data[:pdf_start].strip()
    trailing = data[eof_end:].strip()
    is_wrapped = bool(leading or trailing)
    wrapper_note = "wrapped PDF payload extracted" if is_wrapped else "normal PDF"
    return PdfPayload(payload, is_wrapped, wrapper_note)


def extract_text_with_pdfplumber(payload: PdfPayload) -> tuple[str, str]:
    try:
        import pdfplumber  # type: ignore
    except ImportError as exc:
        raise RuntimeError("pdfplumber is not installed in this Python environment.") from exc

    pages_text: list[str] = []
    with pdfplumber.open(io.BytesIO(payload.bytes_data)) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
            if page_text.strip():
                pages_text.append(f"--- Page {index} ---\n{page_text}")

    method = "pdfplumber text layer"
    if payload.is_wrapped:
        method += " after wrapper unwrap"
    return "\n".join(pages_text), method


def extract_text_with_optional_ocr(_payload: PdfPayload) -> tuple[str, str]:
    """Future hook for local OCR such as Tesseract. Intentionally inactive in v1."""
    return "", "local OCR not enabled"


def useful_lines(text: str) -> list[str]:
    lines = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if line and not re.fullmatch(r"-+ Page \d+ -+", line):
            lines.append(line)
    return lines


def find_value_near_label(
    lines: list[str],
    label_patterns: Iterable[str],
    value_pattern: str | None = None,
    lookahead: int = 3,
) -> str:
    compiled_labels = [re.compile(pattern, re.IGNORECASE) for pattern in label_patterns]
    compiled_value = re.compile(value_pattern, re.IGNORECASE) if value_pattern else None

    for idx, line in enumerate(lines):
        for label in compiled_labels:
            match = label.search(line)
            if not match:
                continue

            after = line[match.end() :]
            after = re.sub(r"^[\s:#\-]+", "", after).strip()
            if after:
                if compiled_value:
                    value_match = compiled_value.search(after)
                    if value_match:
                        return value_match.group(1 if value_match.groups() else 0).strip()
                else:
                    return clean_field_value(after)

            for next_line in lines[idx + 1 : idx + 1 + lookahead]:
                if looks_like_label_only(next_line):
                    continue
                if compiled_value:
                    value_match = compiled_value.search(next_line)
                    if value_match:
                        return value_match.group(1 if value_match.groups() else 0).strip()
                else:
                    return clean_field_value(next_line)
    return ""


def looks_like_label_only(line: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z /#&()'-]{2,35}:?", line.strip()))


def clean_field_value(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" :-")
    return value[:500].strip()


def extract_description(lines: list[str]) -> str:
    line_items = extract_line_items(lines)
    if line_items:
        return primary_description_from_line_items(line_items)

    labels = [
        r"\bProduct\s+Description\b",
        r"\bItem\s+Description\b",
        r"\bDescription\b",
    ]
    description = find_value_near_label(lines, labels, lookahead=4)
    if description:
        return description

    for idx, line in enumerate(lines):
        if re.fullmatch(r"(Product\s+)?Description:?", line, re.IGNORECASE):
            collected = []
            for next_line in lines[idx + 1 : idx + 5]:
                if re.search(r"\b(Qty|Quantity|Price|Amount|Total|Invoice|Order)\b", next_line, re.I):
                    break
                collected.append(next_line)
            if collected:
                return clean_field_value(" ".join(collected))
    return ""


def primary_description_from_line_items(line_items: str) -> str:
    first_item = line_items.split(";", 1)[0].strip()
    return clean_field_value(first_item)


def extract_invoice_number(lines: list[str]) -> str:
    structured = extract_structured_values(lines)
    for key in ("invoice_number", "sales_order_number", "bill_of_lading_number", "customer_order_number"):
        if structured.get(key):
            return structured[key]

    labels = [
        r"\bInvoice\s*(?:No\.?|Number|#)?\b",
        r"\bSales\s+Invoice\s*(?:No\.?|Number|#)?\b",
        r"\bSales\s+Order\s*(?:No\.?|Number|#)?\b",
        r"\bSO\s*(?:No\.?|Number|#)?\b",
        r"\bOrder\s*(?:No\.?|Number|#)\b",
        r"\bP\.?O\.?\s*(?:No\.?|Number|#)?\b",
        r"\bPO\s*(?:No\.?|Number|#)?\b",
    ]
    value_pattern = r"\b([A-Z]?\d[\dA-Z\-]{2,24})\b"
    invoice = find_value_near_label(lines, labels, value_pattern=value_pattern, lookahead=4)
    if invoice:
        return invoice

    # Fallback: favor standalone numeric identifiers near invoice/order text.
    for idx, line in enumerate(lines):
        if re.search(r"\b(invoice|sales order|order|po|p\.o\.)\b", line, re.I):
            window = " ".join(lines[max(0, idx - 1) : idx + 3])
            candidates = re.findall(r"\b(?!20\d{2}\b)\d{4,12}\b", window)
            if candidates:
                return candidates[0]
    return ""


def extract_supplier_name(lines: list[str]) -> str:
    normalized = normalize_known_supplier(" ".join(lines[:40]))
    if normalized:
        return normalized

    labeled_supplier = find_value_near_label(
        lines,
        [
            r"\bSupplier\b",
            r"\bVendor\b",
            r"\bFrom\b",
            r"\bSold\s+By\b",
            r"\bRemit\s+To\b",
        ],
        lookahead=2,
    )
    if labeled_supplier and is_plausible_supplier(labeled_supplier):
        return labeled_supplier

    top_lines = lines[:30]
    scored: list[tuple[int, str]] = []
    repeated_counts: dict[str, int] = {}
    for line in lines:
        repeated_counts[line] = repeated_counts.get(line, 0) + 1

    for position, line in enumerate(top_lines):
        if not is_plausible_supplier(line):
            continue
        score = 0
        if position < 10:
            score += 3
        if re.search(r"\b(co\.?|company|inc\.?|llc|ltd\.?|corp\.?|corporation|limited)\b", line, re.I):
            score += 5
        if repeated_counts.get(line, 0) > 1:
            score += 2
        if re.search(r"\b(invoice|order|quote|statement)\b", line, re.I):
            score -= 4
        scored.append((score, line))

    if scored:
        scored.sort(key=lambda item: (-item[0], len(item[1])))
        return normalize_known_supplier(scored[0][1]) or clean_field_value(scored[0][1])
    return ""


def normalize_known_supplier(text: str) -> str:
    """Match public demo suppliers using configurable aliases, never real vendor names."""
    compact = re.sub(r"[^A-Za-z0-9 ]+", " ", text).lower()
    compact = re.sub(r"\s+", " ", compact)
    for supplier in DEMO_CONFIG["suppliers"]:
        for alias in supplier.get("aliases", []):
            normalized_alias = re.sub(r"[^A-Za-z0-9 ]+", " ", alias).lower().strip()
            if normalized_alias and re.search(r"(?<!\w)" + re.escape(normalized_alias) + r"(?!\w)", compact):
                return supplier["name"]
    return ""


def is_supplier_recognized(supplier_name: str) -> bool:
    return supplier_name in KNOWN_SUPPLIERS


def classify_account(description: str, line_items: str, product_numbers: str) -> dict[str, str]:
    search_text = " ".join([description, line_items, product_numbers]).lower()
    matched_rule = None
    matched_keywords: list[str] = []

    for rule in ACCOUNT_RULES:
        hits = [keyword for keyword in rule["keywords"] if keyword in search_text]
        if hits and len(hits) > len(matched_keywords):
            matched_rule = rule
            matched_keywords = hits

    if matched_rule:
        possible_inventory = possible_inventory_account(search_text, matched_rule["inventory_account"])
        inventory_candidate = "Yes" if possible_inventory else "No"
        notes = "Matched keyword(s): " + ", ".join(matched_keywords[:5]) + "."
        if possible_inventory:
            notes += " Review inventory treatment if purchased for stock rather than a project."
        return {
            "code": matched_rule["code"],
            "name": matched_rule["name"],
            "confidence": "Medium" if possible_inventory else "High",
            "inventory_candidate": inventory_candidate,
            "possible_inventory_account": possible_inventory,
            "notes": notes,
        }

    return {
        "code": DEMO_CODES["other_materials"],
        "name": "Other Demo Materials",
        "confidence": "Low",
        "inventory_candidate": "No",
        "possible_inventory_account": "",
        "notes": "No specific material keyword matched; review account coding.",
    }


def possible_inventory_account(search_text: str, default_inventory_account: str) -> str:
    if not default_inventory_account:
        return ""
    if any(keyword in search_text for keyword in ("hardwood lumber", "hard maple", "lumber")):
        return DEMO_CODES["inventory_lumber"]
    if any(keyword in search_text for keyword in ("engineered wood", "veneer")):
        return DEMO_CODES["inventory_engineered"]
    if any(keyword in search_text for keyword in ("plywood", "mdf", "melamine", "particle board", "panel", "sheet")):
        return DEMO_CODES["inventory_sheet"]
    return ""


def estimate_extraction_confidence(fields: ExtractedFields) -> str:
    if fields.line_item_confidence == "Low":
        return "Low"
    if not is_supplier_recognized(fields.supplier_name):
        return "Medium"
    if fields.supplier_name and fields.invoice_number and fields.total_amount:
        return "High"
    return "Medium"


def extract_document_type(lines: list[str]) -> str:
    joined = " ".join(lines[:25])
    if re.search(r"\bBill\s+of\s+Lading\b", joined, re.I):
        return "Bill of Lading"
    if re.search(r"\bSales\s+Order\b", joined, re.I):
        return "Sales Order"
    if any(re.fullmatch(r"INVOICE", line, re.I) for line in lines[:12]) or re.search(r"\bInvoice#\b", joined, re.I):
        return "Invoice"
    return ""


def normalize_date(value: str) -> str:
    value = value.strip()
    match = re.search(r"\b(\d{4})/(\d{1,2})/(\d{1,2})\b", value)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", value)
    if match:
        year = int(match.group(3))
        if year < 100:
            year += 2000
        return f"{year:04d}-{int(match.group(1)):02d}-{int(match.group(2)):02d}"
    return value


def parse_money(value: str) -> str:
    match = re.search(r"\$?\s*(-?\d[\d,]*\.\d{2})\b", value)
    return match.group(1).replace(",", "") if match else ""


def extract_structured_values(lines: list[str]) -> dict[str, str]:
    values = {
        "document_type": extract_document_type(lines),
        "document_date": "",
        "sales_order_number": "",
        "customer_order_number": "",
        "customer_number": "",
        "bill_of_lading_number": "",
        "ship_date": "",
        "payment_terms": "",
        "invoice_number": "",
        "subtotal_amount": "",
        "sales_tax": "",
        "total_amount": "",
        "balance_due": "",
    }

    for idx, line in enumerate(lines):
        next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
        next_next_line = lines[idx + 2] if idx + 2 < len(lines) else ""

        if re.search(r"\bINVOICE DATE\b.*\bINVOICE NO\.?", line, re.I):
            parts = next_line.split()
            if len(parts) >= 5:
                values["document_date"] = normalize_date(parts[0])
                values["customer_number"] = parts[1]
                values["invoice_number"] = parts[-2]

        if re.search(r"\bCUSTOMER ORDER NO\.?", line, re.I):
            for candidate in (next_line, next_next_line):
                if candidate and not re.fullmatch(r"CONDITIONS", candidate, re.I):
                    parts = candidate.split()
                    if parts:
                        values["customer_order_number"] = parts[0]
                    if len(parts) >= 3:
                        values["payment_terms"] = parts[-1]
                    break

        if re.search(r"\bDate\s+S\.O\.\s+No\.?", line, re.I):
            search_lines = [next_line, next_next_line]
            for candidate in search_lines:
                match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})\s+([A-Z]?\d[\dA-Z\-]{2,24})", candidate)
                if match:
                    values["document_date"] = normalize_date(match.group(1))
                    values["sales_order_number"] = match.group(2)
                    values["invoice_number"] = match.group(2)
                    break

        if re.search(r"\bDate\s+Invoice#\b", line, re.I) or "Invoice#" in line:
            window = " ".join(lines[idx : idx + 4])
            match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4}).*?\b([A-Z]?\d{4,12})\b", window)
            if match:
                values["document_date"] = normalize_date(match.group(1))
                values["invoice_number"] = match.group(2)

        if re.search(r"\bBill\s+of\s+Lading\s*#", line, re.I):
            parts = next_line.split()
            if len(parts) >= 3:
                values["bill_of_lading_number"] = parts[0]
                values["ship_date"] = normalize_date(parts[1])
                values["customer_number"] = parts[2]
                remainder = " ".join(parts[3:])
                if remainder:
                    values["payment_terms"] = clean_field_value(remainder)

        if re.search(r"\bSales\s+Order\s*#", line, re.I):
            parts = next_line.split()
            if len(parts) >= 2:
                values["sales_order_number"] = parts[0]
                values["invoice_number"] = values["invoice_number"] or parts[0]
                if not values["document_date"]:
                    values["document_date"] = normalize_date(parts[1])

        if re.search(r"\bP\.?O\.?\s+No\.?", line, re.I):
            parts = next_line.split()
            if parts:
                first_value = parts[0].strip()
                if (
                    not re.match(r"\d{1,2}/\d{1,2}/\d{2,4}", first_value, re.I)
                    and first_value.upper().rstrip(".") not in {"C.O.D", "COD", "YR"}
                ):
                    values["customer_order_number"] = first_value
                if "C.O.D." in next_line.upper() or "COD" in next_line.upper():
                    values["payment_terms"] = "C.O.D."
                date_matches = re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", next_line)
                if date_matches and not values["ship_date"]:
                    values["ship_date"] = normalize_date(date_matches[-1])

        if re.search(r"\bSUBTOTAL AMOUNT\b|\bSubtotal\b", line, re.I):
            amount = parse_money(line)
            if amount:
                values["subtotal_amount"] = amount

        if re.search(r"\bSALES TAX\b", line, re.I):
            amounts = re.findall(r"\$?\s*(-?\d[\d,]*\.\d{2})\b", line)
            if amounts:
                values["sales_tax"] = amounts[-1].replace(",", "")

        if re.search(r"\bINVOICE TOTAL\b|\bTotal\b", line, re.I) and not re.search(r"\bSubtotal\b", line, re.I):
            amount = parse_money(line)
            if amount:
                values["total_amount"] = amount

        if re.search(r"\bBalance Due\b", line, re.I):
            amount = parse_money(line)
            if amount:
                values["balance_due"] = amount

        if re.search(r"\bAMOUNT BEFORE TAXES\b.*\bTOTAL AMOUNT\b", line, re.I):
            amount_line = next_line
            amounts = re.findall(r"\$?\s*(-?\d[\d,]*\.\d{2})\b", amount_line)
            if amounts:
                values["total_amount"] = amounts[-1].replace(",", "")
                values["subtotal_amount"] = values["subtotal_amount"] or amounts[0].replace(",", "")

    if values["total_amount"] and not values["balance_due"]:
        values["balance_due"] = values["total_amount"]
    return values


def extract_line_items(lines: list[str]) -> str:
    raw_items = collect_line_item_lines(lines)
    cleaned_items = merge_item_lines(raw_items)
    return "; ".join(cleaned_items)[:1000]


def collect_line_item_lines(lines: list[str]) -> list[str]:
    start = None
    for idx, line in enumerate(lines):
        if re.search(r"\b(Product\s+Description|Item\s+Number.*Description|QTY\s+ORD\..*DESCRIPTION|Description\s+Price\s+Amount)\b", line, re.I):
            start = idx + 1
            break
    if start is None:
        return []

    stop_patterns = [
        r"\bSUBTOTAL\b",
        r"\bDocument Totals\b",
        r"\bCustomer Signature\b",
        r"<<TAXABLE AMOUNT",
        r"\bCERTIFIED EPA\b",
        r"\bALL ORDERS SUBJECT\b",
        r"\bTHANK YOU FOR YOUR ORDER\b",
        r"^\*{4,}",
        r"^#{4,}",
    ]
    raw_items = []
    for line in lines[start : start + 25]:
        if any(re.search(pattern, line, re.I) for pattern in stop_patterns):
            break
        if re.search(r"\b(REMIT TO)\b", line, re.I):
            continue
        if re.search(r"\b(Quantity|Quan!ity|Price|Amount|U/M|UNIT PRICE)\b", line, re.I) and not re.search(r"\d", line):
            continue
        if is_noise_line(line):
            continue
        if len(line) <= 2 or re.fullmatch(r"[~\\/_.,;:'`|()\-\s]+", line):
            continue
        raw_items.append(line)
    return raw_items


def extract_product_numbers(lines: list[str]) -> str:
    product_numbers: list[str] = []
    seen: set[str] = set()
    for line in collect_line_item_lines(lines):
        for candidate in product_candidates_from_line(line):
            normalized = candidate.strip(" .,;:")
            if normalized and normalized not in seen:
                seen.add(normalized)
                product_numbers.append(normalized)
    return "; ".join(product_numbers)[:500]


def product_candidates_from_line(line: str) -> list[str]:
    tokens = line.split()
    candidates: list[str] = []

    if len(tokens) >= 2 and re.fullmatch(r"\d+(?:\.\d+)?", tokens[0]):
        second = tokens[1].strip(" ,;:")
        if looks_like_product_number(second, allow_short=True):
            candidates.append(second)

    first = tokens[0].strip(" ,;:") if tokens else ""
    if looks_like_product_number(first, allow_short=False):
        candidates.append(first)

    return candidates


def looks_like_product_number(value: str, allow_short: bool) -> bool:
    value = value.strip()
    if not value:
        return False
    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        return False
    if len(value) < (2 if allow_short else 4) or len(value) > 40:
        return False
    if value.upper() in {"CERTIFIED", "CFR", "PART"}:
        return False
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9./_-]*", value):
        return False
    if allow_short and re.fullmatch(r"[A-Z]{2,}", value):
        return True
    if "-" in value and not re.search(r"\d", value) and len(value) < 8:
        return False
    return bool(re.search(r"\d|-|/", value))


def merge_item_lines(raw_items: list[str]) -> list[str]:
    merged: list[str] = []
    current = ""
    for line in raw_items:
        starts_new = starts_item_line(line)
        if current and starts_new:
            merged.append(clean_item_text(current))
            current = line
        else:
            current = f"{current} {line}".strip()
    if current:
        merged.append(clean_item_text(current))
    return [item for item in merged if item]


def starts_item_line(line: str) -> bool:
    if re.match(r"^\d+/\d", line):
        return True
    if re.match(r"^[A-Z0-9][A-Z0-9\-]{3,}\s+", line):
        return True
    match = re.match(r"^\d+\s+([A-Z0-9][A-Z0-9\-./]*)\s+", line)
    if match and re.search(r"[A-Z]", match.group(1)):
        return True
    return False


def is_noise_line(line: str) -> bool:
    if "�" in line:
        return True
    compact = re.sub(r"\s+", "", line)
    if not compact:
        return True
    alnum = sum(char.isalnum() for char in compact)
    if len(compact) >= 4 and alnum / len(compact) < 0.45:
        return True
    return False


def text_has_noise(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if not compact:
        return False
    replacement_chars = text.count("�")
    unusual = sum(1 for char in compact if ord(char) > 126 and char not in "\u00a0")
    return replacement_chars > 0 or unusual / len(compact) > 0.01


def line_item_confidence(lines: list[str], text: str, source_name: str = "") -> str:
    if source_name.upper().startswith("SCAN_") or text_has_noise(text):
        return "Low"
    if extract_product_numbers(lines):
        return "High"
    if extract_line_items(lines):
        return "Medium"
    return "Low"


def clean_item_text(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    line = re.sub(r"\s+\d+(?:\.\d+)?\s+\d[\d,.]*\s*/\s*(?:SHT|MBF|SF|LF)\s+\d[\d,.]*(?=\s|$)", "", line, flags=re.I)
    line = re.sub(r"\s+\d+\s+(?:EA|SH|RL|PC)\s+\d[\d,.]*\s+\d[\d,.]*(?=\s|$)", "", line, flags=re.I)
    line = re.sub(r"\s+(?:EA|SH|RL|PC)\s+\d[\d,.]*\s+\d[\d,.]*(?=\s|$)", "", line, flags=re.I)
    line = re.sub(r"\s+\d[\d,.]*\s+\d[\d,.]*(?=\s|$)", "", line)
    line = re.sub(r"\s+\(\s*\d[\d,.]*\s*\)\s*(?:SF|LF)\s+\d[\d,.]*$", "", line, flags=re.I)
    line = re.sub(r"\s+\d+(?:\.\d+)?\s*/\s*(?:SHT|MBF|SF|LF)\s+\d[\d,.]*$", "", line, flags=re.I)
    line = re.sub(r"\s+(?:EA|SH|RL|PC)\s+\d[\d,.]*\s+\d[\d,.]*$", "", line, flags=re.I)
    line = re.sub(r"\s+\d+\s+(?:EA|SH|RL|BA|PC)\s+\d[\d,.]*\s+\d[\d,.]*$", "", line, flags=re.I)
    line = re.sub(r"\s+\d[\d,.]*\s+\d[\d,.]*$", "", line)
    return clean_field_value(line)


def is_plausible_supplier(value: str) -> bool:
    value = clean_field_value(value)
    if not (4 <= len(value) <= 120):
        return False
    if not re.search(r"[A-Za-z]", value):
        return False
    reject_patterns = [
        r"\b(invoice|description|qty|quantity|price|amount|total|subtotal|tax|date|page|document|synthetic|demonstration)\b",
        r"\b(bill to|ship to|sold to|customer|account|terms)\b",
        r"^\d+[\d\s\-/.]*$",
        r"^www\.",
        r"@",
    ]
    return not any(re.search(pattern, value, re.I) for pattern in reject_patterns)


def extract_fields(text: str, payload: PdfPayload | None = None, source_name: str = "") -> ExtractedFields:
    lines = useful_lines(text)
    fields = ExtractedFields()
    fields.readable_text_characters = str(len(text))
    if payload is not None:
        fields.wrapped_pdf = "Yes" if payload.is_wrapped else "No"
    if not lines:
        fields.notes.append("No readable text layer found.")
        return fields
    if text_has_noise(text):
        fields.notes.append("Text layer contains noisy/OCR-like artifacts; verify line-item details.")

    structured = extract_structured_values(lines)
    line_items = extract_line_items(lines)
    fields.supplier_name = extract_supplier_name(lines)
    fields.supplier_recognized = "Yes" if is_supplier_recognized(fields.supplier_name) else "No"
    fields.description = extract_description(lines)
    fields.product_numbers = extract_product_numbers(lines)
    fields.line_item_confidence = line_item_confidence(lines, text, source_name)
    fields.invoice_number = extract_invoice_number(lines)
    fields.document_type = structured["document_type"]
    fields.document_date = structured["document_date"]
    fields.sales_order_number = structured["sales_order_number"]
    fields.customer_order_number = structured["customer_order_number"]
    fields.customer_number = structured["customer_number"]
    fields.bill_of_lading_number = structured["bill_of_lading_number"]
    fields.ship_date = structured["ship_date"]
    fields.payment_terms = structured["payment_terms"]
    fields.subtotal_amount = structured["subtotal_amount"]
    fields.sales_tax = structured["sales_tax"]
    fields.total_amount = structured["total_amount"]
    fields.balance_due = structured["balance_due"]
    fields.line_items = line_items or fields.description
    account = classify_account(fields.description, fields.line_items, fields.product_numbers)
    fields.recommended_account_code = account["code"]
    fields.recommended_account_name = account["name"]
    fields.classification_confidence = account["confidence"]
    fields.inventory_candidate = account["inventory_candidate"]
    fields.possible_inventory_account = account["possible_inventory_account"]
    fields.classification_notes = account["notes"]
    fields.extraction_confidence = estimate_extraction_confidence(fields)

    missing = []
    if not fields.supplier_name:
        missing.append("Supplier name")
    if not fields.description:
        missing.append("Description")
    if not fields.invoice_number:
        missing.append("Invoice number")
    if missing:
        fields.notes.append("Missing required field(s): " + ", ".join(missing))
    return fields


def copy_success(source: Path, processed_root: Path, fields: ExtractedFields) -> Path:
    supplier_dir = processed_root / sanitize_filename_part(fields.supplier_name, "unknown_supplier", 80)
    supplier_dir.mkdir(parents=True, exist_ok=True)

    supplier_part = sanitize_filename_part(fields.supplier_name, "unknown_supplier", 80)
    invoice_part = sanitize_filename_part(fields.invoice_number, "unknown_invoice", 50)
    final_name = sanitize_filename_part(f"{supplier_part}_{invoice_part}", "extracted_pdf", 140) + ".pdf"
    destination = unique_path(supplier_dir / final_name)
    shutil.copy2(source, destination)
    return destination


def copy_for_review(source: Path, target_root: Path) -> Path:
    target_root.mkdir(parents=True, exist_ok=True)
    destination = unique_path(target_root / sanitize_filename_part(source.name, "source.pdf", 180))
    if destination.suffix.lower() != ".pdf":
        destination = destination.with_suffix(".pdf")
    shutil.copy2(source, destination)
    return destination


def process_pdf(source: Path, roots: dict[str, Path], scan_policy: str = "warn") -> dict[str, str]:
    row = {column: "" for column in OUTPUT_COLUMNS}
    row["File Name"] = source.name

    try:
        payload = find_pdf_payload(source)
        text, method = extract_text_with_pdfplumber(payload)
        fields = extract_fields(text, payload, source.name)
        notes = list(fields.notes or [])
        notes.insert(0, payload.wrapper_note)
        is_scan_like = source.name.upper().startswith("SCAN_") or fields.line_item_confidence == "Low"
        if is_scan_like:
            notes.append("Scan-like or low-confidence line-item text; verify line-item details before relying on them.")

        row["Supplier name"] = fields.supplier_name
        row["Supplier Recognized"] = fields.supplier_recognized
        row["Extraction Confidence"] = fields.extraction_confidence
        row["Description"] = fields.description
        row["Product Numbers"] = fields.product_numbers
        row["Line Item Confidence"] = fields.line_item_confidence
        row["Invoice number"] = fields.invoice_number
        row["Document Type"] = fields.document_type
        row["Document Date"] = fields.document_date
        row["Sales Order Number"] = fields.sales_order_number
        row["Customer PO / Order Number"] = fields.customer_order_number
        row["Customer Number"] = fields.customer_number
        row["Bill of Lading Number"] = fields.bill_of_lading_number
        row["Ship Date"] = fields.ship_date
        row["Payment Terms"] = fields.payment_terms
        row["Subtotal Amount"] = fields.subtotal_amount
        row["Sales Tax"] = fields.sales_tax
        row["Total Amount"] = fields.total_amount
        row["Balance Due"] = fields.balance_due
        row["Line Items"] = fields.line_items
        row["Recommended Account Code"] = fields.recommended_account_code
        row["Recommended Account Name"] = fields.recommended_account_name
        row["Classification Confidence"] = fields.classification_confidence
        row["Inventory Candidate"] = fields.inventory_candidate
        row["Possible Inventory Account"] = fields.possible_inventory_account
        row["Classification Notes"] = fields.classification_notes
        row["Readable Text Characters"] = fields.readable_text_characters
        row["Wrapped PDF"] = fields.wrapped_pdf
        row["Extraction Method"] = method
        row["Notes / Errors"] = "; ".join(note for note in notes if note)

        if fields.supplier_name and fields.description and fields.invoice_number and not (
            scan_policy == "manual_review" and is_scan_like
        ):
            destination = copy_success(source, roots["processed"], fields)
            row["Processing Status"] = "processed"
        else:
            destination = copy_for_review(source, roots["manual_review"])
            row["Processing Status"] = "manual_review"
            if scan_policy == "manual_review" and is_scan_like:
                notes.append("Scan policy sent this file to manual_review.")
                row["Notes / Errors"] = "; ".join(note for note in notes if note)

        row["Final File Name"] = destination.name
        row["Output Folder"] = str(destination.parent.relative_to(roots["processed"].parent))
        return row
    except Exception as exc:  # Keep batch processing alive and record the failing file.
        destination = copy_for_review(source, roots["failed"])
        row["Extraction Method"] = "failed before text extraction"
        row["Notes / Errors"] = str(exc)
        row["Final File Name"] = destination.name
        row["Output Folder"] = str(destination.parent.relative_to(roots["processed"].parent))
        row["Processing Status"] = "failed"
        return row


def excel_column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def write_xlsx_fallback(rows: list[dict[str, str]], output_path: Path) -> None:
    """Write a minimal valid .xlsx using only the standard library."""
    table = [OUTPUT_COLUMNS] + [[safe_excel_text(row.get(column, "")) for column in OUTPUT_COLUMNS] for row in rows]

    sheet_rows = []
    for row_index, values in enumerate(table, start=1):
        cells = []
        for col_index, value in enumerate(values, start=1):
            cell_ref = f"{excel_column_name(col_index)}{row_index}"
            escaped = html.escape(str(value), quote=False)
            cells.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{escaped}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    widths = "".join(
        f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"/>'
        for idx, width in enumerate(OUTPUT_COLUMN_WIDTHS, start=1)
    )
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<cols>{widths}</cols><sheetData>{''.join(sheet_rows)}</sheetData></worksheet>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="PDF Extraction" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/></Relationships>'
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", content_types_xml)
        xlsx.writestr("_rels/.rels", rels_xml)
        xlsx.writestr("xl/workbook.xml", workbook_xml)
        xlsx.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        xlsx.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def money_value(value: str) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except ValueError:
        return None


def safe_excel_text(value: str) -> str:
    """Ensure external document content is written as text, not an Excel formula."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def detail_cell_value(column: str, value: str) -> str | float:
    if column in {"Subtotal Amount", "Sales Tax", "Total Amount", "Balance Due"}:
        number = money_value(value)
        return number if number is not None else ""
    return safe_excel_text(value)


def safe_sheet_name(value: str, used_names: set[str]) -> str:
    cleaned = re.sub(r"[\[\]:*?/\\]", " ", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned) or "UNKNOWN"
    cleaned = cleaned[:31].strip()
    base = cleaned
    counter = 2
    while cleaned in used_names:
        suffix = f" {counter}"
        cleaned = (base[: 31 - len(suffix)] + suffix).strip()
        counter += 1
    used_names.add(cleaned)
    return cleaned


def supplier_sheet_name(supplier: str, used_names: set[str]) -> str:
    name = supplier.upper()
    name = name.replace(" CO.", "").replace(", INC.", "").replace(" LTD.", "")
    name = name.replace(" AMERICA", "")
    return safe_sheet_name(name, used_names)


def supplier_summary_description(row: dict[str, str]) -> str:
    text = " ".join(
        [
            row.get("Description", ""),
            row.get("Line Items", ""),
            row.get("Product Numbers", ""),
            row.get("Recommended Account Name", ""),
        ]
    ).lower()
    code = row.get("Recommended Account Code", "")
    if code == DEMO_CODES["sheet_materials"]:
        if "pvc" in text or "edge" in text or "edg" in text:
            return "PVC EDGE / SHEET GOODS"
        if "melamine" in text:
            return "MELAMINE / SHEET GOODS"
        if "mdf" in text:
            return "MDF / SHEET GOODS"
        if "maple" in text or "hardwood" in text or "lumber" in text:
            return "LUMBER / SHEET GOODS"
        return "PLYWOOD / SHEET GOODS"
    if code == DEMO_CODES["hardware"]:
        if "pull" in text or "handle" in text:
            return "HANDLES / HARDWARE"
        return "HARDWARE"
    if code == DEMO_CODES["finishing"]:
        return "FINISHING MATERIALS"
    if code == DEMO_CODES["other_materials"]:
        return "OTHER MATERIALS"
    return (row.get("Description") or "").upper()


def style_sheet(sheet, widths: list[int] | None = None, add_filter: bool = True) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill

    header_fill = PatternFill("solid", fgColor="D9EAD3")
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    sheet.freeze_panes = "A2"
    if add_filter and sheet.max_row > 1 and sheet.max_column > 1:
        sheet.auto_filter.ref = sheet.dimensions
    if widths:
        for idx, width in enumerate(widths, start=1):
            sheet.column_dimensions[excel_column_name(idx)].width = width
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def add_detailed_sheet(workbook, rows: list[dict[str, str]]) -> None:
    sheet = workbook.active
    sheet.title = "Detailed Extraction"
    sheet.append(OUTPUT_COLUMNS)
    for row in rows:
        sheet.append([detail_cell_value(column, row.get(column, "")) for column in OUTPUT_COLUMNS])
    style_sheet(sheet, OUTPUT_COLUMN_WIDTHS)
    for column in ("Subtotal Amount", "Sales Tax", "Total Amount", "Balance Due"):
        col_index = OUTPUT_COLUMNS.index(column) + 1
        for cell in sheet.iter_cols(min_col=col_index, max_col=col_index, min_row=2):
            for item in cell:
                item.number_format = "$#,##0.00"


def add_summary_sheet(workbook, rows: list[dict[str, str]]) -> None:
    from openpyxl.styles import Font, PatternFill

    sheet = workbook.create_sheet("Summary")
    sheet.append(["PDF Extraction Summary"])
    sheet.append([])
    sheet.append(["Metric", "Value"])
    sheet.append(["Total PDFs", len(rows)])
    sheet.append(["Processed", sum(1 for row in rows if row.get("Processing Status") == "processed")])
    sheet.append(["Manual Review", sum(1 for row in rows if row.get("Processing Status") == "manual_review")])
    sheet.append(["Failed", sum(1 for row in rows if row.get("Processing Status") == "failed")])
    sheet.append([])

    sheet.append(["Totals by Supplier", "Count", "Total Amount", "Manual Review Count"])
    for supplier in sorted({row.get("Supplier name", "") or "Unknown" for row in rows}):
        supplier_rows = [row for row in rows if (row.get("Supplier name", "") or "Unknown") == supplier]
        total = sum(money_value(row.get("Total Amount", "")) or 0 for row in supplier_rows)
        manual = sum(1 for row in supplier_rows if row.get("Processing Status") == "manual_review")
        sheet.append([supplier, len(supplier_rows), total, manual])

    sheet.append([])
    sheet.append(["Totals by Account", "Account Name", "Count", "Total Amount", "Inventory Candidates"])
    accounts = sorted({row.get("Recommended Account Code", "") or "Uncoded" for row in rows})
    for code in accounts:
        account_rows = [row for row in rows if (row.get("Recommended Account Code", "") or "Uncoded") == code]
        name = account_rows[0].get("Recommended Account Name", "") if account_rows else ""
        total = sum(money_value(row.get("Total Amount", "")) or 0 for row in account_rows)
        inventory = sum(1 for row in account_rows if row.get("Inventory Candidate") == "Yes")
        sheet.append([code, name, len(account_rows), total, inventory])

    sheet.append([])
    sheet.append(["Totals by Status", "Count", "Total Amount"])
    for status in sorted({row.get("Processing Status", "") or "Unknown" for row in rows}):
        status_rows = [row for row in rows if (row.get("Processing Status", "") or "Unknown") == status]
        total = sum(money_value(row.get("Total Amount", "")) or 0 for row in status_rows)
        sheet.append([status, len(status_rows), total])

    style_sheet(sheet, [28, 18, 18, 22, 22], add_filter=False)
    section_fill = PatternFill("solid", fgColor="D9EAD3")
    for row_idx in (1, 3, 9, 14, 18):
        for cell in sheet[row_idx]:
            cell.font = Font(bold=True)
            cell.fill = section_fill
    for row in sheet.iter_rows():
        for cell in row:
            if isinstance(cell.value, float):
                cell.number_format = "$#,##0.00"


def add_supplier_sheets(workbook, rows: list[dict[str, str]]) -> None:
    used_names = {sheet.title for sheet in workbook.worksheets}
    suppliers = sorted({row.get("Supplier name", "") or "Unknown Supplier" for row in rows})
    for supplier in suppliers:
        sheet = workbook.create_sheet(supplier_sheet_name(supplier, used_names))
        headers = [
            "DATE",
            "INVOICE #",
            "AMT",
            "DESCRIPTION",
            "ACCOUNT CODE",
            "ACCOUNT NAME",
            "STATUS",
            "NOTES",
        ]
        sheet.append(headers)
        supplier_rows = [row for row in rows if (row.get("Supplier name", "") or "Unknown Supplier") == supplier]
        supplier_rows.sort(key=lambda row: (row.get("Document Date", ""), row.get("Invoice number", "")))
        for row in supplier_rows:
            sheet.append(
                [
                    safe_excel_text(row.get("Document Date", "")),
                    safe_excel_text(row.get("Invoice number", "")),
                    money_value(row.get("Total Amount", "")) or "",
                    safe_excel_text(supplier_summary_description(row)),
                    row.get("Recommended Account Code", ""),
                    row.get("Recommended Account Name", ""),
                    row.get("Processing Status", ""),
                    safe_excel_text(row.get("Notes / Errors", "")),
                ]
            )
        style_sheet(sheet, [14, 18, 14, 32, 16, 28, 18, 54])
        for cell in sheet.iter_cols(min_col=3, max_col=3, min_row=2):
            for item in cell:
                item.number_format = "$#,##0.00"


def add_account_rules_sheet(workbook) -> None:
    sheet = workbook.create_sheet("Account Rules")
    sheet.append(["Account Code", "Account Name", "Use When", "Tool Treatment"])
    for code, name, use_when in ACCOUNT_REFERENCE_ROWS:
        if code in {DEMO_CODES["inventory_sheet"], DEMO_CODES["inventory_lumber"], DEMO_CODES["inventory_engineered"]}:
            treatment = "Reference only. Used as possible inventory account when purchase may be for stock."
        elif code in {DEMO_CODES["sheet_materials"], DEMO_CODES["hardware"], DEMO_CODES["finishing"], DEMO_CODES["other_materials"]}:
            treatment = "Used for recommended direct material account classification."
        else:
            treatment = "Fallback/general account reference."
        sheet.append([code, name, use_when, treatment])
    style_sheet(sheet, [16, 34, 70, 70])


def add_readme_sheet(workbook) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill

    sheet = workbook.create_sheet("README")
    rows = [
        ["PDF Extraction Tool - Quick Guide"],
        [""],
        ["What this workbook is"],
        ["This workbook summarizes PDF invoices/orders processed locally by the extraction script."],
        [""],
        ["How to use it"],
        ["1. Start with the Summary sheet for totals by supplier, account, and status."],
        ["2. Use each supplier tab for the simple DATE / INVOICE # / AMT / DESCRIPTION view."],
        ["3. Use Detailed Extraction only when you need audit details, notes, or troubleshooting."],
        ["4. Review every file listed as manual_review before using its line-item details."],
        [""],
        ["Folder meanings"],
        ["processed: copied PDFs where required fields were found and confidence rules passed."],
        ["manual_review: copied PDFs that need human review, usually scanned or lower-confidence files."],
        ["failed: copied PDFs that could not be parsed."],
        [""],
        ["Important notes"],
        ["Source PDFs are never moved, deleted, or modified."],
        ["Account codes are recommendations. Final accounting treatment still depends on business context."],
        ["Inventory account fields are only flags for review when purchases may be for stock."],
        ["Line-item details from scanned files should be checked manually."],
        [""],
        ["Main sheets"],
        ["Summary: quick totals, similar to a pivot-style overview."],
        ["Supplier tabs: simplified views for day-to-day use."],
        ["Detailed Extraction: full extracted data and notes."],
        ["Account Rules: reference for the account-code logic used by the tool."],
    ]
    for row in rows:
        sheet.append(row)

    title_fill = PatternFill("solid", fgColor="D9EAD3")
    section_fill = PatternFill("solid", fgColor="EAF4E6")
    sheet["A1"].font = Font(bold=True, size=14)
    sheet["A1"].fill = title_fill
    section_titles = {
        "What this workbook is",
        "How to use it",
        "Folder meanings",
        "Important notes",
        "Main sheets",
    }
    for row in sheet.iter_rows():
        cell = row[0]
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        if cell.value in section_titles:
            cell.font = Font(bold=True)
            cell.fill = section_fill
    sheet.column_dimensions["A"].width = 110
    sheet.freeze_panes = "A2"
    workbook.move_sheet(sheet, offset=-(len(workbook.worksheets) - 1))


def write_excel(rows: list[dict[str, str]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path = unique_path(output_path)
    try:
        from openpyxl import Workbook  # type: ignore

        workbook = Workbook()
        add_detailed_sheet(workbook, rows)
        add_summary_sheet(workbook, rows)
        add_supplier_sheets(workbook, rows)
        add_account_rules_sheet(workbook)
        add_readme_sheet(workbook)
        workbook.save(output_path)
        return output_path
    except Exception:
        pass

    try:
        from openpyxl import Workbook  # type: ignore

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "PDF Extraction"
        sheet.append(OUTPUT_COLUMNS)
        for row in rows:
            sheet.append([safe_excel_text(row.get(column, "")) for column in OUTPUT_COLUMNS])
        for idx, width in enumerate(OUTPUT_COLUMN_WIDTHS, start=1):
            sheet.column_dimensions[excel_column_name(idx)].width = width
        workbook.save(output_path)
        return output_path
    except Exception:
        pass

    write_xlsx_fallback(rows, output_path)
    return output_path


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    input_dir = Path(args.input).expanduser().resolve()
    if args.output_root:
        output_root = Path(args.output_root).expanduser().resolve()
    else:
        output_root = input_dir / "pdf_extraction_output"

    output_arg = Path(args.output).expanduser()
    if output_arg.is_absolute():
        output_path = output_arg.resolve()
    else:
        output_path = (output_root / output_arg).resolve()
    if output_path.suffix.lower() != ".xlsx":
        output_path = output_path.with_suffix(".xlsx")

    return input_dir, output_root, output_path


def main() -> int:
    args = parse_args()
    input_dir, output_root, output_path = resolve_paths(args)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input folder does not exist or is not a directory: {input_dir}", file=sys.stderr)
        return 2

    roots = {
        "processed": output_root / "processed",
        "manual_review": output_root / "manual_review",
        "failed": output_root / "failed",
    }
    for folder in roots.values():
        folder.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf")
    rows = [process_pdf(path, roots, args.scan_policy) for path in pdf_files]
    final_output_path = write_excel(rows, output_path)

    processed = sum(1 for row in rows if row["Processing Status"] == "processed")
    manual_review = sum(1 for row in rows if row["Processing Status"] == "manual_review")
    failed = sum(1 for row in rows if row["Processing Status"] == "failed")

    print(f"Processed PDFs: {len(rows)}")
    print(f"Successful: {processed}")
    print(f"Manual review: {manual_review}")
    print(f"Failed: {failed}")
    print(f"Excel output: {final_output_path}")
    print(f"Output root: {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
