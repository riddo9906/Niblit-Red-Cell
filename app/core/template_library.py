TASK_SCHEMAS: dict[str, list[str]] = {
    "resume": ["candidate_summary", "optimized_bullet_points", "skills"],
    "cover_letter": ["opening", "fit_summary", "body", "closing"],
    "meeting_summary": ["summary", "key_points", "action_items", "risks"],
    "business_idea": [
        "business_model",
        "target_audience",
        "monetization_strategy",
        "landing_page_copy",
    ],
    "ad_copy": ["facebook", "google", "tiktok"],
}

LIST_FIELDS_BY_TASK: dict[str, set[str]] = {
    "resume": {"optimized_bullet_points", "skills"},
    "cover_letter": set(),
    "meeting_summary": {"key_points", "action_items", "risks"},
    "business_idea": set(),
    "ad_copy": set(),
}

TASK_PROMPTS: dict[str, str] = {
    "resume": "Transform raw experience text into structured resume output.",
    "cover_letter": "Create a tailored cover letter using profile and job description.",
    "meeting_summary": "Convert messy notes into a concise meeting summary with actions.",
    "business_idea": "Transform idea dump into business strategy output.",
    "ad_copy": "Generate concise ad variants for Facebook, Google, and TikTok.",
}


def get_schema(task: str) -> list[str]:
    return TASK_SCHEMAS[task]


def get_prompt(task: str) -> str:
    return TASK_PROMPTS[task]


def is_list_field(task: str, field: str) -> bool:
    return field in LIST_FIELDS_BY_TASK[task]
