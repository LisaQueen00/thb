from enum import StrEnum


class CommunicationLabel(StrEnum):
    STATEMENT = "statement"
    PAST_EVENT_CLAIM = "past_event_claim"
    QUESTION = "question"
    REQUEST = "request"
    DEMAND = "demand"
    COMMITMENT = "commitment"
    CONDITION = "condition"
    CONSEQUENCE = "consequence"
    DEADLINE_EXPRESSION = "deadline_expression"
    PERSONAL_EVALUATION = "personal_evaluation"
    BLAME = "blame"
    RESPONSIBILITY_ASSIGNMENT = "responsibility_assignment"
    EMOTION_EXPRESSION = "emotion_expression"
    URGENCY_PRESSURE = "urgency_pressure"
    MORAL_PRESSURE = "moral_pressure"
    SOCIAL_PRESSURE = "social_pressure"
    RELATIONSHIP_PRESSURE = "relationship_pressure"
    AUTHORITY_PRESSURE = "authority_pressure"
    SARCASM = "sarcasm"
    PASSIVE_AGGRESSION = "passive_aggression"
    IMPLICIT_CONSEQUENCE = "implicit_consequence"
    PRESUPPOSITION = "presupposition"
    RHETORICAL_QUESTION = "rhetorical_question"
    VAGUE_REFERENCE = "vague_reference"
    AMBIGUOUS_OBLIGATION = "ambiguous_obligation"
    AMBIGUOUS_EXPRESSION = "ambiguous_expression"


IMPLICIT_LABELS = {
    CommunicationLabel.SARCASM,
    CommunicationLabel.PASSIVE_AGGRESSION,
    CommunicationLabel.IMPLICIT_CONSEQUENCE,
    CommunicationLabel.PRESUPPOSITION,
    CommunicationLabel.RHETORICAL_QUESTION,
}

PRESSURE_LABELS = {
    CommunicationLabel.URGENCY_PRESSURE,
    CommunicationLabel.MORAL_PRESSURE,
    CommunicationLabel.SOCIAL_PRESSURE,
    CommunicationLabel.RELATIONSHIP_PRESSURE,
    CommunicationLabel.AUTHORITY_PRESSURE,
}

EVALUATIVE_LABELS = {
    CommunicationLabel.PERSONAL_EVALUATION,
    CommunicationLabel.BLAME,
}
