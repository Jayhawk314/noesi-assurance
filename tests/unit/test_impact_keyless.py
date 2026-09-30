"""Record types with no key field are compared row by row as whole rows."""
from decimal import Decimal

from assurance_application.impact import diff_records, thresholds


def test_an_appended_file_shows_only_the_added_rows():
    june = [{"entry_id": "1", "debit": "100", "source_row": 1, "source_hash": "a"},
            {"entry_id": "1", "debit": "100", "source_row": 2, "source_hash": "a"}]
    july = [{"entry_id": "9", "debit": "25", "source_row": 1, "source_hash": "b"}]
    out = diff_records(june, june + july, (), thresholds(15000))
    assert out["key_fields"] == ["whole row"] and out["duplicate_keys"] == []
    assert out["removed"] == [] and out["changed"] == []
    assert len(out["added"]) == 1 and out["added"][0]["key"].startswith("9")


def test_identical_rows_from_a_reloaded_file_cancel_out():
    rows = [{"a": "1", "source_row": 1, "source_hash": "x"}]
    moved = [{"a": "1", "source_row": 7, "source_hash": "y"}]
    out = diff_records(rows, moved, (), thresholds(15000))
    assert out["added"] == [] and out["removed"] == []
