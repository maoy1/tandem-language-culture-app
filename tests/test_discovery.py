"""Eligibility scenarios use synthetic account and catalogue identifiers."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tandem.discovery import Participant, eligible_candidates


def person(account, teach=(), learn=(), status="Active"):
    return Participant(account, status, frozenset(teach), frozenset(learn))


def test_reciprocal_match_uses_catalogue_ids_and_excludes_self():
    me = person("account-a", teach=[1], learn=[2])
    candidates = eligible_candidates(me, [me, person("account-b", [2], [1])])
    assert len(candidates) == 1
    assert candidates[0].account_id == "account-b"
    assert candidates[0].can_learn == {2}
    assert candidates[0].can_teach == {1}
    assert candidates[0].reciprocal


@pytest.mark.parametrize("teach,learn,other_teach,other_learn", [
    ([], [2], [2], []),  # Learner finds a sharer.
    ([1], [], [], [1]),  # Teach-only sharer finds a learner.
])
def test_one_way_exchange_is_eligible(teach, learn, other_teach, other_learn):
    matches = eligible_candidates(
        person("account-a", teach, learn),
        [person("account-b", other_teach, other_learn)],
    )
    assert len(matches) == 1
    assert not matches[0].reciprocal


@pytest.mark.parametrize("status", ["Needs review", "Paused", "Inactive", "", "Unknown"])
def test_non_active_profiles_cannot_discover_or_appear(status):
    me = person("account-a", learn=[2])
    other = person("account-b", teach=[2], status=status)
    assert eligible_candidates(me, [other]) == []
    assert eligible_candidates(person("account-a", learn=[2], status=status),
                               [person("account-b", teach=[2])]) == []


def test_no_language_compatibility_yields_no_candidates():
    assert eligible_candidates(person("account-a", learn=[2]), [
        person("account-b", teach=[3]),
        person("account-c"),
        person("account-d", learn=[2]),
    ]) == []


def test_multiple_languages_and_no_input_mutation():
    me = person("account-a", learn=[1, 2])
    other = person("account-b", teach=[2, 3])
    source = [me, other]
    assert eligible_candidates(me, source)[0].can_learn == {2}
    assert source == [me, other]
    assert other.teach_languages == {2, 3}


def test_duplicate_identity_is_rejected_instead_of_duplicate_suggestions():
    other = person("account-b", teach=[2])
    with pytest.raises(ValueError, match="Duplicate"):
        eligible_candidates(person("account-a", learn=[2]), [other, other])


@pytest.mark.parametrize("language", ["Dutch", "2", 0, -1, True])
def test_invalid_language_lookup_values_are_rejected(language):
    with pytest.raises(ValueError, match="catalogue IDs"):
        person("account-a", teach=[language])
