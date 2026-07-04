# Serverless Chat Application

A real-time chat application built with AWS serverless technologies.

## Architecture

- AWS Lambda: Serverless compute for processing chat messages.
- Amazon API Gateway: HTTP endpoints for sending and receiving messages.
- Amazon DynamoDB: Persistent storage for chat history and user metadata.

## Features

- Real-time message delivery through API Gateway and Lambda.
- Message persistence in DynamoDB.
- Scalable serverless architecture with no servers to manage.

## Components

- `POST /messages`: Submit a new chat message.
- `GET /messages`: Retrieve recent chat messages.
- DynamoDB table for storing messages with timestamp and user info.

## Deployment

1. Define Lambda functions in AWS Lambda.
2. Configure API Gateway routes for chat endpoints.
3. Create a DynamoDB table for chat data.
4. Connect Lambda functions to API Gateway and DynamoDB.

## Usage

- Send messages via `POST /messages`.
- Read message history via `GET /messages`.
- Extend with WebSocket or polling for live updates.

## Deployment Commands

- `sam build`: Build the serverless application.
- `sam deploy`: Deploy the serverless application.
