"""
CSV and PDF report generation for StockPilot AI.

CSV: Standard library csv module with proper escaping and headers.
PDF: reportlab for reliable server-side generation (no browser dependency).
"""

import csv
import io
from datetime import datetime
from decimal import Decimal

from django.utils import timezone


def generate_csv(*, title, headers, rows):
    """
    Generate a CSV file from headers and rows.
    Returns bytes ready for HTTP response or storage.

    Handles:
    - Proper escaping via csv.writer
    - Empty result sets (headers only)
    - Decimal serialization
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([
            str(v) if isinstance(v, Decimal) else (v if v is not None else "")
            for v in row
        ])
    return output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility


def generate_pdf(*, title, organization_name, report_type, period, filters_text, summary, headers, rows):
    """
    Generate a professional PDF report.
    Returns bytes ready for HTTP response or storage.

    Uses reportlab which is a pure-Python PDF library compatible with
    any deployment platform (Render, Heroku, etc.) — no system dependencies.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        raise RuntimeError(
            "reportlab is required for PDF generation. "
            "Install it with: pip install reportlab"
        )

    buffer = io.BytesIO()
    page_size = landscape(A4) if len(headers) > 6 else A4
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=4 * mm,
        textColor=colors.HexColor("#1e293b"),
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=2 * mm,
    )
    summary_style = ParagraphStyle(
        "SummaryText",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        spaceAfter=1 * mm,
    )

    elements = []

    # Header
    elements.append(Paragraph("StockPilot AI", subtitle_style))
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(f"Organization: {organization_name}", subtitle_style))
    elements.append(Paragraph(f"Report: {report_type}", subtitle_style))
    if period:
        elements.append(Paragraph(f"Period: {period}", subtitle_style))
    if filters_text:
        elements.append(Paragraph(f"Filters: {filters_text}", subtitle_style))
    generated_at = timezone.now().strftime("%Y-%m-%d %H:%M UTC")
    elements.append(Paragraph(f"Generated: {generated_at}", subtitle_style))
    elements.append(Spacer(1, 6 * mm))

    # Summary section
    if summary:
        elements.append(Paragraph("Summary", styles["Heading2"]))
        for key, value in summary.items():
            label = key.replace("_", " ").title()
            elements.append(Paragraph(f"{label}: {value}", summary_style))
        elements.append(Spacer(1, 4 * mm))

    # Data table
    if rows:
        table_data = [headers] + [
            [str(v) if v is not None else "" for v in row]
            for row in rows
        ]

        # Calculate column widths based on available width
        available_width = page_size[0] - 30 * mm
        col_width = available_width / len(headers)

        table = Table(table_data, repeatRows=1, colWidths=[col_width] * len(headers))
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No data matches the selected filters.", summary_style))

    doc.build(elements)
    return buffer.getvalue()


def report_data_to_table(report_type, data):
    """
    Convert analytics service output to (headers, rows) for CSV/PDF export.
    Returns (headers: list[str], rows: list[list]).
    """
    if report_type == "inventory_health":
        items = data.get("items", [])
        headers = ["Product", "SKU", "On Hand", "Reorder Threshold", "Target Level", "Status", "Recent Movement"]
        rows = [
            [i["product_name"], i["sku"], i["on_hand"], i["reorder_threshold"],
             i["target_stock_level"], i["status"], "Yes" if i["has_recent_movement"] else "No"]
            for i in items
        ]
        return headers, rows

    if report_type == "low_stock":
        headers = ["Product", "SKU", "On Hand", "Reorder Threshold", "Target Level", "Deficit", "Category"]
        rows = [
            [i["product_name"], i["sku"], i["on_hand"], i["reorder_threshold"],
             i["target_stock_level"], i["deficit"], i.get("category", "")]
            for i in data
        ]
        return headers, rows

    if report_type == "stockout":
        # Reuse stock health data filtered to out_of_stock
        items = [i for i in data.get("items", []) if i["status"] == "out_of_stock"]
        headers = ["Product", "SKU", "Reorder Threshold", "Target Level"]
        rows = [
            [i["product_name"], i["sku"], i["reorder_threshold"], i["target_stock_level"]]
            for i in items
        ]
        return headers, rows

    if report_type == "inventory_valuation":
        items = data.get("items", [])
        headers = ["Product", "SKU", "Hub", "On Hand", "Cost Price", "Line Value", "Category"]
        rows = [
            [i["product_name"], i["sku"], i["hub_name"], i["on_hand"],
             i["cost_price"], i["line_value"], i.get("category", "")]
            for i in items
        ]
        return headers, rows

    if report_type == "slow_moving":
        items = [i for i in data.get("items", []) if not i["has_recent_movement"] and i["on_hand"] != "0" and i["on_hand"] != "0.00"]
        headers = ["Product", "SKU", "On Hand", "Status"]
        rows = [
            [i["product_name"], i["sku"], i["on_hand"], i["status"]]
            for i in items
        ]
        return headers, rows

    if report_type == "hub_performance":
        headers = ["Hub", "Code", "Products", "Total Units", "Total Value", "Low Stock", "Out of Stock"]
        rows = [
            [i["hub_name"], i["hub_code"], i["product_count"], i["total_units"],
             i["total_value"], i["low_stock_count"], i["out_of_stock_count"]]
            for i in data
        ]
        return headers, rows

    if report_type == "stock_movements":
        headers = ["Date", "Product", "SKU", "Hub", "Type", "Delta", "Before", "After", "Reason", "Actor"]
        rows = [
            [i["created_at"][:19], i["product_name"], i["product_sku"], i["hub_name"],
             i["movement_type"], i["quantity_delta"], i["quantity_before"],
             i["quantity_after"], i["reason"], i.get("actor", "")]
            for i in data
        ]
        return headers, rows

    if report_type == "transfers":
        headers = ["Date", "Product", "From Hub", "To Hub", "Qty", "Status", "Requested By", "Dispatched", "Received"]
        rows = [
            [i["created_at"][:19], i["product_name"], i["source_hub"], i["destination_hub"],
             i["quantity"], i["status"], i.get("requested_by", ""),
             i.get("dispatched_at", ""), i.get("received_at", "")]
            for i in data
        ]
        return headers, rows

    if report_type == "restocking":
        headers = ["Date", "Product", "Hub", "Supplier", "Qty", "Status", "Requested By", "Received"]
        rows = [
            [i["created_at"][:19], i["product_name"], i["hub_name"], i.get("supplier_name", ""),
             i["quantity"], i["status"], i.get("requested_by", ""),
             i.get("received_at", "")]
            for i in data
        ]
        return headers, rows

    return [], []
