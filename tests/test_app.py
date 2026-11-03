import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import app  # noqa: E402


class FakeTable:
    def __init__(self):
        self.items = []
        self.query_result = {"Items": []}

    def put_item(self, Item):
        self.items.append(Item)

    def query(self, **_kwargs):
        return self.query_result


class ChatApiTests(unittest.TestCase):
    def setUp(self):
        self.table = FakeTable()
        app._table = self.table

    def test_creates_message(self):
        result = app.create_message({"body": '{"user":"Ada","content":"Hello"}'}, None)
        payload = json.loads(result["body"])
        self.assertEqual(result["statusCode"], 201)
        self.assertEqual(payload["message"]["chatId"], "general")
        self.assertEqual(self.table.items[0]["content"], "Hello")

    def test_rejects_valid_json_that_is_not_an_object(self):
        result = app.create_message({"body": "[]"}, None)
        self.assertEqual(result["statusCode"], 400)

    def test_returns_chronological_page_and_cursor(self):
        self.table.query_result = {
            "Items": [
                {"id": "2", "chatId": "general", "timestamp": "2026-01-02Z", "user": "Ada", "content": "new"},
                {"id": "1", "chatId": "general", "timestamp": "2026-01-01Z", "user": "Ada", "content": "old"},
            ],
            "LastEvaluatedKey": {"chatId": "general", "createdAt": "2026-01-01Z#x"},
        }
        result = app.list_messages({"queryStringParameters": {"limit": "2"}}, None)
        payload = json.loads(result["body"])
        self.assertEqual([item["id"] for item in payload["messages"]], ["1", "2"])
        self.assertIn("cursor", payload)

    def test_rejects_cursor_for_another_chat(self):
        cursor = app._encode_cursor({"chatId": "private", "createdAt": "key"})
        result = app.list_messages({"queryStringParameters": {"cursor": cursor}}, None)
        self.assertEqual(result["statusCode"], 400)
