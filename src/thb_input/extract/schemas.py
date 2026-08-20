from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from thb_input.schemas.input import InputRecord
from thb_input.strip.schemas import StripResult


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceSource(StrEnum):
    OTHER = "other"
    USER_CONTEXT = "user_context"
    BOTH = "both"


class EpistemicStatus(StrEnum):
    REPORTED_BY_OTHER = "reported_by_other"
    REPORTED_BY_USER = "reported_by_user"
    SUPPORTED_BY_BOTH = "supported_by_both"
    INFERRED = "inferred"
    UNKNOWN = "unknown"
    CONFLICTING = "conflicting"


class Participant(StrictModel):
    participant_id: str = Field(pattern=r"^participant_\d{3,}$")
    name: str = Field(min_length=1)
    role: str | None
    source: EvidenceSource
    epistemic_status: EpistemicStatus
    supporting_segments: list[str]


class Claim(StrictModel):
    claim_id: str = Field(pattern=r"^claim_\d{3,}$")
    content: str = Field(min_length=1)
    source: EvidenceSource
    epistemic_status: EpistemicStatus
    supporting_segments: list[str]


class RequestStrength(StrEnum):
    REQUEST = "request"
    DEMAND = "demand"


class Request(StrictModel):
    request_id: str = Field(pattern=r"^req_\d{3,}$")
    actor: str = Field(min_length=1)
    target: str = Field(min_length=1)
    action: str = Field(min_length=1)
    requested_time: str | None
    strength: RequestStrength
    source: EvidenceSource
    supporting_segments: list[str]


class Commitment(StrictModel):
    commitment_id: str = Field(pattern=r"^commitment_\d{3,}$")
    actor: str = Field(min_length=1)
    content: str = Field(min_length=1)
    time: str | None
    condition: str | None
    source: EvidenceSource
    epistemic_status: EpistemicStatus
    supporting_segments: list[str]


class TimeConstraintType(StrEnum):
    REQUESTED_DEADLINE = "requested_deadline"
    CLAIMED_AGREED_DEADLINE = "claimed_agreed_deadline"
    USER_REPORTED_DEADLINE = "user_reported_deadline"
    SUPPORTED_DEADLINE = "supported_deadline"
    AMBIGUOUS_DEADLINE = "ambiguous_deadline"


class TimeConstraint(StrictModel):
    time_id: str = Field(pattern=r"^time_\d{3,}$")
    expression: str = Field(min_length=1)
    type: TimeConstraintType
    epistemic_status: EpistemicStatus
    source: EvidenceSource
    supporting_segments: list[str]


class Responsibility(StrictModel):
    responsibility_id: str = Field(pattern=r"^responsibility_\d{3,}$")
    actor: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source: EvidenceSource
    epistemic_status: EpistemicStatus
    basis: str | None
    supporting_segments: list[str]


class ConditionConsequenceKind(StrEnum):
    CONDITION = "condition"
    EXPLICIT_CONSEQUENCE = "explicit_consequence"
    IMPLICIT_CONSEQUENCE = "implicit_consequence"


class ConditionConsequence(StrictModel):
    relation_id: str = Field(pattern=r"^condition_\d{3,}$")
    kind: ConditionConsequenceKind
    content: str = Field(min_length=1)
    source: EvidenceSource
    epistemic_status: EpistemicStatus
    confidence: Confidence | None
    supporting_segments: list[str]


class EventRelationshipType(StrEnum):
    TEMPORAL = "temporal_relation"
    CAUSAL = "causal_relation"
    DEPENDENCY = "dependency_relation"
    CONDITIONAL = "conditional_relation"
    CLAIMED_CAUSALITY = "claimed_causality"


class EventRelationship(StrictModel):
    relationship_id: str = Field(pattern=r"^relationship_\d{3,}$")
    type: EventRelationshipType
    from_reference: str = Field(
        min_length=1,
        description="Existing object ID or concise source event reference.",
    )
    to_reference: str = Field(
        min_length=1,
        description="Existing object ID or concise target event reference.",
    )
    description: str = Field(min_length=1)
    epistemic_status: EpistemicStatus
    supporting_segments: list[str]


class Presupposition(StrictModel):
    presupposition_id: str = Field(pattern=r"^pre_\d{3,}$")
    content: str = Field(min_length=1)
    status: Literal["unverified", "supported", "conflicting"]
    supporting_segments: list[str]


class Inference(StrictModel):
    content: str = Field(min_length=1)
    confidence: Confidence
    basis: str = Field(min_length=1)
    supporting_segments: list[str]


class ImplicitMeaning(Inference):
    implicit_id: str = Field(pattern=r"^imp_\d{3,}$")


class PossibleIntention(Inference):
    intention_id: str = Field(pattern=r"^intent_\d{3,}$")


class PragmaticExplicitContent(StrictModel):
    content: str = Field(min_length=1)
    supporting_segments: list[str]


class PragmaticInference(StrictModel):
    content: str = Field(min_length=1)
    confidence: Confidence
    basis: str = Field(min_length=1)
    supporting_segments: list[str]


class PragmaticInterpretation(StrictModel):
    """Internal Level 1/2/3 separation used to compose the public Meaning."""

    explicit_content: list[PragmaticExplicitContent] = Field(min_length=1)
    implied_stances: list[PragmaticInference]
    contextual_implications: list[PragmaticInference]


class MeaningCandidateKind(StrEnum):
    CORE_SPEECH_ACT = "core_speech_act"
    MATERIAL_STANCE = "material_stance"
    FACT_BOUNDARY = "fact_boundary"
    RESPONSIBILITY = "responsibility"
    COMMITMENT = "commitment"
    CONSEQUENCE = "consequence"
    CONFLICT = "conflict"


class MeaningCandidate(StrictModel):
    content: str = Field(min_length=1)
    kind: MeaningCandidateKind
    confidence: Confidence
    materiality: Confidence
    basis: str = Field(min_length=1)
    supporting_segments: list[str]


class MeaningSelection(StrictModel):
    """Internal selection plan composed deterministically by MeaningService."""

    candidates: list[MeaningCandidate] = Field(min_length=1)


class ConflictPosition(StrictModel):
    source: EvidenceSource
    content: str = Field(min_length=1)
    supporting_segments: list[str]


class Conflict(StrictModel):
    conflict_id: str = Field(pattern=r"^conflict_\d{3,}$")
    topic: str = Field(min_length=1)
    positions: list[ConflictPosition] = Field(min_length=2)
    resolution: Literal["unresolved", "resolved_by_input"]


class Unknown(StrictModel):
    unknown_id: str = Field(pattern=r"^unknown_\d{3,}$")
    description: str = Field(min_length=1)
    importance: Confidence
    reason: str = Field(min_length=1)


class RiskType(StrEnum):
    COMMITMENT = "commitment_risk"
    RESPONSIBILITY = "responsibility_risk"
    DEADLINE = "deadline_risk"
    EVIDENCE = "evidence_risk"
    FINANCIAL = "financial_risk"
    RELATIONSHIP = "relationship_risk"
    ESCALATION = "escalation_risk"
    AMBIGUITY = "ambiguity_risk"
    DEPENDENCY = "dependency_risk"
    IRREVERSIBLE_ACTION = "irreversible_action_risk"
    OTHER = "other"


class Risk(StrictModel):
    risk_id: str = Field(pattern=r"^risk_\d{3,}$")
    risk_type: RiskType
    description: str = Field(min_length=1)
    confidence: Confidence
    basis: str = Field(min_length=1)
    supporting_segments: list[str]


class ExtractResult(StrictModel):
    analysis_version: Literal["0.1"]
    event_summary: str = Field(min_length=1)
    pragmatic_interpretation: PragmaticInterpretation
    meaning_selection: MeaningSelection
    participants: list[Participant]
    claims: list[Claim]
    requests: list[Request]
    commitments: list[Commitment]
    time_constraints: list[TimeConstraint]
    responsibilities: list[Responsibility]
    conditions_and_consequences: list[ConditionConsequence]
    event_relationships: list[EventRelationship]
    presuppositions: list[Presupposition]
    implicit_meanings: list[ImplicitMeaning]
    possible_intentions: list[PossibleIntention]
    conflicts: list[Conflict]
    unknowns: list[Unknown]
    risks: list[Risk]


class ExtractRequest(StrictModel):
    canonical_input: InputRecord
    strip_result: StripResult
