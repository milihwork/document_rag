/** OpenAPI 3.0 spec for the Document RAG Gateway. */
export const openApiSpec = {
  openapi: '3.0.0',
  info: {
    title: 'Document RAG Gateway',
    version: '1.0.0',
    description: 'Single entry for frontend; proxies to Ingestion and RAG services.',
  },
  paths: {
    '/health': {
      get: {
        summary: 'Health check',
        description: 'Returns service health status.',
        responses: {
          '200': {
            description: 'OK',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  required: ['status'],
                  properties: { status: { type: 'string', example: 'ok' } },
                },
              },
            },
          },
        },
      },
    },
    '/ingest/': {
      post: {
        summary: 'Ingest PDF',
        description: 'Upload a PDF file. Proxies to the Ingestion service.',
        requestBody: {
          required: true,
          content: {
            'multipart/form-data': {
              schema: {
                type: 'object',
                required: ['file'],
                properties: {
                  file: { type: 'string', format: 'binary', description: 'PDF file to ingest' },
                },
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Ingestion succeeded',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    status: { type: 'string', example: 'success' },
                    chunks_inserted: { type: 'integer', example: 5 },
                    document: { type: 'string', example: 'document.pdf' },
                  },
                },
              },
            },
          },
          '400': { description: 'Missing or invalid file (e.g. missing multipart field "file")' },
          '502': { description: 'Upstream error while proxying to Ingestion' },
        },
      },
    },
    '/chat/': {
      post: {
        summary: 'Chat (ask a question)',
        description: 'Ask a question. Proxies to the RAG service.',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                required: ['question'],
                properties: {
                  question: { type: 'string', description: 'User question', example: 'What is in this document?' },
                },
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Answer and sources',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  required: ['question', 'answer', 'sources'],
                  properties: {
                    question: { type: 'string' },
                    answer: { type: 'string' },
                    sources: { type: 'array', items: { type: 'string' } },
                  },
                },
              },
            },
          },
          '400': { description: 'Missing or empty question' },
          '502': { description: 'Upstream error while proxying to RAG' },
        },
      },
    },
  },
} as const;
