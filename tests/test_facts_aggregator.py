"""
Unit tests for ChapterFactsAggregator — pure logic, no DB required.

Tests cover:
- Deduplication: same actor+target keeps latest fact
- Grouping: facts route to correct fact_type bucket
- Conflict detection: same actor+target but different content → latest wins
- Edge cases: unknown fact_type, empty input, missing fields
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from workflow.facts_aggregator import aggregate_facts, FACT_TYPES


class TestFactTypeBuckets:
    """aggregate_facts routes facts to the correct fact_type bucket."""

    def test_relationship_change_goes_to_correct_bucket(self):
        facts = [{"fact_type": "relationship_changes", "actor": "Alice", "target": "Bob", "content": "became friends"}]
        result = aggregate_facts(facts)
        assert len(result["relationship_changes"]) == 1
        assert result["relationship_changes"][0]["actor"] == "Alice"

    def test_world_change_goes_to_correct_bucket(self):
        facts = [{"fact_type": "world_changes", "actor": "city", "target": "", "content": "burned down"}]
        result = aggregate_facts(facts)
        assert len(result["world_changes"]) == 1

    def test_timeline_change_goes_to_correct_bucket(self):
        facts = [{"fact_type": "timeline_changes", "actor": "story", "target": "", "content": "three days passed"}]
        result = aggregate_facts(facts)
        assert len(result["timeline_changes"]) == 1

    def test_new_information_goes_to_correct_bucket(self):
        facts = [{"fact_type": "new_information", "actor": "Bob", "target": "", "content": "Bob is a spy"}]
        result = aggregate_facts(facts)
        assert len(result["new_information"]) == 1

    def test_unknown_fact_type_falls_back_to_new_information(self):
        facts = [{"fact_type": "some_unknown_type", "actor": "X", "target": "Y", "content": "something"}]
        result = aggregate_facts(facts)
        # Unknown types are routed to new_information
        assert len(result["new_information"]) == 1
        assert len(result["relationship_changes"]) == 0

    def test_facts_without_fact_type_default_to_new_information(self):
        facts = [{"actor": "X", "target": "", "content": "something happened"}]
        result = aggregate_facts(facts)
        assert len(result["new_information"]) == 1

    def test_multiple_facts_across_all_buckets(self):
        facts = [
            {"fact_type": "relationship_changes", "actor": "A", "target": "B", "content": "c1"},
            {"fact_type": "world_changes", "actor": "place", "target": "", "content": "c2"},
            {"fact_type": "timeline_changes", "actor": "time", "target": "", "content": "c3"},
            {"fact_type": "new_information", "actor": "spy", "target": "", "content": "c4"},
        ]
        result = aggregate_facts(facts)
        assert len(result["relationship_changes"]) == 1
        assert len(result["world_changes"]) == 1
        assert len(result["timeline_changes"]) == 1
        assert len(result["new_information"]) == 1


class TestDeduplication:
    """Facts with same (actor, target) within a fact_type are deduplicated."""

    def test_identical_actor_target_deduplicates_to_one(self):
        facts = [
            {"fact_type": "relationship_changes", "actor": "Alice", "target": "Bob", "content": "first"},
            {"fact_type": "relationship_changes", "actor": "Alice", "target": "Bob", "content": "second"},
        ]
        result = aggregate_facts(facts)
        assert len(result["relationship_changes"]) == 1

    def test_latest_fact_is_kept(self):
        """When deduplicating, the last fact in the list (latest scene) wins."""
        facts = [
            {"fact_type": "relationship_changes", "actor": "Alice", "target": "Bob", "content": "early content"},
            {"fact_type": "relationship_changes", "actor": "Alice", "target": "Bob", "content": "latest content"},
        ]
        result = aggregate_facts(facts)
        assert result["relationship_changes"][0]["content"] == "latest content"

    def test_different_targets_are_not_deduplicated(self):
        facts = [
            {"fact_type": "relationship_changes", "actor": "Alice", "target": "Bob", "content": "c1"},
            {"fact_type": "relationship_changes", "actor": "Alice", "target": "Carol", "content": "c2"},
        ]
        result = aggregate_facts(facts)
        assert len(result["relationship_changes"]) == 2

    def test_different_actors_are_not_deduplicated(self):
        facts = [
            {"fact_type": "world_changes", "actor": "north city", "target": "", "content": "c1"},
            {"fact_type": "world_changes", "actor": "south city", "target": "", "content": "c2"},
        ]
        result = aggregate_facts(facts)
        assert len(result["world_changes"]) == 2

    def test_deduplication_is_per_fact_type(self):
        """Same actor+target in different fact_types are NOT merged."""
        facts = [
            {"fact_type": "relationship_changes", "actor": "A", "target": "B", "content": "rel"},
            {"fact_type": "world_changes", "actor": "A", "target": "B", "content": "world"},
        ]
        result = aggregate_facts(facts)
        assert len(result["relationship_changes"]) == 1
        assert len(result["world_changes"]) == 1

    def test_three_updates_keeps_only_last(self):
        facts = [
            {"fact_type": "relationship_changes", "actor": "A", "target": "B", "content": "v1"},
            {"fact_type": "relationship_changes", "actor": "A", "target": "B", "content": "v2"},
            {"fact_type": "relationship_changes", "actor": "A", "target": "B", "content": "v3"},
        ]
        result = aggregate_facts(facts)
        assert len(result["relationship_changes"]) == 1
        assert result["relationship_changes"][0]["content"] == "v3"

    def test_none_actor_and_target_treated_as_empty_string(self):
        """None actor/target is normalized to empty string for deduplication key."""
        facts = [
            {"fact_type": "new_information", "actor": None, "target": None, "content": "first"},
            {"fact_type": "new_information", "actor": None, "target": None, "content": "second"},
        ]
        result = aggregate_facts(facts)
        assert len(result["new_information"]) == 1
        assert result["new_information"][0]["content"] == "second"


class TestConflictDetection:
    """Same actor+target with different content (content conflicts) — latest wins."""

    def test_conflicting_relationship_status_keeps_latest(self):
        """Two scenes describe Alice→Bob differently; the latter scene's fact wins."""
        facts = [
            {
                "fact_type": "relationship_changes",
                "actor": "Alice",
                "target": "Bob",
                "content": "Alice and Bob are allies",
                "scene_order": 1,
            },
            {
                "fact_type": "relationship_changes",
                "actor": "Alice",
                "target": "Bob",
                "content": "Alice betrayed Bob",
                "scene_order": 3,
            },
        ]
        result = aggregate_facts(facts)
        surviving = result["relationship_changes"]
        assert len(surviving) == 1
        assert surviving[0]["content"] == "Alice betrayed Bob"
        assert surviving[0]["scene_order"] == 3

    def test_conflicting_world_fact_keeps_latest(self):
        facts = [
            {"fact_type": "world_changes", "actor": "the_kingdom", "target": "", "content": "at peace"},
            {"fact_type": "world_changes", "actor": "the_kingdom", "target": "", "content": "at war"},
        ]
        result = aggregate_facts(facts)
        assert result["world_changes"][0]["content"] == "at war"

    def test_conflicting_info_preserves_all_other_fields(self):
        """All fields of the winning fact are preserved."""
        facts = [
            {
                "fact_type": "new_information",
                "actor": "Bob",
                "target": "",
                "content": "Bob is a merchant",
                "confidence": 0.5,
                "source_scene": "scene-1",
            },
            {
                "fact_type": "new_information",
                "actor": "Bob",
                "target": "",
                "content": "Bob is an assassin",
                "confidence": 0.9,
                "source_scene": "scene-5",
            },
        ]
        result = aggregate_facts(facts)
        winner = result["new_information"][0]
        assert winner["content"] == "Bob is an assassin"
        assert winner["confidence"] == 0.9
        assert winner["source_scene"] == "scene-5"

    def test_no_conflict_when_actor_target_differ(self):
        """Different actor+target pairs are never considered conflicting."""
        facts = [
            {"fact_type": "relationship_changes", "actor": "Alice", "target": "Bob", "content": "friends"},
            {"fact_type": "relationship_changes", "actor": "Alice", "target": "Carol", "content": "rivals"},
            {"fact_type": "relationship_changes", "actor": "Bob", "target": "Carol", "content": "strangers"},
        ]
        result = aggregate_facts(facts)
        assert len(result["relationship_changes"]) == 3


class TestEdgeCases:
    """Edge cases and return structure invariants."""

    def test_empty_input_returns_all_four_keys(self):
        result = aggregate_facts([])
        assert set(result.keys()) == set(FACT_TYPES)
        for ft in FACT_TYPES:
            assert result[ft] == []

    def test_result_always_has_all_four_keys(self):
        facts = [{"fact_type": "relationship_changes", "actor": "X", "target": "Y", "content": "c"}]
        result = aggregate_facts(facts)
        assert set(result.keys()) == set(FACT_TYPES)

    def test_fact_types_constant_contains_four_entries(self):
        assert len(FACT_TYPES) == 4
        assert "relationship_changes" in FACT_TYPES
        assert "world_changes" in FACT_TYPES
        assert "timeline_changes" in FACT_TYPES
        assert "new_information" in FACT_TYPES

    def test_order_within_bucket_matches_insertion_order(self):
        """Facts with distinct keys preserve insertion order."""
        facts = [
            {"fact_type": "relationship_changes", "actor": "A", "target": "B", "content": "1"},
            {"fact_type": "relationship_changes", "actor": "C", "target": "D", "content": "2"},
            {"fact_type": "relationship_changes", "actor": "E", "target": "F", "content": "3"},
        ]
        result = aggregate_facts(facts)
        contents = [f["content"] for f in result["relationship_changes"]]
        assert contents == ["1", "2", "3"]

    def test_large_batch_deduplication(self):
        """100 updates for the same pair → only the last survives."""
        facts = [
            {"fact_type": "timeline_changes", "actor": "clock", "target": "", "content": f"tick-{i}"}
            for i in range(100)
        ]
        result = aggregate_facts(facts)
        assert len(result["timeline_changes"]) == 1
        assert result["timeline_changes"][0]["content"] == "tick-99"

    def test_mixed_none_and_empty_string_actors_treated_equally(self):
        """None and missing actor both normalize to '' — they share a dedup key."""
        facts = [
            {"fact_type": "new_information", "actor": None, "target": "", "content": "first"},
            {"fact_type": "new_information", "target": "", "content": "second"},  # actor key absent
        ]
        result = aggregate_facts(facts)
        assert len(result["new_information"]) == 1
        assert result["new_information"][0]["content"] == "second"
