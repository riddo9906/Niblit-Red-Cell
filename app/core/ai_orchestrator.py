import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AIAdapter:
    def generate(self, prompt_payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class OpenAIAdapter(AIAdapter):
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        try:
            from openai import OpenAI

            self.client = OpenAI()
        except Exception as exc:
            raise RuntimeError("OpenAI SDK unavailable") from exc

    def generate(self, prompt_payload: dict[str, Any]) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict JSON transformer. Output valid JSON only.",
                },
                {"role": "user", "content": json.dumps(prompt_payload)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)


class LocalDeterministicAdapter(AIAdapter):
    def _sentences(self, text: str) -> list[str]:
        return [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]

    def generate(self, prompt_payload: dict[str, Any]) -> dict[str, Any]:
        task = prompt_payload["task"]
        data = prompt_payload["input"]

        if task == "resume":
            text = data["raw_experience_text"]
            snippets = self._sentences(text)
            return {
                "candidate_summary": snippets[0] if snippets else text[:180],
                "optimized_bullet_points": [
                    f"Delivered impact: {s}" for s in snippets[:5]
                ]
                or ["Delivered measurable project outcomes"],
                "skills": sorted(
                    {
                        word.strip(",.:;!?()[]{}")
                        for word in text.split()
                        if len(word) > 5
                    }
                )[:8],
            }

        if task == "cover_letter":
            profile = data["user_profile"]
            jd = data["job_description"]
            return {
                "opening": "Dear Hiring Manager,",
                "fit_summary": f"My background aligns with your needs: {profile[:240]}",
                "body": f"I can contribute to priorities described in the role: {jd[:320]}",
                "closing": "Thank you for your consideration. I look forward to discussing the role.",
            }

        if task == "meeting_summary":
            notes = data["notes"]
            snippets = self._sentences(notes)
            return {
                "summary": snippets[0] if snippets else notes[:240],
                "key_points": snippets[:5] or ["No key points detected"],
                "action_items": [
                    f"Action: {s}" for s in snippets[1:4]
                ]
                or ["Action: Follow up on meeting decisions"],
                "risks": snippets[4:6] or ["No explicit risks captured"],
            }

        if task == "business_idea":
            idea = data["idea_dump"]
            return {
                "business_model": f"Subscription + service upsell around: {idea[:180]}",
                "target_audience": "Early adopters, SMB teams, and digital-first professionals",
                "monetization_strategy": "Free tier for trial, Pro monthly subscription, Enterprise custom contracts",
                "landing_page_copy": f"Turn your idea into outcomes: {idea[:220]}",
            }

        if task == "ad_copy":
            product = data["product_description"]
            base = product[:180]
            return {
                "facebook": f"Stop scrolling—{base}. Try it today.",
                "google": f"{base} | Fast setup | Start now",
                "tiktok": f"POV: You found {base}. Tap to see why everyone is switching.",
            }

        return {}


class AIOrchestrator:
    def __init__(self, adapters: list[AIAdapter]) -> None:
        self.adapters = adapters

    def generate(self, prompt_payload: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        for adapter in self.adapters:
            try:
                return adapter.generate(prompt_payload)
            except Exception as exc:
                errors.append(str(exc))
                logger.warning("Adapter failed: %s", exc)
        raise RuntimeError(f"All AI adapters failed: {errors}")
