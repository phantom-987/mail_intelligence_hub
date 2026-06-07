import json
import re
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert email analyst. Analyze the provided email and return ONLY valid JSON. No markdown, no explanation, no code blocks."""

USER_PROMPT = """Analyze this email and return a JSON object with exactly these fields:
{{
  "summary": "2-3 sentence summary",
  "important_points": ["point 1", "point 2"],
  "priority": "High | Medium | Low",
  "deadline": "extracted deadline or empty string",
  "category": "Job | Internship | Funding | AI | Startup | Security | Event | Personal | Promotion | Other",
  "links": ["url1", "url2"]
}}

Subject: {subject}
From: {sender}
Body:
{body}"""


def analyze_email(subject, sender, body):
    default = {
        "summary": "Unable to analyze email.",
        "important_points": [],
        "priority": "Low",
        "deadline": "",
        "category": "Other",
        "links": [],
    }

    if not settings.OPENAI_API_KEY:
        return default

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT.format(
                    subject=subject,
                    sender=sender,
                    body=body[:3000]
                )},
            ],
            max_tokens=800,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        result = json.loads(raw)

        return {
            "summary": str(result.get("summary", "")),
            "important_points": list(result.get("important_points", []))[:5],
            "priority": result.get("priority", "Low") if result.get("priority") in ("High", "Medium", "Low") else "Low",
            "deadline": str(result.get("deadline", "")),
            "category": result.get("category", "Other") if result.get("category") in (
                "Job", "Internship", "Funding", "AI", "Startup",
                "Security", "Event", "Personal", "Promotion", "Other"
            ) else "Other",
            "links": [str(l) for l in result.get("links", [])],
        }
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return default