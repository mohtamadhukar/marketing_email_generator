"""
Function Tools Module

This module defines programmatic tools that agents can use to perform deterministic
operations. These tools provide reliable, rule-based functionality that complements
LLM-based reasoning.

Design Pattern:
    - Function Tool Pattern: Wraps Python functions as callable tools for agents
    - Deterministic Operations: Provides reliable, repeatable logic for critical checks
    - Separation of Concerns: Business logic separated from agent orchestration

Tools:
    - brand_check: Programmatic brand compliance filtering
    - safety_check: Automated safety and compliance validation
    - reject_email_tool: Human rejection handler
    - deploy_email_to_sfmc_tool: SFMC deployment integration (mock)
"""

# Standard library imports
import json
import re
import uuid

# Third-party imports
from google.adk.tools.function_tool import FunctionTool


def brand_check(draft_email: dict, creative_guidelines: dict) -> dict:
    """
    Programmatic brand compliance filter for email content.
    
    Design: Provides deterministic rule-based filtering that complements LLM governance.
    This ensures critical brand rules are always enforced, even if LLM misses them.
    
    Implementation Details:
        - Case-insensitive banned phrase detection using set lookup (O(1) per phrase)
        - Subject line length truncation with rstrip to preserve formatting
        - Disclaimer appending to all body variants for legal compliance
        - Preserves original structure while filtering/transforming content
    
    Behavior:
        1. Extracts banned phrases from creative_guidelines and normalizes to lowercase
        2. Filters subject lines:
           - Removes any subject containing banned phrases (case-insensitive)
           - Truncates remaining subjects to length limit
        3. Appends disclaimer to all body variants if specified in guidelines
        4. Returns filtered content in same structure as input
    
    Args:
        draft_email: Dictionary with structure:
            {
                "subject_lines": [str, ...],  # List of subject line strings
                "body_variants": [str, ...]   # List of body text strings
            }
        creative_guidelines: Dictionary containing:
            {
                "banned_phrases": [str, ...],      # Phrases to filter out (optional)
                "subject_length_limit": int,       # Max subject length (default: 60)
                "disclaimer": str                  # Text to append to bodies (optional)
            }
    
    Returns:
        Dictionary with same structure as draft_email, but filtered and adjusted:
        {
            "subject_lines": [str, ...],  # Filtered and truncated subjects
            "body_variants": [str, ...]   # Bodies with disclaimers appended
        }
    
    Note: Currently not directly used by BrandAgent (which uses LLM), but available
    for programmatic enforcement if needed. Could be integrated for hybrid approach.
    """
    # Normalize banned phrases to lowercase set for O(1) lookup performance
    # Uses set comprehension for efficient membership testing
    banned = {b.lower() for b in (creative_guidelines.get("banned_phrases") or [])}
    # Get subject length limit with default fallback to 60 characters
    limit = int(creative_guidelines.get("subject_length_limit", 60))
    
    # Filter & trim subjects
    # Implementation: Iterates through subjects, filtering banned phrases and applying length limit
    filtered_subjects = []
    for s in draft_email.get("subject_lines", []):
        # Case-insensitive banned phrase detection
        # Uses any() for short-circuit evaluation (stops at first match)
        if any(b in s.lower() for b in banned): 
            continue  # Skip this subject line entirely if it contains banned phrase
        # Truncate to limit and remove trailing whitespace
        s = s[:limit].rstrip()
        filtered_subjects.append(s)
    
    # Append disclaimer to bodies
    # Implementation: Creates a copy of body list to avoid mutating original
    # Appends disclaimer as italicized text at the end of each body variant
    bodies = draft_email.get("body_variants", [])[:]  # [:] creates shallow copy
    disclaimer = creative_guidelines.get("disclaimer")
    if disclaimer:
        # List comprehension to append disclaimer to all body variants
        # Format: adds two newlines and italicized disclaimer
        bodies = [b + f"\n\n*{disclaimer}*" for b in bodies]
    
    return {"subject_lines": filtered_subjects, "body_variants": bodies}

def safety_check(governed_email: dict) -> dict:
    """
    Automated safety and compliance validation for email content.
    
    Design: Provides deterministic safety checks that complement LLM-based review.
    This ensures critical safety rules are always enforced programmatically.
    
    Implementation Details:
        - Converts entire email structure to JSON string for comprehensive text search
        - Uses case-insensitive matching by converting to lowercase
        - Spam detection via keyword matching against known trigger words
        - PII detection via regex patterns for emails and phone numbers
        - Returns structured report with boolean flags and detected issues
    
    Behavior:
        1. Serializes governed_email to JSON string for text analysis
        2. Checks for spam trigger words (case-insensitive):
           - "free", "guaranteed", "urgent" (common spam indicators)
        3. Detects PII using regex patterns:
           - Email addresses: word@word.domain format
           - Phone numbers: 10-digit patterns with various separators
        4. Determines overall safety: safe only if no spam triggers AND no PII
        5. Returns detailed report for human review
    
    Args:
        governed_email: Dictionary containing the email content to check.
                       Structure can vary, but will be serialized to JSON for analysis.
    
    Returns:
        Dictionary with safety validation results:
        {
            "safe": bool,              # True if email passes all checks
            "spam_hits": [str, ...],   # List of detected spam trigger words
            "pii_detected": bool       # True if PII patterns found in content
        }
    
    Note: This is a "naive" implementation for demo purposes. Production systems would:
        - Use more sophisticated NLP models for spam detection
        - Implement comprehensive PII detection (SSN, credit cards, etc.)
        - Add content moderation for inappropriate language
        - Integrate with external compliance APIs
    """
    # Serialize email to JSON string for comprehensive text search
    # Lowercase conversion enables case-insensitive matching
    text = json.dumps(governed_email).lower()
    
    # Spam trigger word detection
    # Design: Uses set of known spam indicators commonly flagged by email filters
    # Implementation: Set membership testing for O(1) lookup performance
    spam_triggers = {"free","guaranteed","urgent"}
    # List comprehension to collect all detected trigger words
    spam_hits = [w for w in spam_triggers if w in text]
    
    # PII (Personally Identifiable Information) detection
    # Implementation: Uses regex to find email addresses and phone numbers
    # Pattern breakdown:
    #   - Email: [\w\.-]+@[\w\.-]+ (word chars, dots, hyphens @ word chars, dots, hyphens)
    #   - Phone: \b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b (3-3-4 digit pattern with optional separators)
    # Note: Regex pattern has escaped backslashes for Python string literal
    pii = bool(re.search(r"[\\w\\.-]+@[\\w\\.-]+|\\b\\d{3}[-.\\s]?\\d{3}[-.\\s]?\\d{4}\\b", text))
    
    # Overall safety determination
    # Safe only if: no spam triggers detected AND no PII detected
    safe = (len(spam_hits) == 0) and (not pii)
    
    return {"safe": safe, "spam_hits": spam_hits, "pii_detected": pii}


def reject_email_tool() -> str:
    """
    Handler for human rejection of email content.
    
    Design: Simple acknowledgment function that marks email as rejected.
    In a production system, this would log the rejection, update status in database,
    and potentially trigger feedback collection or revision workflows.
    
    Behavior:
        - Returns confirmation message that email was rejected
        - Root agent uses this to acknowledge human decision
        - Could be extended to log rejection reason, timestamp, etc.
    
    Returns:
        String confirmation message indicating email rejection
    """
    return "Email rejected by human approval."


def deploy_email_to_sfmc_tool(governed_email: dict) -> dict:
    """
    Deploys approved email to Salesforce Marketing Cloud (SFMC).
    
    Design: Integration point with external email marketing platform.
    Currently implemented as a mock for development/demo purposes.
    
    Implementation (Mock):
        - Generates a mock SFMC ID using UUID
        - Returns a simulated deployment response
        - Does not perform actual API call
    
    Production Implementation Would:
        1. Authenticate with SFMC using OAuth2 or API key
        2. Transform governed_email to SFMC API format (HTML, text, metadata)
        3. Make REST API call to SFMC Content Builder or Email Studio
        4. Handle API errors and retries
        5. Return actual SFMC content ID and deployment status
        6. Log deployment for audit trail
    
    Behavior:
        - Accepts governed_email dictionary containing final email content
        - Generates unique identifier for tracking
        - Returns deployment status and metadata
    
    Args:
        governed_email: Dictionary containing the final, approved email content
                       to be deployed. Structure should match SFMC API requirements.
    
    Returns:
        Dictionary with deployment information:
        {
            "sfmc_id": str,      # Unique identifier for the deployed email in SFMC
            "status": str,       # Deployment status (e.g., "queued", "deployed", "failed")
            "note": str          # Human-readable status message
        }
    
    Note: This is a mock implementation. Replace with actual SFMC REST API integration
    for production use. Consider implementing:
        - Error handling and retry logic
        - Rate limiting compliance
        - Webhook callbacks for async deployment status
        - Rollback capability for failed deployments
    """
    # Generate mock SFMC ID using UUID
    # Implementation: Uses UUID4 for randomness, takes first 8 hex chars for shorter ID
    # Format: "sfmc_" prefix + 8-character hex string (e.g., "sfmc_a1b2c3d4")
    sfmc_id = f"sfmc_{uuid.uuid4().hex[:8]}"
    
    return {
        "sfmc_id": sfmc_id,
        "status": "queued",  # Typical initial status in email marketing platforms
        "note": "Mock SFMC draft created successfully."
    }



# Function Tool Wrappers
# Design: Wraps Python functions as callable tools that agents can invoke
# Implementation: FunctionTool automatically generates tool schemas from function signatures
# Behavior: Agents can call these tools by name, passing arguments and receiving return values
#
# Tool Registration:
#   - brand_check_tool: Available for programmatic brand filtering (currently unused)
#   - safety_check_tool: Used by SafetyAgent for automated compliance checks
#   - reject_email_tool: Used by RootAgent when human rejects email
#   - deploy_email_to_sfmc_tool: Used by RootAgent when human approves email

brand_check_tool = FunctionTool(brand_check)
safety_check_tool = FunctionTool(safety_check)
reject_email_tool = FunctionTool(reject_email_tool)
deploy_email_to_sfmc_tool = FunctionTool(deploy_email_to_sfmc_tool)

print("✅ FunctionTools ready: brand_check, safety_check, assemble_payload")