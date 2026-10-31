"""Pure discovery eligibility over trusted, normalized participant records.

This module is not an authorization endpoint. A future authorized adapter must
load records and map language lookups to catalogue IDs before calling it.
"""

from dataclasses import dataclass
from collections.abc import Iterable


@dataclass(frozen=True)
class Participant:
    account_id: str
    status: str
    teach_languages: frozenset[int] = frozenset()
    learn_languages: frozenset[int] = frozenset()

    def __post_init__(self) -> None:
        if not self.account_id or not self.account_id.strip():
            raise ValueError("A canonical account ID is required")
        # Copy inputs so callers cannot mutate an already-validated profile.
        for name in ("teach_languages", "learn_languages"):
            values = frozenset(getattr(self, name))
            if any(type(value) is not int or value <= 0 for value in values):
                raise ValueError("Languages must be positive integer catalogue IDs")
            object.__setattr__(self, name, values)


@dataclass(frozen=True)
class Candidate:
    account_id: str
    can_learn: frozenset[int]
    can_teach: frozenset[int]

    @property
    def reciprocal(self) -> bool:
        return bool(self.can_learn and self.can_teach)


def eligible_candidates(
    current: Participant, participants: Iterable[Participant]
) -> list[Candidate]:
    """Return compatible Active candidates without ranking or side effects.

    A one-way exchange is sufficient, including a teach-only participant finding
    a learner. Both directions make an exchange reciprocal. Missing, unknown,
    paused and inactive statuses fail closed. No open-to-connections field exists
    in the approved schema; a later participation-status decision can extend it.
    """
    if current.status != "Active":
        return []

    result = []
    seen = set()
    for participant in participants:
        if participant.account_id == current.account_id:
            continue
        if participant.account_id in seen:
            raise ValueError("Duplicate participant identity in discovery input")
        seen.add(participant.account_id)
        if participant.status != "Active":
            continue
        can_learn = current.learn_languages & participant.teach_languages
        can_teach = current.teach_languages & participant.learn_languages
        if can_learn or can_teach:
            result.append(Candidate(participant.account_id, can_learn, can_teach))
    return result
