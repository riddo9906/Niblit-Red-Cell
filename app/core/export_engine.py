import json
from dataclasses import dataclass


@dataclass
class ExportBundle:
    json_data: str
    markdown_data: str
    pdf_bytes: bytes | None


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _create_simple_pdf(markdown_text: str) -> bytes:
    lines = markdown_text.splitlines()[:42]
    content_lines = ["BT", "/F1 11 Tf", "50 780 Td", "14 TL"]
    for idx, line in enumerate(lines):
        escaped = _escape_pdf_text(line[:100])
        if idx > 0:
            content_lines.append("T*")
        content_lines.append(f"({escaped}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", "ignore")

    objects = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>endobj\n"
    )
    objects.append(b"4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")
    objects.append(
        f"5 0 obj<< /Length {len(stream)} >>stream\n".encode("latin-1")
        + stream
        + b"\nendstream endobj\n"
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_start = len(pdf)
    count = len(objects) + 1
    pdf.extend(f"xref\n0 {count}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        f"trailer<< /Size {count} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode(
            "latin-1"
        )
    )
    return bytes(pdf)


def build_export_bundle(structured_output: dict, markdown: str, include_pdf: bool) -> ExportBundle:
    json_data = json.dumps(structured_output, indent=2)
    pdf_bytes = _create_simple_pdf(markdown) if include_pdf else None
    return ExportBundle(json_data=json_data, markdown_data=markdown, pdf_bytes=pdf_bytes)
