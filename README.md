# serverless-chat-application

Serverless Chat Application: a chat-message API built with AWS Lambda for serverless compute, Amazon API Gateway for endpoints, and Amazon DynamoDB for data storage. Messages are partitioned by `chatId` and returned in chronological order.

## Endpoints

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/messages` | Store `user`, `content`, and an optional `chatId` (defaults to `general`). |
| `GET` | `/messages` | Read recent messages with optional `chatId`, `limit` (1–100), and `cursor`. |

Example request:

```sh
curl -X POST "$API_URL/messages" \
  -H 'Content-Type: application/json' \
  -d '{"user":"Ada","content":"Hello, team!","chatId":"general"}'
curl "$API_URL/messages?chatId=general&limit=50"
```

When a response has a `cursor`, pass it back as `?cursor=...` to retrieve the next older page.

## Local development

Run the dependency-free local version (it stores messages only in memory):

```sh
python3 src/local_server.py
```

In another terminal, use the `curl` commands above with `API_URL=http://127.0.0.1:8080`.

Run tests:

```sh
python3 -m unittest discover -s tests -v
```

## AWS deployment

Install the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html), configure AWS credentials, then run:

```sh
sam build
sam deploy --guided
```

Use the deployed stack's `ApiUrl` output as `API_URL`. The supplied API is intentionally public for a simple demo; add an API Gateway authorizer (such as Cognito/JWT) before storing private conversations.
