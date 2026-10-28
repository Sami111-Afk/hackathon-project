"""Contractul comun. Vezi ARCHITECTURE.md §3. Schimbările se anunță pe grup."""
from typing import Any, Literal

from pydantic import BaseModel, Field

AgentName = Literal["paznic", "functionar", "verificator", "detector", "detectiv", "compliance"]
Severity = Literal["info", "low", "medium", "high", "critical"]
AgentStatus = Literal["pending", "running", "done", "error", "skipped"]
CaseStatus = Literal["received", "processing", "awaiting_review", "cleared", "rejected", "escalated", "error"]
DocType = Literal["id_card", "payslip", "bank_statement", "employment_certificate", "other", "unknown"]
EventType = Literal[
    "case_created", "agent_started", "agent_progress", "agent_finished", "agent_error",
    "debate", "verdict", "decision", "rule_proposed", "rule_approved", "arena_scored", "ping",
]


class Evidence(BaseModel):
    doc_id: str | None = None
    page: int | None = None
    bbox: list[float] | None = None  # [x0, y0, x1, y1] în pixeli pe pagină
    field: str | None = None


class Finding(BaseModel):
    code: str
    severity: Severity
    message: str
    evidence: Evidence | None = None
    rule_id: str | None = None


class LLMUsage(BaseModel):
    provider: Literal["bedrock", "featherless", "ollama", "mock", "cache"]
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class AgentResult(BaseModel):
    agent: AgentName
    status: AgentStatus
    risk: float | None = None
    duration_ms: int = 0
    error: str | None = None  # mesaj generic + ID de corelare, fără valori din document
    findings: list[Finding] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)
    llm_usage: LLMUsage | None = None


class PageInfo(BaseModel):
    page: int
    width: int
    height: int


class ExtractedValue(BaseModel):
    value: Any = None
    source_text: str | None = None


class Document(BaseModel):
    id: str
    type: DocType = "unknown"
    filename: str
    pages: list[PageInfo] = Field(default_factory=list)
    redacted_text: str | None = None
    extracted: dict[str, ExtractedValue] | None = None


class Verdict(BaseModel):
    risk: float
    label: Literal["clean", "suspicious", "forged", "identity_fraud", "fraud_ring"]
    summary: str
    recommendation: Literal["clear", "review", "escalate"]
    incomplete: bool = False


class Decision(BaseModel):
    action: Literal["clear", "reject", "escalate", "flag_network", "correct"]
    decided_by: str
    notes: str = ""
    corrections: dict[str, Any] = Field(default_factory=dict)
    decided_at: str | None = None


class Case(BaseModel):
    id: str
    source: Literal["bank", "arena"] = "bank"
    status: CaseStatus = "received"
    created_at: str
    requested_amount_ron: float | None = None
    applicant_token: str | None = None
    documents: list[Document] = Field(default_factory=list)
    fingerprints: dict[str, list[str]] = Field(default_factory=dict)
    results: list[AgentResult] = Field(default_factory=list)
    verdict: Verdict | None = None
    decision: Decision | None = None


class PipelineEvent(BaseModel):
    case_id: str
    seq: int
    ts: str
    type: EventType
    agent: AgentName | None = None
    message: str = ""
    data: dict[str, Any] | None = None
