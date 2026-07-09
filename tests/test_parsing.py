"""Tests for skills parsing utility."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from skills.parsing import parse_json_from_markdown, parse_list_from_response


class TestParsing:
    def test_parse_json_direct(self):
        result = parse_json_from_markdown('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_list(self):
        result = parse_json_from_markdown('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_parse_json_with_fence(self):
        result = parse_json_from_markdown("text\n```json\n{\"key\": \"value\"}\n```\nmore")
        assert result == {"key": "value"}

    def test_parse_list_from_response_key(self):
        result = parse_list_from_response(
            '{"patches": [{"op": "replace", "block_index": 0}]}',
            "patches"
        )
        assert len(result) == 1
        assert result[0]["op"] == "replace"

    def test_parse_list_from_response_direct_list(self):
        result = parse_list_from_response('[{"a": 1}]')
        assert len(result) == 1

    def test_parse_list_from_response_invalid(self):
        result = parse_list_from_response("not json", "patches")
        assert result == []