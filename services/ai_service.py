import json
import re
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert email analyst. Return ONLY valid JSON, no markdown, no explanation."""

ANALYSIS_PROMPT = """Analyze this email thoroughly and return a JSON object with exactly these fields:

{{
  "summary": "2-3 sentence summary",
  "important_points": ["detailed point 1", "detailed point 2", "detailed point 3"],
  "priority": "High | Medium | Low",
  "deadline": "extracted deadline or empty string",
  "category": "Job | Internship | Funding | AI | Startup | Security | Event | Personal | Promotion | Other",
  "links": ["url1", "url2"],
  "sentiment": "Positive | Neutral | Negative",
  "action_required": true,
  "action_items": ["action 1", "action 2"],
  "suggested_reply": "A professional reply to this email in 3-4 sentences",
  "reply_subject": "Re: original subject"
}}

Rules:
- important_points: maximum 5 detailed bullet points
- action_items: specific things the recipient should do
- suggested_reply: professional, concise, ready to send
- priority: High if urgent/deadline/interview, Medium if informational, Low if promotional

Subject: {subject}
From: {sender}
Body:
{body}"""

SENDER_VERIFY_PROMPT = """You are a cybersecurity and email authenticity expert.
Analyze this sender email address for legitimacy based on domain, patterns, and context.
Return ONLY valid JSON:

{{
  "is_legitimate": true,
  "confidence": "High | Medium | Low",
  "domain_type": "Corporate | Personal | Suspicious | Unknown",
  "red_flags": ["flag 1"],
  "explanation": "Brief explanation",
  "recommendation": "Safe to engage | Proceed with caution | Likely spam/phishing"
}}

Sender: {sender}
Subject: {subject}"""


def analyze_email(subject, sender, body):
    default = {
        "summary": "Unable to analyze email.",
        "important_points": [],
        "priority": "Low",
        "deadline": "",
        "category": "Other",
        "links": [],
        "sentiment": "Neutral",
        "action_required": False,
        "action_items": [],
        "suggested_reply": "",
        "reply_subject": f"Re: {subject}",
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
                {"role": "user", "content": ANALYSIS_PROMPT.format(
                    subject=subject,
                    sender=sender,
                    body=body[:3000]
                )},
            ],
            max_tokens=1200,
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
            "sentiment": result.get("sentiment", "Neutral"),
            "action_required": bool(result.get("action_required", False)),
            "action_items": list(result.get("action_items", []))[:5],
            "suggested_reply": str(result.get("suggested_reply", "")),
            "reply_subject": str(result.get("reply_subject", f"Re: {subject}")),
        }

    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return default


def verify_sender(sender_email, subject):
    default = {
        "is_legitimate": True,
        "confidence": "Low",
        "domain_type": "Unknown",
        "red_flags": [],
        "explanation": "Unable to verify sender.",
        "recommendation": "Proceed with caution"
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
                {"role": "user", "content": SENDER_VERIFY_PROMPT.format(
                    sender=sender_email,
                    subject=subject,
                )},
            ],
            max_tokens=400,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        return json.loads(raw)

    except Exception as e:
        logger.error(f"Sender verification error: {e}")
        return default