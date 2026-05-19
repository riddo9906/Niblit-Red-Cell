from typing import Any

from app.core.template_library import get_schema, is_list_field


def enforce_schema(task: str, raw_output: dict[str, Any]) -> dict[str, Any]:
    schema = get_schema(task)
    formatted: dict[str, Any] = {}
    for field in schema:
        value = raw_output.get(field)
        if value is None:
            value = [] if is_list_field(task, field) else ""
        formatted[field] = value
    return formatted


def to_markdown(task: str, structured_output: dict[str, Any]) -> str:
    lines = [f"# {task.replace('_', ' ').title()} Output", ""]
    for key, value in structured_output.items():
        lines.append(f"## {key.replace('_', ' ').title()}")
        if isinstance(value, list):
            lines.extend([f"- {item}" for item in value] or ["- N/A"])
        else:
            lines.append(str(value) if value else "N/A")
        lines.append("")
    return "\n".join(lines).strip() + "\n"
