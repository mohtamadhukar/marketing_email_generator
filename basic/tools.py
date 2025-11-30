# Standard library imports
import json
import re
import uuid

# Third-party imports
from google.adk.tools.function_tool import FunctionTool


def brand_check(draft_email: dict, creative_guidelines: dict) -> dict:
    """
    Input: 
      draft_email = {"subject_lines":[...], "body_variants":[...]}
      creative_guidelines = {"banned_phrases":[...], "subject_length_limit": int, "disclaimer": "..."}
    Output: same structure, filtered & adjusted
    """
    banned = {b.lower() for b in (creative_guidelines.get("banned_phrases") or [])}
    limit = int(creative_guidelines.get("subject_length_limit", 60))
    # Filter & trim subjects
    filtered_subjects = []
    for s in draft_email.get("subject_lines", []):
        if any(b in s.lower() for b in banned): 
            continue
        s = s[:limit].rstrip()
        filtered_subjects.append(s)
    # Append disclaimer to bodies
    bodies = draft_email.get("body_variants", [])[:]
    disclaimer = creative_guidelines.get("disclaimer")
    if disclaimer:
        bodies = [b + f"\n\n*{disclaimer}*" for b in bodies]
    return {"subject_lines": filtered_subjects, "body_variants": bodies}

def safety_check(governed_email: dict) -> dict:
    """
    Naive spam/PII heuristics for demo.
    """
    text = json.dumps(governed_email).lower()
    spam_triggers = {"free","guaranteed","urgent"}
    spam_hits = [w for w in spam_triggers if w in text]
    pii = bool(re.search(r"[\\w\\.-]+@[\\w\\.-]+|\\b\\d{3}[-.\\s]?\\d{3}[-.\\s]?\\d{4}\\b", text))
    safe = (len(spam_hits) == 0) and (not pii)
    return {"safe": safe, "spam_hits": spam_hits, "pii_detected": pii}


def reject_email_tool() -> str:
    return "Email rejected by human approval."


def deploy_email_to_sfmc_tool(governed_email: dict) -> dict:
    """
    Mock SFMC integration.
    In real life, this would call SFMC's REST API with auth headers.
    Here we just pretend and return an ID + status.
    """
    sfmc_id = f"sfmc_{uuid.uuid4().hex[:8]}"
    return {
        "sfmc_id": sfmc_id,
        "status": "queued",
        "note": "Mock SFMC draft created successfully."
    }



brand_check_tool = FunctionTool(brand_check)
safety_check_tool = FunctionTool(safety_check)
reject_email_tool = FunctionTool(reject_email_tool)
deploy_email_to_sfmc_tool = FunctionTool(deploy_email_to_sfmc_tool)

print("✅ FunctionTools ready: brand_check, safety_check, assemble_payload")