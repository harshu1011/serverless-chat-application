"""AWS Lambda handlers for the serverless chat API."""

import base64
import binascii
import json
import os
import uuid
from datetime import datetime, timezone

try:
    import boto3
    from boto3.dynamodb.conditions import Key
except ModuleNotFoundError:  # Lets unit tests and local_server run without AWS SDK packages.
    boto3 = None
    Key = None


TABLE_NAME = os.environ.get("MESSAGES_TABLE", "MessagesTable")
_table = None


def get_table():
    """Lazily initialise DynamoDB to keep module imports fast and testable."""
    global _table
    if _table is None:
        if boto3 is None:
            raise RuntimeError("boto3 is required for DynamoDB. Install requirements.txt first.")
        _table = boto3.resource("dynamodb").Table(TABLE_NAME)
    return _table


def create_message(event, _context):
    """Handle POST /messages."""
    body, error = _parse_body(event)
    if error:
        return error

    content = body.get("content")
    user = body.get("user")
    chat_id = body.get("chatId", "general")
    if not all(isinstance(value, str) and value.strip() for value in (content, user, chat_id)):
        return _response(400, {"error": "content, user, and chatId must be non-empty strings."})

    content, user, chat_id = content.strip(), user.strip(), chat_id.strip()
    if len(content) > 4_000 or len(user) > 100 or len(chat_id) > 100:
        return _response(400, {"error": "A message field exceeds its allowed length."})

    timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    message = {
        "id": str(uuid.uuid4()),
        "chatId": chat_id,
        # The suffix preserves a unique, chronological DynamoDB sort key.
        "createdAt": f"{timestamp}#{uuid.uuid4().hex}",
        "timestamp": timestamp,
        "user": user,
        "content": content,
    }
    get_table().put_item(Item=message)
    return _response(201, {"message": _public_message(message)})


def list_messages(event, _context):
    """Handle GET /messages and return one chronological page for a chat."""
    params = event.get("queryStringParameters") or {}
    chat_id = params.get("chatId", "general")
    if not isinstance(chat_id, str) or not chat_id.strip() or len(chat_id.strip()) > 100:
        return _response(400, {"error": "chatId must be a non-empty string of at most 100 characters."})

    try:
        limit = int(params.get("limit", 50))
    except (TypeError, ValueError):
        return _response(400, {"error": "limit must be an integer between 1 and 100."})
    if not 1 <= limit <= 100:
        return _response(400, {"error": "limit must be an integer between 1 and 100."})

    cursor, cursor_error = _decode_cursor(params.get("cursor"), chat_id.strip())
    if cursor_error:
        return cursor_error

    query_args = {"ScanIndexForward": False, "Limit": limit}
    if Key is None:
        # The dependency-free local runner consumes this instead of a Key condition.
        query_args["chatId"] = chat_id.strip()
    else:
        query_args["KeyConditionExpression"] = Key("chatId").eq(chat_id.strip())
    if cursor:
        query_args["ExclusiveStartKey"] = cursor

    result = get_table().query(**query_args)
    payload = {
        "messages": [_public_message(item) for item in reversed(result.get("Items", []))],
        "count": len(result.get("Items", [])),
    }
    if result.get("LastEvaluatedKey"):
        payload["cursor"] = _encode_cursor(result["LastEvaluatedKey"])
    return _response(200, payload)


def _parse_body(event):
    raw_body = event.get("body") or "{}"
    try:
        if event.get("isBase64Encoded"):
            raw_body = base64.b64decode(raw_body, validate=True).decode("utf-8")
        body = json.loads(raw_body)
    except (UnicodeDecodeError, binascii.Error, json.JSONDecodeError):
        return None, _response(400, {"error": "Request body must be valid JSON."})
    if not isinstance(body, dict):
        return None, _response(400, {"error": "Request body must be a JSON object."})
    return body, None


def _decode_cursor(value, chat_id):
    if not value:
        return None, None
    try:
        padded = value + "=" * (-len(value) % 4)
        cursor = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        if cursor.get("chatId") != chat_id or not isinstance(cursor.get("createdAt"), str):
            raise ValueError
    except (AttributeError, ValueError, UnicodeDecodeError, binascii.Error, json.JSONDecodeError):
        return None, _response(400, {"error": "cursor is invalid for this chat."})
    return cursor, None


def _encode_cursor(key):
    encoded = json.dumps(key, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(encoded).decode("ascii").rstrip("=")


def _public_message(message):
    return {name: message[name] for name in ("id", "chatId", "timestamp", "user", "content")}


def _response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(payload),
    }
