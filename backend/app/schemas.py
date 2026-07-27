from typing import Literal
from pydantic import BaseModel, Field


class ComplaintForm(BaseModel):
    complaint_source: str = ""
    customer_name: str = ""
    product_name: str = ""
    product_strength: str = ""
    batch_number: str = ""
    affected_quantity: str = ""
    manufacturing_date: str = ""
    expiry_date: str = ""
    originating_site: str = ""
    impacted_materials: str = ""
    complaint_category: str = ""
    complaint_description: str = ""
    reporter_contact: str = ""


class RiskAssessment(BaseModel):
    severity: Literal["Critical", "Major", "Minor", "Pending"] = "Pending"
    priority: Literal["High", "Medium", "Low", "Pending"] = "Pending"
    suggested_next_action: str = "Awaiting complaint details"
    initial_risk_assessment: str = "AIVOA will assess product quality risk after extracting complaint details."
    root_cause_hypothesis: str = ""
    capa_recommendation: str = ""
    duplicate_hint: str = "No comparable complaints in the current session."


class CopilotResponse(BaseModel):
    form: ComplaintForm
    risk: RiskAssessment
    message: str
    mode: Literal["created", "updated", "extracted"]


class CopilotRequest(BaseModel):
    message: str = Field(min_length=2, max_length=8000)
    current_form: ComplaintForm = Field(default_factory=ComplaintForm)
    current_risk: RiskAssessment = Field(default_factory=RiskAssessment)


class CommitRequest(BaseModel):
    form: ComplaintForm
    risk: RiskAssessment

