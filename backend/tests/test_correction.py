from hanasu_backend.conversation.correction import finalize_correction
from hanasu_backend.conversation.models import DraftCorrection, DraftIssue

ORIGINAL = "昨日映画が見ました"


def _issue(span: str) -> DraftIssue:
    return DraftIssue(
        category="particle", original_span=span, suggestion="映画を", note="Use を for objects."
    )


def test_ok_clears_issues_and_keeps_original() -> None:
    draft = DraftCorrection(ok=True, corrected="違う文", issues=[_issue("映画が")])
    result = finalize_correction(ORIGINAL, draft)
    assert result.ok
    assert result.corrected == ORIGINAL
    assert result.issues == []


def test_not_ok_without_any_change_counts_as_ok() -> None:
    result = finalize_correction(ORIGINAL, DraftCorrection(ok=False, corrected=ORIGINAL, issues=[]))
    assert result.ok


def test_span_is_located_in_original() -> None:
    draft = DraftCorrection(ok=False, corrected="昨日映画を見ました", issues=[_issue("映画が")])
    issue = finalize_correction(ORIGINAL, draft).issues[0]
    assert (issue.start, issue.end) == (2, 5)


def test_span_not_in_original_gets_no_highlight() -> None:
    draft = DraftCorrection(ok=False, corrected="昨日映画を見ました", issues=[_issue("えいがが")])
    issue = finalize_correction(ORIGINAL, draft).issues[0]
    assert issue.start is None
    assert issue.note
