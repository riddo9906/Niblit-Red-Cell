from app.core.template_library import get_prompt, get_schema


def build_prompt(task: str, normalized_payload: dict) -> dict:
    return {
        "task": task,
        "instruction": get_prompt(task),
        "required_fields": get_schema(task),
        "input": normalized_payload,
        "rules": [
            "Return only JSON object",
            "Include all required fields",
            "Keep concise and professional",
            "No unstructured prose outside schema",
        ],
    }
