import assert from 'node:assert';
import { after, before, describe, it } from 'node:test';
import { createServer } from 'node:http';
import type { Server } from 'node:http';
import supertest from 'supertest';

let mockIngestion: Server;
let mockRag: Server;
let gatewayServer: Server;
let request: ReturnType<typeof supertest>;

describe('Gateway', () => {
  before(async () => {
    mockIngestion = createServer((req, res) => {
      if (req.method === 'POST' && req.url === '/ingest') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success', chunks_inserted: 1, document: 'test.pdf' }));
      } else {
        res.writeHead(404);
        res.end();
      }
    });

    mockRag = createServer((req, res) => {
      if (req.method === 'POST' && req.url === '/ask') {
        let body = '';
        req.on('data', (chunk) => { body += chunk; });
        req.on('end', () => {
          const parsed = body ? JSON.parse(body) : {};
          const question = parsed.question ?? '';
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(
            JSON.stringify({
              question,
              answer: 'Mock answer',
              sources: ['test.pdf'],
            }),
          );
        });
      } else {
        res.writeHead(404);
        res.end();
      }
    });

    await new Promise<void>((resolve) => {
      mockIngestion.listen(0, () => {
        mockRag.listen(0, () => {
          const port1 = (mockIngestion.address() as { port: number }).port;
          const port2 = (mockRag.address() as { port: number }).port;
          process.env.INGESTION_URL = `http://127.0.0.1:${port1}`;
          process.env.RAG_URL = `http://127.0.0.1:${port2}`;
          resolve();
        });
      });
    });

    const appModule = await import('../src/app');
    const app = appModule.app;
    await new Promise<void>((resolve) => {
      gatewayServer = app.listen(0, () => resolve());
    });
    const port = (gatewayServer.address() as { port: number }).port;
    request = supertest(`http://127.0.0.1:${port}`);
  });

  after(() => {
    mockIngestion.close();
    mockRag.close();
    gatewayServer.close();
  });

  describe('GET /health', () => {
    it('returns 200 and { status: "ok" }', async () => {
      const res = await request.get('/health');
      assert.strictEqual(res.status, 200);
      assert.deepStrictEqual(res.body, { status: 'ok' });
    });
  });

  describe('POST /chat/', () => {
    it('returns 400 when question is missing', async () => {
      const res = await request.post('/chat/').send({});
      assert.strictEqual(res.status, 400);
      assert.ok(res.body.detail);
    });

    it('returns 400 when question is empty string', async () => {
      const res = await request.post('/chat/').send({ question: '   ' });
      assert.strictEqual(res.status, 400);
    });

    it('proxies to RAG and returns 200 with question, answer, sources', async () => {
      const res = await request.post('/chat/').send({ question: 'What is X?' });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.body.question, 'What is X?');
      assert.strictEqual(res.body.answer, 'Mock answer');
      assert.ok(Array.isArray(res.body.sources));
      assert.deepStrictEqual(res.body.sources, ['test.pdf']);
    });
  });

  describe('POST /ingest/', () => {
    it('returns 400 when file is missing', async () => {
      const res = await request.post('/ingest/');
      assert.strictEqual(res.status, 400);
      assert.ok(res.body.detail);
    });

    it('proxies file to ingestion and returns 200 with status, chunks_inserted, document', async () => {
      const res = await request
        .post('/ingest/')
        .attach('file', Buffer.from('mock pdf'), { filename: 'doc.pdf', contentType: 'application/pdf' });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.body.status, 'success');
      assert.strictEqual(res.body.chunks_inserted, 1);
      assert.strictEqual(res.body.document, 'test.pdf');
    });
  });
});
