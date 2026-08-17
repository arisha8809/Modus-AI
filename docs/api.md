# The Brief API Documentation

The backend is a FastAPI application. When running locally, interactive OpenAPI documentation is available at `http://localhost:8000/docs` and the raw OpenAPI schema is available at `http://localhost:8000/openapi.json`.

## Health check

`GET /health`

Returns the backend health status.

## Start research

`POST /research`

Request body:

```json
{
  "question": "How has AI impacted the stock market?"
}
```

The endpoint creates a research topic and starts the background pipeline. It returns the topic identifier and initial status.

## List research runs

`GET /research`

Returns persisted research topics with their question, detected domain, status, and creation timestamp.

## Retrieve a complete dossier

`GET /research/{topic_id}`

Returns the research status, pipeline events, sub-questions, sources, findings, classifications, contradictions, conclusions, source-backed timeline events, and calculated analytics.

## Search the knowledge base

`GET /knowledge-base/search?q={query}`

Performs semantic search across findings stored in the persistent Chroma index and returns matching finding text with domain and source metadata.

## Traceability path

The central traceability path is:

```text
Conclusion → supporting Finding → Source URL
```

Contradictions link two findings from different source records, while timeline events link explicitly dated milestones back to their source record.
