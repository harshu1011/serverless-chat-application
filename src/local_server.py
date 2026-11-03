"""Run the API locally with in-memory storage: python3 src/local_server.py."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import app


class MemoryTable:
    def __init__(self):
        self.items = []

    def put_item(self, Item):
        self.items.append(Item)

    def query(self, *, chatId, ScanIndexForward, Limit, ExclusiveStartKey=None, **_kwargs):
        items = [item for item in self.items if item["chatId"] == chatId]
        items.sort(key=lambda item: item["createdAt"], reverse=not ScanIndexForward)
        if ExclusiveStartKey:
            items = [item for item in items if item["createdAt"] < ExclusiveStartKey["createdAt"]]
        page = items[:Limit]
        result = {"Items": page}
        if len(items) > Limit:
            last = page[-1]
            result["LastEvaluatedKey"] = {"chatId": last["chatId"], "createdAt": last["createdAt"]}
        return result


app._table = MemoryTable()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/messages":
            return self._send(404, '{"error":"Not found"}')
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._send(400, '{"error":"Invalid Content-Length"}')
        response = app.create_message({"body": self.rfile.read(size).decode("utf-8")}, None)
        self._send_lambda(response)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/messages":
            return self._send(404, '{"error":"Not found"}')
        params = {key: values[-1] for key, values in parse_qs(url.query).items()}
        self._send_lambda(app.list_messages({"queryStringParameters": params}, None))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_lambda(self, result):
        self.send_response(result["statusCode"])
        for name, value in result.get("headers", {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(result["body"].encode("utf-8"))

    def _send(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))


if __name__ == "__main__":
    print("Local chat API: http://127.0.0.1:8080")
    ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()
