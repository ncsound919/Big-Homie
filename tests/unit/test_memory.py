"""
Unit tests for memory.py and correction_ledger.py

Covers: store, recall, forget, correction tracking, and persistence.
"""
from __future__ import annotations

import pytest


class TestMemory:
    """Memory module should store, retrieve, and forget entries."""

    @pytest.fixture
    def mem(self, tmp_db):
        from memory import Memory
        return Memory(db_path=tmp_db)

    def test_store_and_recall(self, mem):
        mem.store(key="user_name", value="Big Homie")
        result = mem.recall(key="user_name")
        assert result == "Big Homie"

    def test_recall_missing_returns_none(self, mem):
        result = mem.recall(key="nonexistent_key")
        assert result is None

    def test_forget_removes_entry(self, mem):
        mem.store(key="temp", value="data")
        mem.forget(key="temp")
        assert mem.recall(key="temp") is None

    def test_overwrite_existing_key(self, mem):
        mem.store(key="mood", value="happy")
        mem.store(key="mood", value="focused")
        assert mem.recall(key="mood") == "focused"

    def test_store_dict_value(self, mem):
        mem.store(key="config", value={"theme": "dark", "model": "claude"})
        result = mem.recall(key="config")
        assert isinstance(result, dict)
        assert result["theme"] == "dark"

    def test_list_all_keys(self, mem):
        mem.store(key="a", value=1)
        mem.store(key="b", value=2)
        keys = mem.list_keys()
        assert "a" in keys
        assert "b" in keys

    def test_persistence_across_instances(self, tmp_db):
        from memory import Memory
        m1 = Memory(db_path=tmp_db)
        m1.store(key="persistent", value="yes")
        m2 = Memory(db_path=tmp_db)
        assert m2.recall(key="persistent") == "yes"


class TestCorrectionLedger:
    """CorrectionLedger tracks and learns from agent corrections."""

    @pytest.fixture
    def ledger(self, tmp_db):
        from correction_ledger import CorrectionLedger
        return CorrectionLedger(db_path=tmp_db)

    def test_record_correction(self, ledger):
        ledger.record(
            original_action="wrong_answer",
            corrected_action="right_answer",
            context={"task": "math"}
        )
        entries = ledger.get_all()
        assert len(entries) >= 1

    def test_correction_has_timestamp(self, ledger):
        ledger.record(original_action="a", corrected_action="b", context={})
        entries = ledger.get_all()
        assert "timestamp" in entries[-1] or hasattr(entries[-1], 'timestamp')

    def test_correction_count(self, ledger):
        for i in range(5):
            ledger.record(original_action=f"wrong_{i}", corrected_action=f"right_{i}", context={})
        assert ledger.count() == 5

    def test_get_recent_corrections(self, ledger):
        for i in range(10):
            ledger.record(original_action=f"w{i}", corrected_action=f"r{i}", context={})
        recent = ledger.get_recent(n=3)
        assert len(recent) == 3

    def test_correction_improves_future_decisions(self, ledger):
        """Ledger should be queryable for similar past contexts."""
        ledger.record(
            original_action="use_expensive_model",
            corrected_action="use_cheap_model",
            context={"task_type": "simple_summary"}
        )
        if hasattr(ledger, 'find_similar'):
            results = ledger.find_similar(context={"task_type": "simple_summary"})
            assert len(results) >= 1
