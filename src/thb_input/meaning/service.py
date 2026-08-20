from difflib import SequenceMatcher

from thb_input.extract.schemas import (
    Confidence,
    ExtractResult,
    MeaningCandidate,
    MeaningCandidateKind,
)

from .schemas import MeaningResult


class MeaningService:
    """Select and compose the most material structured Extract information."""

    _kind_order = {
        MeaningCandidateKind.MATERIAL_STANCE: 0,
        MeaningCandidateKind.CORE_SPEECH_ACT: 1,
        MeaningCandidateKind.FACT_BOUNDARY: 2,
        MeaningCandidateKind.RESPONSIBILITY: 2,
        MeaningCandidateKind.COMMITMENT: 2,
        MeaningCandidateKind.CONSEQUENCE: 2,
        MeaningCandidateKind.CONFLICT: 2,
    }

    def process(self, result: ExtractResult) -> MeaningResult:
        selected = [
            candidate
            for candidate in result.meaning_selection.candidates
            if candidate.materiality is Confidence.HIGH
            and candidate.confidence is Confidence.HIGH
        ]
        selected.sort(key=lambda item: self._kind_order[item.kind])
        contents = self._deduplicate(
            [self._render(candidate) for candidate in selected]
        )
        if not contents:
            raise ValueError("Extract result has no high-materiality Meaning candidates")
        return MeaningResult(meaning="；".join(contents) + "。")

    @staticmethod
    def _render(candidate: MeaningCandidate) -> str:
        content = candidate.content.strip().rstrip("。！？；; ")
        if content.startswith("讲话者"):
            content = "对方" + content.removeprefix("讲话者")
        return content.replace("用户", "你")

    @staticmethod
    def _deduplicate(contents: list[str]) -> list[str]:
        unique: list[str] = []
        for content in contents:
            if any(
                content in existing
                or existing in content
                or SequenceMatcher(None, content, existing).ratio() >= 0.85
                for existing in unique
            ):
                continue
            unique.append(content)
        return unique
