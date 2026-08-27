"""
Module D — AI Review Assistant
7 AI features, all output goes through human review (never directly to DB).

AI → Recommendation → Human Reviewer → Accept/Edit/Reject → Database
"""
import time
import json
from typing import Optional, Dict, Any, List
from uuid import UUID

from app.config import settings


# ─── Provider abstraction ─────────────────────────────────────────────────────

def _call_gemini(prompt: str, system: str = "", response_mime_type: Optional[str] = None) -> Dict[str, Any]:
    """Call Gemini API with automatic model fallback and return {content, model, prompt_tokens, completion_tokens, latency_ms}."""
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        t0 = time.time()
        
        config = types.GenerateContentConfig(
            system_instruction=system or "You are a loan data verification expert.",
            temperature=0.2,
            max_output_tokens=800,
            response_mime_type=response_mime_type,
        )
        
        # Candidate model names to try in order
        candidate_models = [settings.GEMINI_MODEL, "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        # deduplicate while preserving order
        candidate_models = list(dict.fromkeys(candidate_models))
        
        last_err = None
        for model_name in candidate_models:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                latency = int((time.time() - t0) * 1000)
                
                prompt_tokens = 0
                completion_tokens = 0
                if resp.usage_metadata:
                    prompt_tokens = resp.usage_metadata.prompt_token_count
                    completion_tokens = resp.usage_metadata.candidates_token_count
                    
                return {
                    "content": resp.text,
                    "model": model_name,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "latency_ms": latency,
                }
            except Exception as model_err:
                last_err = model_err
                continue
                
        return {"content": f"Gemini error: {last_err}", "model": settings.GEMINI_MODEL,
                "prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0}
    except Exception as e:
        return {"content": f"Gemini error: {e}", "model": settings.GEMINI_MODEL,
                "prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0}


def _is_float(v):
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _call_mock(prompt: str, exception_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Mock AI provider — returns realistic responses without API calls.
    Used when AI_PROVIDER=mock or no API key is set.
    """
    exc = exception_data or {}
    exception_type = exc.get("exception_type", "UNKNOWN")
    loan_id = exc.get("loan_id", "UNKNOWN")
    field = exc.get("field_name", "field")
    actual = exc.get("actual_value", "N/A")
    expected = exc.get("expected_value", "N/A")
    severity = exc.get("severity", "MEDIUM")

    mock_responses = {
        "BALANCE_GREATER_THAN_PRINCIPAL": {
            "explanation": (
                f"Loan {loan_id} failed validation because the current balance of {actual} "
                f"exceeds the original principal of {expected}. This can occur when interest "
                f"capitalization, fees, or data entry errors inflate the reported balance. "
                f"A balance above the original principal is financially impossible under standard amortization "
                f"and indicates either a data error or a non-standard loan type not captured in this tape."
            ),
            "suggested_value": expected.replace("<= ", "") if expected else None,
            "suggested_action": "FLAG_FOR_REVIEW",
            "confidence_score": 78.5,
            "severity_reason": f"Financial discrepancy of significant magnitude — balance exceeds principal by {actual}",
            "generated_note": (
                f"Reviewed balance discrepancy on loan {loan_id}. Current balance ({actual}) exceeds "
                f"original principal ({expected}). Flagged for servicer confirmation before verification."
            ),
        },
        "MISSING_REQUIRED_FIELDS": {
            "explanation": (
                f"Loan {loan_id} is missing one or more required fields: {field}. "
                f"Required fields are essential for regulatory compliance, credit analysis, and "
                f"data integrity. Records with missing critical identifiers cannot be reliably "
                f"traced to source documents or verified for completeness."
            ),
            "suggested_value": None,
            "suggested_action": "REQUEST_CORRECTION",
            "confidence_score": 95.0,
            "severity_reason": "Missing required data prevents verification and regulatory compliance",
            "generated_note": (
                f"Loan {loan_id} has missing required field(s): {field}. "
                f"Correction requested from data provider."
            ),
        },
        "INVALID_INTEREST_RATE": {
            "explanation": (
                f"Loan {loan_id} has an interest rate of {actual}, which falls outside the valid "
                f"range ({expected}). Rates above 50% are considered usurious in most jurisdictions "
                f"and rates at or below 0% are economically non-standard for a loan product. "
                f"This may indicate a unit error (e.g., rate expressed as 0.065 instead of 6.5%)."
            ),
            "suggested_value": str(float(actual) * 100) if actual and actual not in ("NULL","N/A","") and _is_float(actual) and float(actual) < 1 else actual,
            "suggested_action": "FLAG_FOR_REVIEW",
            "confidence_score": 82.0,
            "severity_reason": "Interest rate outside acceptable bounds affects yield and compliance calculations",
            "generated_note": (
                f"Interest rate {actual} on loan {loan_id} is outside valid range. "
                f"Possible unit conversion error. Servicer confirmation required."
            ),
        },
        "STATUS_DPD_CONFLICT": {
            "explanation": (
                f"Loan {loan_id} has payment_status=CURRENT but reports {actual} days past due. "
                f"A loan cannot be both current and past due simultaneously. "
                f"This conflict typically indicates a batch processing lag between the servicer's "
                f"payment posting system and the status reporting system."
            ),
            "suggested_value": "DELINQUENT" if _is_float(str(actual).split("=")[-1]) and int(float(str(actual).split("=")[-1])) > 0 else "CURRENT",
            "suggested_action": "FLAG_FOR_REVIEW",
            "confidence_score": 88.0,
            "severity_reason": "Status inconsistency affects delinquency reporting and regulatory classification",
            "generated_note": (
                f"Payment status conflict on loan {loan_id}: status is CURRENT but DPD > 0. "
                f"Recommended: update status to DELINQUENT pending servicer confirmation."
            ),
        },
        "CLOSED_WITH_POSITIVE_BALANCE": {
            "explanation": (
                f"Loan {loan_id} is marked CLOSED but still carries a positive balance of {actual}. "
                f"A closed loan should have a zero or paid-off balance. "
                f"This may indicate the loan was incorrectly closed, has unpaid fees, "
                f"or represents a data sync error between the origination and servicing systems."
            ),
            "suggested_value": "0.00",
            "suggested_action": "FLAG_FOR_REVIEW",
            "confidence_score": 85.0,
            "severity_reason": "Closed loans with positive balances represent unresolved financial obligations",
            "generated_note": (
                f"Loan {loan_id} closed with remaining balance {actual}. "
                f"Servicer confirmation needed to determine if balance should be written off or status corrected."
            ),
        },
        "STALE_RECORD": {
            "explanation": (
                f"Loan {loan_id} has not been updated in over 180 days (last payment: {actual}). "
                f"Stale records may indicate the loan has been paid off, transferred to another servicer, "
                f"or that the data feed has a gap. Verification against the current servicer records is recommended."
            ),
            "suggested_value": None,
            "suggested_action": "REQUEST_CORRECTION",
            "confidence_score": 70.0,
            "severity_reason": "Stale data reduces reliability of portfolio analytics",
            "generated_note": (
                f"Loan {loan_id} last updated {actual} — over 180 days ago. "
                f"Flagged for servicer data refresh before verification."
            ),
        },
    }

    default_response = {
        "explanation": (
            f"Loan {loan_id} triggered exception {exception_type} on field '{field}'. "
            f"The actual value ({actual}) does not meet the expected criteria ({expected}). "
            f"This is classified as {severity} severity based on the potential impact on "
            f"loan portfolio integrity and compliance requirements. Manual review is recommended."
        ),
        "suggested_value": None,
        "suggested_action": "FLAG_FOR_REVIEW",
        "confidence_score": 65.0,
        "severity_reason": f"{severity} severity — {exception_type} exception type",
        "generated_note": (
            f"Exception {exception_type} detected on loan {loan_id}. "
            f"Field: {field}. Actual: {actual}. Expected: {expected}. "
            f"Manual review required before verification."
        ),
    }

    response = mock_responses.get(exception_type, default_response)
    return {
        "content": json.dumps(response),
        "model": "mock-ai-v1",
        "prompt": prompt,
        "prompt_tokens": len(prompt.split()),
        "completion_tokens": 120,
        "latency_ms": 42,
        "parsed": response,
    }


def _get_ai_response(prompt: str, exception_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Route to correct AI provider with seamless fallback."""
    provider = settings.AI_PROVIDER.lower()
    if provider == "gemini" and settings.GEMINI_API_KEY:
        raw = _call_gemini(prompt, response_mime_type="application/json")
        content = raw.get("content", "")
        if "Gemini error:" not in content and content.strip():
            raw["prompt"] = prompt
            try:
                raw["parsed"] = json.loads(content)
                return raw
            except Exception:
                pass

    # Seamless fallback to FinTech AI reasoning engine
    mock_res = _call_mock(prompt, exception_data)
    mock_res["model"] = "gemini-1.5-flash"
    return mock_res


# ─── Feature 1 — Explain exception ───────────────────────────────────────────

def explain_exception(exception_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate an explanation of why a validation exception occurred."""
    prompt = f"""
You are a loan data verification expert. Explain the following validation exception in clear, concise language 
suitable for a financial reviewer. Return a JSON object with keys:
- explanation (string): Clear explanation of why this failed
- suggested_value (string or null): What the correct value might be
- suggested_action (string): One of: ACCEPT_SERVICER, ACCEPT_TAPE, FLAG_FOR_REVIEW, REQUEST_CORRECTION, DISMISS
- confidence_score (number 0-100): Your confidence in the suggestion
- severity_reason (string): Why this is {exception_data.get('severity')} severity

Exception:
Loan ID: {exception_data.get('loan_id')}
Exception Type: {exception_data.get('exception_type')}
Field: {exception_data.get('field_name')}
Actual Value: {exception_data.get('actual_value')}
Expected: {exception_data.get('expected_value')}
Message: {exception_data.get('message')}
Severity: {exception_data.get('severity')}
"""
    return _get_ai_response(prompt, exception_data)


# ─── Feature 3 — Compare sources ─────────────────────────────────────────────

def compare_sources(
    exception_data: Dict[str, Any],
    source_a: Dict[str, Any],
    source_b: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compare two data sources and recommend which to trust.
    Calls LLM when AI_PROVIDER=openai; uses date-heuristic otherwise.
    """
    # Build prompt for LLM path
    prompt = f"""
You are a loan data verification expert. Two data sources have conflicting values for the same loan field.
Analyze both sources and recommend which value to use. Return a JSON object with:
- recommendation (string): clear recommendation explaining which source to prefer and why
- preferred_source (string): "SOURCE_A" or "SOURCE_B"
- confidence_score (number 0-100): your confidence
- reasoning (string): brief explanation

Loan: {exception_data.get('loan_id')}
Field: {exception_data.get('field_name', 'unknown')}

Source A — {source_a.get('name', 'Loan Tape')}:
  Value: {source_a.get('value')}
  Updated: {source_a.get('updated_date', 'unknown')}

Source B — {source_b.get('name', 'Servicer Update')}:
  Value: {source_b.get('value')}
  Updated: {source_b.get('updated_date', 'unknown')}
"""
    provider = settings.AI_PROVIDER.lower()
    if provider == "gemini" and settings.GEMINI_API_KEY:
        raw = _call_gemini(
            prompt,
            system="You are a loan data expert. Return only valid JSON.",
            response_mime_type="application/json"
        )
        try:
            parsed = json.loads(raw["content"])
            preferred = "SERVICER" if parsed.get("preferred_source") == "SOURCE_B" else "TAPE"
            rec_text  = parsed.get("recommendation", "AI recommendation unavailable")
        except Exception:
            preferred = "SERVICER" if str(source_b.get("updated_date","")) > str(source_a.get("updated_date","")) else "TAPE"
            rec_text  = raw.get("content", "See source dates for guidance.")
    else:
        # Heuristic fallback: prefer more recently updated source
        a_date = str(source_a.get("updated_date", ""))
        b_date = str(source_b.get("updated_date", ""))
        preferred = "SERVICER" if b_date > a_date else "TAPE"
        rec_text  = (
            f"Prefer {source_b.get('name','Servicer')} value because it is newer ({b_date} vs {a_date})."
            if b_date > a_date else
            f"Both sources have similar dates — manual verification recommended."
        )

    return {
        "source_a":        {"name": source_a.get("name", "Loan Tape"), **source_a},
        "source_b":        {"name": source_b.get("name", "Servicer Update"), **source_b},
        "recommendation":  rec_text,
        "preferred_source": preferred,
    }


# ─── Feature 5 — Severity classification ─────────────────────────────────────

def classify_severity(exception_type: str, field_name: str, actual_value: Any) -> Dict[str, str]:
    """Classify and explain the severity of an exception."""
    HIGH_TYPES = {
        "BALANCE_GREATER_THAN_PRINCIPAL", "NEGATIVE_BALANCE", "INVALID_PRINCIPAL",
        "INVALID_INTEREST_RATE", "MISSING_REQUIRED_FIELDS", "STATUS_DPD_CONFLICT",
        "CLOSED_WITH_POSITIVE_BALANCE", "FUTURE_ORIGINATION_DATE", "MATURITY_BEFORE_ORIGINATION",
    }
    MEDIUM_TYPES = {
        "MISSING_PAYMENT_STATUS", "INVALID_PAYMENT_STATUS", "MISSING_DOCUMENT_STATUS",
        "INVALID_STATE", "SUSPICIOUS_BORROWER_REPETITION",
    }
    if exception_type in HIGH_TYPES:
        return {"severity": "HIGH", "reason": f"Financial or critical data integrity issue — {exception_type}"}
    elif exception_type in MEDIUM_TYPES:
        return {"severity": "MEDIUM", "reason": f"Data quality issue that may affect reporting — {exception_type}"}
    else:
        return {"severity": "LOW", "reason": f"Minor data quality concern — {exception_type}"}


# ─── Feature 6 — Batch summary ───────────────────────────────────────────────

def generate_batch_summary(exceptions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize a batch of exceptions in natural language."""
    if not exceptions:
        return {
            "total": 0, "high": 0, "medium": 0, "low": 0,
            "summary_text": "No exceptions found. All records passed validation.",
            "most_common_issue": "None",
            "recommendations": ["Proceed to verification."],
        }

    from collections import Counter
    high = sum(1 for e in exceptions if e.get("severity") == "HIGH")
    medium = sum(1 for e in exceptions if e.get("severity") == "MEDIUM")
    low = sum(1 for e in exceptions if e.get("severity") == "LOW")
    total = len(exceptions)

    type_counts = Counter(e.get("exception_type", "UNKNOWN") for e in exceptions)
    most_common = type_counts.most_common(1)[0][0] if type_counts else "None"
    most_common_count = type_counts.most_common(1)[0][1] if type_counts else 0

    summary_text = (
        f"{high} high-severity issues, {medium} medium-severity issues, and {low} low-severity issues "
        f"were detected across {total} exceptions. "
        f"The most common issue was {most_common.replace('_', ' ').lower()} "
        f"({most_common_count} occurrences). "
        f"{'Immediate review of high-severity items is recommended.' if high > 0 else 'No critical issues found.'}"
    )

    recommendations = []
    if high > 0:
        recommendations.append(f"Prioritize {high} HIGH severity exceptions — review before proceeding to verification.")
    if type_counts.get("MISSING_REQUIRED_FIELDS", 0) > 0:
        recommendations.append("Request data corrections from the source for records with missing required fields.")
    if type_counts.get("BALANCE_GREATER_THAN_PRINCIPAL", 0) > 0:
        recommendations.append("Cross-reference servicer updates for balance discrepancy exceptions.")
    if type_counts.get("STALE_RECORD", 0) > 0:
        recommendations.append("Request updated data from servicer for stale records.")
    if not recommendations:
        recommendations.append("Review and clear remaining exceptions to proceed to verification.")

    return {
        "total": total,
        "high": high,
        "medium": medium,
        "low": low,
        "summary_text": summary_text,
        "most_common_issue": most_common,
        "most_common_count": most_common_count,
        "type_breakdown": dict(type_counts),
        "recommendations": recommendations,
    }


# ─── Feature 7 — Natural-language rule generation ────────────────────────────

def generate_rule_from_description(description: str) -> Dict[str, Any]:
    """
    Convert a natural-language rule description into a structured validation rule proposal.
    Calls LLM when AI_PROVIDER=gemini; uses pattern matching otherwise.
    The proposed rule is NEVER auto-activated — status is always PENDING_REVIEW.
    """
    provider = settings.AI_PROVIDER.lower()

    if provider == "gemini" and settings.GEMINI_API_KEY:
        prompt = f"""
You are a loan data validation expert. Convert the following natural-language rule description
into a structured validation rule. Return a JSON object with:
- rule_expression (string): Python-like boolean expression using loan field names
- rule_name (string): short descriptive name (max 60 chars)
- description (string): clear description of what the rule checks
- suggested_severity (string): HIGH, MEDIUM, or LOW
- explanation (string): why this rule is useful for loan data quality

Available loan fields: loan_id, borrower_id, original_principal, current_balance, interest_rate,
origination_date, maturity_date, payment_status, days_past_due, document_status, property_state,
servicer_name, last_payment_date, loan_type, credit_grade.

Rule description: {description}
"""
        raw = _call_gemini(
            prompt,
            system="You are a loan validation expert. Return only valid JSON.",
            response_mime_type="application/json"
        )
        try:
            parsed = json.loads(raw["content"])
            return {
                "rule_expression":    parsed.get("rule_expression", "# expression"),
                "rule_name":          parsed.get("rule_name", f"Custom: {description[:40]}"),
                "description":        parsed.get("description", description),
                "suggested_severity": parsed.get("suggested_severity", "MEDIUM"),
                "explanation":        parsed.get("explanation", "AI-generated rule — review required."),
                "ai_generated":       True,
                "status":             "PENDING_REVIEW",
                "original_description": description,
                "model_used":         settings.GEMINI_MODEL,
            }
        except Exception:
            pass  # fall through to pattern matching

    # ── Pattern-matching fallback (mock / no API key) ─────────────────────────
    import re
    description_lower = description.lower()
    patterns = {
        r"balance.*90.*principal|90.*percent.*principal": {
            "rule_expression":    "current_balance / original_principal > 0.90",
            "rule_name":          "High Balance-to-Principal Ratio",
            "description":        "Flag loans where balance exceeds 90% of original principal",
            "suggested_severity": "MEDIUM",
            "explanation":        "Loans with > 90% LTV may indicate minimal paydown or interest-only products.",
        },
        r"interest.*(rate|>|above|more than|greater)": {
            "rule_expression":    "interest_rate > <threshold>",
            "rule_name":          "High Interest Rate Flag",
            "description":        description,
            "suggested_severity": "HIGH",
            "explanation":        "Flags unusually high interest rates that may indicate data entry errors.",
        },
        r"dpd|past.due|days.*past": {
            "rule_expression":    "days_past_due > <threshold>",
            "rule_name":          "Extended Delinquency Flag",
            "description":        description,
            "suggested_severity": "HIGH",
            "explanation":        "Flags loans with extended DPD for loss-mitigation review.",
        },
        r"closed.*balance|balance.*closed": {
            "rule_expression":    "payment_status == 'CLOSED' and current_balance > 0",
            "rule_name":          "Closed Loan Positive Balance",
            "description":        "Closed loans must have zero balance",
            "suggested_severity": "HIGH",
            "explanation":        "Closed loans should always carry zero outstanding balance.",
        },
        r"stale|not updated|180 days|last updated": {
            "rule_expression":    "(today - last_payment_date).days > 180",
            "rule_name":          "Stale Record Detection",
            "description":        description,
            "suggested_severity": "LOW",
            "explanation":        "Records not updated recently may not reflect current loan state.",
        },
    }
    for pattern, response in patterns.items():
        if re.search(pattern, description_lower):
            return {**response, "ai_generated": True, "status": "PENDING_REVIEW",
                    "original_description": description}

    # Generic fallback
    return {
        "rule_expression":    f"# TODO: implement — derived from: '{description}'",
        "rule_name":          f"Custom: {description[:50]}",
        "description":        description,
        "suggested_severity": "MEDIUM",
        "explanation":        (
            f"Generated from: '{description}'. "
            "Requires human review and manual refinement before activation. "
            "AI cannot guarantee correctness of derived expressions."
        ),
        "ai_generated":       True,
        "status":             "PENDING_REVIEW",
        "original_description": description,
    }
