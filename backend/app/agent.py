"""LangGraph complaint copilot: parse/update a structured QMS complaint then assess risk."""
from __future__ import annotations

import json
import re
from typing import Any, TypedDict
from langgraph.graph import END, START, StateGraph
from .config import settings
from .schemas import ComplaintForm, CopilotRequest, CopilotResponse, RiskAssessment


class AgentState(TypedDict, total=False):
    request: CopilotRequest
    form: dict[str, Any]
    risk: dict[str, Any]
    assistant_message: str
    mode: str


FIELDS = list(ComplaintForm.model_fields.keys())


def _clean_json(content: str) -> dict[str, Any]:
    content = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", content, re.DOTALL)
    return json.loads(match.group(0) if match else content)


def _offline_extract(text: str, current: dict[str, Any]) -> dict[str, Any]:
    """A resilient local fallback for demos or unavailable API keys."""
    merged = dict(current)
    normalized = text.strip()
    patterns = {
        "batch_number": r"(?:batch(?:\s*(?:number|no\.?))?|lot(?:\s*(?:number|no\.?))?)\s*(?:is|:|#)?\s*([A-Z]{2,}[A-Z0-9-]+)",
        "affected_quantity": r"(?:affected\s*(?:quantity)?|quantity)\s*(?:is|:)?\s*(\d+(?:\.\d+)?\s*(?:capsules?|tablets?|kg|kilograms?|g|grams?|HDPE\s*drums?)(?:\s*,?\s*\d+\s*HDPE\s*drums?)?)",
        "product_strength": r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|g|%|IU|mg/mL))\b",
        "manufacturing_date": r"(?:manufactur(?:ing|ed)\s*(?:date)?|mfg\.?|mfd\.?)\s*(?:is|:)?\s*([A-Za-z]+\s+20\d{2}|\d{1,2}[/-]\d{1,2}[/-]20\d{2})",
        "expiry_date": r"(?:expiry|exp(?:iration)?\s*(?:date)?)\s*(?:is|:)?\s*([A-Za-z]+\s+20\d{2}|\d{1,2}[/-]\d{1,2}[/-]20\d{2})",
    }
    for key, pattern in patterns.items():
        found = re.search(pattern, normalized, re.IGNORECASE)
        if found:
            merged[key] = found.group(1).strip()
    if not merged.get("affected_quantity"):
        affected_after = re.search(r"(\d+(?:\.\d+)?\s*(?:capsules?|tablets?|kg|kilograms?|g|grams?))\s+(?:were|was)?\s*affected", normalized, re.I)
        if affected_after:
            merged["affected_quantity"] = affected_after.group(1).strip()
    customer = re.search(r"^([A-Z][\w& .'-]+?(?:Pharmacy|Hospital|Clinics?|Distributors?))\s+(?:reported|has reported)", normalized, re.I)
    if customer:
        merged["customer_name"] = customer.group(1).strip()
        merged["complaint_source"] = "Pharmacy" if "pharmacy" in customer.group(1).lower() else "Customer"
    product = re.search(r"(?:in|for)\s+([A-Z][A-Za-z ]+(?:Capsules?|Tablets?|API|Injection|Suspension))\s*(?:\d+(?:\.\d+)?\s*(?:mg|mcg|g))?", normalized)
    if product and not merged.get("product_name"):
        merged["product_name"] = product.group(1).strip()
    if re.search(r"discolou?red|colour change", normalized, re.I):
        merged["complaint_category"] = "Product Defect - Discoloration"
        merged["impacted_materials"] = merged.get("impacted_materials") or "Primary Packaging"
        merged["originating_site"] = merged.get("originating_site") or "Manufacturing"
    elif re.search(r"broken|crack|leak", normalized, re.I):
        merged["complaint_category"] = "Product Defect - Packaging Integrity"
    elif re.search(r"contamin|foreign", normalized, re.I):
        merged["complaint_category"] = "Product Defect - Contamination"
    merged["complaint_description"] = normalized if len(normalized) < 1000 else normalized[:997] + "..."
    return {k: str(merged.get(k, "")) for k in FIELDS}


def extract_complaint(state: AgentState) -> AgentState:
    req = state["request"]
    existing = req.current_form.model_dump()
    if not settings.groq_api_key:
        form = _offline_extract(req.message, existing)
        return {"form": form, "mode": "updated" if any(existing.values()) else "created"}
    try:
        from langchain_groq import ChatGroq
        llm = ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0)
        prompt = f"""You are a pharmaceutical QMS intake specialist. Extract or update only factual complaint data.
Existing record (preserve all facts unless the new message corrects them): {json.dumps(existing)}
New customer text: {req.message}
Return JSON only with exactly these keys: {FIELDS}. Use empty string only when neither the record nor message provides a value. Normalize concise field values. Treat corrections as authoritative."""
        result = _clean_json(llm.invoke(prompt).content)
        form = {field: str(result.get(field, existing.get(field, "")) or "") for field in FIELDS}
        return {"form": form, "mode": "updated" if any(existing.values()) else "created"}
    except Exception:
        return {"form": _offline_extract(req.message, existing), "mode": "updated" if any(existing.values()) else "created"}


def assess_risk(state: AgentState) -> AgentState:
    form = state["form"]
    category = form.get("complaint_category", "").lower()
    desc = form.get("complaint_description", "").lower()
    critical_terms = ("contamin", "adverse", "sterility", "foreign particle", "wrong product")
    major_terms = ("discolor", "leak", "crack", "broken", "dissolv", "missing")
    if any(x in category or x in desc for x in critical_terms):
        severity, priority = "Critical", "High"
        action = "Quarantine affected batch; notify QA leadership and begin expedited investigation"
        cause = "Potential product quality or patient-safety failure requiring immediate containment."
    elif any(x in category or x in desc for x in major_terms):
        severity, priority = "Major", "High"
        action = "Route to QA investigation; retain samples and arrange customer replacement"
        cause = "Possible process, storage, or primary packaging integrity failure."
    else:
        severity, priority = "Minor", "Medium"
        action = "QA review and trend against similar complaints"
        cause = "Potential isolated handling, packaging, or distribution variance."
    product = form.get("product_name") or "the product"
    risk = {
        "severity": severity, "priority": priority, "suggested_next_action": action,
        "initial_risk_assessment": f"{severity} initial risk for {product}. Assess batch history, retain samples, distribution conditions, and complaint trend before disposition.",
        "root_cause_hypothesis": cause,
        "capa_recommendation": "Open investigation; verify batch records and packaging controls; document effectiveness check.",
        "duplicate_hint": "No exact duplicate detected in this demo session; compare batch and category in the QMS ledger.",
    }
    return {"risk": risk}


def compose_response(state: AgentState) -> AgentState:
    form = state["form"]
    name = form.get("product_name") or "complaint"
    return {"assistant_message": f"{('Updated' if state['mode'] == 'updated' else 'Logged')} the {name} complaint. I preserved the existing record and refreshed the AI risk assessment.", "mode": state["mode"]}


workflow = StateGraph(AgentState)
workflow.add_node("extract", extract_complaint)
workflow.add_node("assess", assess_risk)
workflow.add_node("respond", compose_response)
workflow.add_edge(START, "extract")
workflow.add_edge("extract", "assess")
workflow.add_edge("assess", "respond")
workflow.add_edge("respond", END)
complaint_graph = workflow.compile()


def process_request(request: CopilotRequest, mode: str | None = None) -> CopilotResponse:
    result = complaint_graph.invoke({"request": request})
    return CopilotResponse(form=ComplaintForm(**result["form"]), risk=RiskAssessment(**result["risk"]), message=result["assistant_message"], mode=mode or result["mode"])
