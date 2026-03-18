**Published:** [How I Built a Local-First AI Stack for Document Q&A Without OpenAI](https://dev.to/mili_hunjic_70cb2c5dd0e49/how-i-built-a-local-first-ai-stack-for-document-qa-without-openai-364) (DEV Community)

![Article Cover Image](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/obbvzdfqt8aawvwuvy3t.png)

## How I Built a Local-First AI Stack for Document Q&A Without OpenAI 📚🤖

*A multi-service monorepo with `llama.cpp`, Qdrant, Python `FastAPI` services, React, Node and MCP support for AI agents.*

*You’ve probably seen buzzwords like RAG, vector database, embeddings, MCP, and local LLMs everywhere. This article is meant to make those terms feel concrete by showing how they fit together in a real project.*

## What You’ll See in This Project 👀

- **Local-first RAG architecture**
- **Document PDF ingestion and chunking pipeline**
- **Embedding generation** using `sentence-transformers`
- **Vector search** with `Qdrant`
- **Local LLM inference** with `llama.cpp`
- **Python backend microservices** built with `FastAPI`
- **React frontend** for document upload and chat
- **Optional ML layer** for security and query analysis
- **MCP integration** so AI agents can use the system as tools

## Table of contents 🧭

* [1. Introduction](#1-introduction)
* [2. What Is a Local AI Stack](#2-what-is-a-local-ai-stack)
* [3. Why Build AI Without OpenAI](#3-why-build-ai-without-openai)
* [4. Use Cases for Local AI](#4-use-cases-for-local-ai)
* [5. Key Concepts Behind the System](#5-key-concepts-behind-the-system)
* [6. High Level Architecture](#6-high-level-architecture)
* [7. Technology Stack](#7-technology-stack)
* [8. System Components Explained](#8-system-components-explained)
* [9. Document Ingestion Pipeline](#9-document-ingestion-pipeline)
* [10. Example Document Ingestion Lifecycle](#10-example-document-ingestion-lifecycle)
* [11. Query Processing Flow](#11-query-processing-flow)
* [12. Example Request Lifecycle](#12-example-request-lifecycle)
* [13. Improving Retrieval Quality](#13-improving-retrieval-quality)
* [14. Security Considerations](#14-security-considerations)
* [15. Performance Optimization](#15-performance-optimization)
* [16. Advantages And Pros of a Local AI Stack](#16-advantages-and-pros-of-a-local-ai-stack)
* [17. Limitations And Cons and Tradeoffs](#17-limitations-and-cons-and-tradeoffs)
* [18. Future Improvements](#18-future-improvements)
* [19. Refactoring Path: LangChain, LlamaIndex, or Bedrock](#19-refactoring-path-langchain-llamaindex-or-bedrock)
* [20. Conclusion](#20-conclusion)
* [21. Demoing This Repo](#21-demoing-this-repo)
* [22. Article updates](#22-article-updates)

Most AI tutorials still follow the same recipe: call OpenAI, print the response, and label it an AI application.

That is fine for a quick prototype, but it becomes limiting fast. You inherit API costs, external latency, privacy concerns, and a system design that often relies on a single provider sitting in the middle of everything.

I wanted to build something closer to a real product: a local-first AI system that can ingest documents, search them semantically, generate grounded answers, and stay flexible enough to support both humans and AI agents.

That is what `document_rag` is. It is a local-first Retrieval-Augmented Generation (RAG) platform for uploading documents, retrieving relevant context, and answering questions with sources. By default, it runs locally without requiring OpenAI, and it is structured as a multi-service monorepo with an MCP server so tools like Cursor or Claude Desktop can also use the same platform.

You can find the full source code on GitHub at [GitHub](https://github.com/milihwork/document_rag).

In this article, I will walk through the architecture, the tech stack, the tradeoffs, and why building AI locally is worth considering in the first place.


## 1. Introduction 🌱

AI-powered applications are quickly moving from novelty to default product features. Search, support assistants, internal copilots, documentation chat, and workflow automation are all being rebuilt around language models.

The easiest way to build these systems is to rely entirely on hosted providers such as OpenAI. That works well for prototypes, but many teams eventually hit the same questions:

- How much will this cost at scale?
- Can we safely send internal documents to an external API?
- What happens if latency spikes or pricing changes?
- What if the application needs to work inside a private network?

Running AI locally is one answer to those concerns.

In this project, I built a local-first RAG system that ingests PDFs and text, chunks them, turns them into embeddings, stores them in a vector database, retrieves relevant context for a question, and then generates an answer with a local LLM. It lives in a monorepo that contains the frontend, backend services, shared modules, and an MCP server for agent access. The article shows how that stack fits together and why this architecture is useful beyond a demo.


## 2. What Is a Local AI Stack 🧱

A local AI stack is a system where the critical AI components run on infrastructure you control instead of depending entirely on an external API provider.

In practice, that usually means:

- A local or self-hosted LLM runtime
- A local embedding model
- A vector database for retrieval
- Backend services that orchestrate ingestion and question answering
- A UI or API layer for users and other tools

The biggest difference from cloud AI is where inference and data processing happen.

- In a cloud-first setup, your app sends prompts and often context to a remote provider.
- In a local-first setup, your app keeps the pipeline close to the data and only uses external providers if you intentionally enable them.

In `document_rag`, the default local stack is:

- `llama.cpp` for LLM inference
- `BAAI/bge-small-en-v1.5` for embeddings
- Qdrant for vector storage
- FastAPI services for ingestion, embedding, retrieval, RAG orchestration, and optional ML analysis
- Express Gateway as the entry point for the frontend
- React frontend for upload and chat
- MCP server so AI agents can search, ask questions, and ingest content through the same platform

From a repository-design perspective, this is also a monorepo: multiple related applications and services live in one Git repository, share documentation and infrastructure, and work together as one system.


## 3. Why Build AI Without OpenAI 💸

There is nothing wrong with OpenAI or other cloud providers. They are excellent tools. But there are solid engineering reasons to build a system that does not require them by default.

### Cost considerations

Hosted APIs are easy to start with, but repeated embedding calls, chat completions, and large context windows can become expensive. A local stack makes costs more predictable because the main expense is infrastructure and hardware, not token billing on every request.

For example, AWS Bedrock pricing depends on the model you choose and can add up quickly at scale. As one reference point, the AWS Bedrock pricing page lists Claude 3.5 Sonnet Extended Access at roughly `$6` per million input tokens and `$30` per million output tokens, with batch pricing lower than that. That may be perfectly reasonable for production workloads, but the cost becomes usage-driven very quickly once you have frequent queries, longer contexts, or multiple users.

With a local `llama.cpp` setup, the cost model is different. There is no per-token API bill for each request. Instead, you are paying for the machine, electricity, storage, and the operational overhead of running the model. If you are testing on hardware you already own, the marginal cost can feel close to zero. But if you need a stronger dedicated GPU box, the fixed monthly cost can be significant even before traffic grows.

### Data privacy and security

Many RAG systems work with internal PDFs, team docs, policies, contracts, or private knowledge bases. Keeping the pipeline local reduces exposure and makes the system easier to justify in privacy-sensitive environments.

### Latency improvements

When embeddings, search, and inference are close to the application, you remove some network overhead. Local inference is not always faster in absolute terms, but it is often more predictable.

### Vendor lock-in concerns

If the whole product depends on one hosted provider, switching later can be painful. This project avoids that by using config-driven backends. The default path is local, but optional OpenAI and other future backends fit behind stable service contracts.

### Offline and internal systems

Some tools need to run on internal networks, development laptops, or restricted environments. A local-first design makes those scenarios practical.


## 4. Use Cases for Local AI 🎯

A local AI stack is especially useful for:

- Internal document search
- Engineering or product knowledge bases
- Company documentation assistants
- Secure enterprise environments
- Teams in regulated industries that want stronger control over data flow

This repository focuses on document question answering, but the same architecture can support internal wikis, policy assistants, onboarding tools, legal document review support, and research archives.


## 5. Key Concepts Behind the System 🧠

Before looking at the architecture, it helps to define the core RAG building blocks.

### Large Language Models

LLM stands for **Large Language Model**. It is the component responsible for generating the final answer from the user question plus the retrieved context. In this project, the default runtime is `llama.cpp`, which serves a local model such as Mistral 7B in GGUF format.

### Embeddings

Embeddings convert text into vectors so semantically similar content can be matched even if the wording is different. This repo uses `BAAI/bge-small-en-v1.5` by default.

### Vector search

Vector search lets the system retrieve the most relevant document chunks for a user query. Qdrant is used as the default vector store.

### Retrieval-Augmented Generation

RAG stands for **Retrieval-Augmented Generation**. It combines document retrieval with language generation, so the model answers using relevant source material instead of relying only on its pretrained knowledge.

In practice, RAG combines retrieval and generation:

1. Turn the user question into an embedding.
2. Search the vector database for relevant chunks.
3. Pass those chunks as context to the LLM.
4. Generate an answer grounded in the retrieved content.

That grounding is what makes RAG more useful for document-based assistants than raw prompting alone.


## 6. High Level Architecture 🏗️
![High-Level Architecture Image](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/ozq2r6jn92r55en7y72e.png)

At a high level, the system is split into focused services instead of a single large app:

- Frontend for upload and chat
- Gateway for a unified API entry point
- Ingestion service for parsing and chunking documents
- Embedding service for converting text to vectors
- Retrieval service for vector storage and search
- RAG service for orchestration and answer generation
- Optional ML service for injection detection, query classification, and retrieval scoring
- MCP server so AI agents can use the same backend as tools

This layout is one reason I describe the project as a monorepo. Instead of separating everything into different repositories, the frontend, backend services, shared modules, and MCP integration are versioned together. For a system like this, it makes local development, documentation, and architecture changes easier to manage.

The main data flow looks like this:

1. A user uploads a document through the frontend.
2. The Gateway forwards the request to the Ingestion service.
3. Ingestion parses the file, splits it into chunks, and asks the Embedding service for vectors.
4. The Retrieval service stores those vectors in Qdrant.
5. Later, when the user asks a question, the RAG service embeds the query, retrieves relevant chunks, optionally reranks them, and sends grounded context to the LLM.
6. The answer comes back with sources.

Here is the high-level architecture:

![High Level diagram](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/vbikd1689ffdrw97a49t.png)
  

There is also a second access path besides the browser UI: the MCP server exposes the system to AI agents over the Model Context Protocol. That means the same platform can power both a human-facing frontend and agent workflows such as `search_documents`, `ask_rag`, and `ingest_document`.

That separation makes the system easier to reason about, replace, and extend.


## 7. Technology Stack 🧰

Here is the concrete stack used in this project.


| Layer                         | Technology                                                            |
| ----------------------------- | --------------------------------------------------------------------- |
| LLM runtime                   | `(C++ runtime) --> llama.cpp`                                         |
| Default LLM model             | `(GGUF model) --> Mistral 7B`                                         |
| Embeddings                    | `(Python / sentence-transformers) --> BAAI/bge-small-en-v1.5`         |
| Vector database               | `(Vector DB) --> Qdrant`                                              |
| API gateway                   | `(NodeJS) --> Express + TypeScript`                                   |
| Backend services              | `(Python) --> FastAPI`                                                |
| Frontend                      | `Frontend (React) --> React + Vite + TypeScript`                              |
| Optional agent interface      | `(Python) --> MCP server via FastMCP`                                 |
| Optional alternative backends | `(Config-driven) --> OpenAI, pgvector, Bedrock placeholders/backends` |


One thing I like about this setup is that it stays practical. The default stack is local-first, but the interfaces are designed so that changing a backend does not force a full rewrite of the product.


## 8. System Components Explained 🧩

### Gateway / API layer

The Gateway is the public entry point used by the frontend. It keeps the UI simple and hides the internal service boundaries.

### Embedding service

This service owns text-to-vector conversion. Other services do not care which embedding provider is behind it as long as the `/embed` contract stays stable.

### Vector database

Qdrant stores chunk vectors and powers similarity search. The Retrieval service sits in front of it so vector database details are isolated.

### LLM service

The generation layer uses `llama.cpp` by default. The RAG service talks to an abstraction, so local inference is the default but not the only possible implementation.

### Ingestion service

The Ingestion service is responsible for parsing documents, chunking text, requesting embeddings, and inserting results into the retrieval layer. The next sections go deeper into the ingestion pipeline and its request lifecycle.

### RAG orchestration service

This is the brain of the application. It handles query processing, context assembly, prompt construction, answer generation, safeguards, optional query rewriting, and optional reranking. The dedicated query-flow sections below show that process in more detail.

### Optional ML service

The ML service adds extra intelligence around prompt injection detection, query intent classification, and retrieval scoring. It is not required for the core app to work, which is a good design choice for graceful degradation.

### MCP server

The MCP server is a thin integration layer that exposes the platform as tools for AI agents such as Cursor or Claude Desktop. Instead of building a separate agent-specific backend, this repo reuses the same ingestion, retrieval, and RAG services and makes them available over MCP.

The service architecture looks like this:

![Service architecture diagram](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/911a31ibccuopmxg7jqo.png)


## 9. Document Ingestion Pipeline 📥

Ingestion is where a lot of real RAG quality is decided.

The pipeline in this repo looks like this:

1. Accept a PDF upload or raw text.
2. Parse the document into plain text.
3. Split the text into chunks.
4. Generate embeddings for those chunks.
5. Store vectors and metadata in the retrieval layer.

Here is the ingestion pipeline:

**Input**
A document or text is provided by the user through upload or via the MCP client.

**Gateway / MCP Server**
The request is received and validated by the Gateway API or the MCP server, which acts as the system entry point.

**Ingestion Service**
The request is forwarded to the Ingestion Service, responsible for preparing the document for processing and indexing.

**Parser**
The parser extracts raw text from the uploaded content (for example PDF, TXT, or other supported formats).

**Chunker**
The extracted text is split into smaller chunks to optimise embedding generation and retrieval accuracy.

**Embedding Service**
Each chunk is converted into a vector representation (embedding) using an embedding model.

**Vector Preparation**
The generated vectors represent the semantic meaning of each chunk.

**Retrieval Service**
The vectors and their associated metadata are upserted through the retrieval service.

**Vector Database**
The vectors are stored in Qdrant, where they become searchable for future semantic queries.


### Document parsing

The system supports PDF ingestion and also text ingestion, which is useful for testing, automation, and MCP-driven workflows.

### Chunking strategies

Chunking is critical because poor chunking hurts retrieval quality even if the model is strong. This project exposes chunk-size configuration and keeps chunking as a shared concern rather than scattering it across services.

### Embedding generation

Each chunk is sent to the Embedding service, which returns vector representations using the configured backend.

### Storing vectors

The Retrieval service upserts the vectors into Qdrant, making the document searchable for future queries.


## 10. Example Document Ingestion Lifecycle 🔄

To make the ingestion path as concrete as the query path, here is a simplified lifecycle of what happens when a user uploads a PDF document through the frontend.

### Document Ingestion Service Flow (with Optional ML)


| Step | Caller            | Endpoint               | Target Service    | Description                                                    |
| ---- | ----------------- | ---------------------- | ----------------- | -------------------------------------------------------------- |
| 1    | Frontend          | `/ingest/`             | Gateway           | Upload PDF or raw text document                                |
| 2    | Gateway           | `/ingest`              | Ingestion Service | Forward document to ingestion pipeline                         |
| 3    | Ingestion Service | —                      | Parser Module     | Extract text from PDF or text input                            |
| 4    | Ingestion Service | `/classify` (optional) | ML Service        | Classify document type when document classification is enabled |
| 5    | Ingestion Service | —                      | Chunker Module    | Split extracted text into smaller chunks                       |
| 6    | Ingestion Service | `/embed`               | Embedding Service | Convert text chunks into vector embeddings                     |
| 7    | Embedding Service | —                      | Embedding Model   | Generate embeddings using `sentence-transformers`              |
| 8    | Ingestion Service | `/upsert`              | Retrieval Service | Send vectors and metadata for storage                          |
| 9    | Retrieval Service | —                      | Qdrant            | Store embeddings in vector database                            |
| 10   | Ingestion Service | Response               | Gateway           | Return ingestion result                                        |
| 11   | Gateway           | JSON response          | Frontend          | Confirm document indexed successfully                          |


### User action

Upload file:

`employment_contract.pdf`

**Step 1 — Frontend uploads the document**

The React frontend sends the PDF to the Gateway as a multipart form upload.

```http
POST http://localhost:8000/ingest/
Content-Type: multipart/form-data

file = employment_contract.pdf
```

**Step 2 — Gateway forwards to the Ingestion service**

The Gateway proxies the uploaded file to the Ingestion service.

```http
POST http://localhost:8001/ingest
Content-Type: multipart/form-data

file = employment_contract.pdf
```

**Step 3 — PDF parsing and text extraction**

The Ingestion service stores the upload temporarily, extracts text from the PDF, and prepares it for chunking. If document classification is enabled, the service can also classify the document before indexing it.

**Step 4 — Chunking**

The extracted text is split into smaller chunks so the content can be embedded and retrieved effectively later.

Example chunk output:

```text
Chunk 1: This employment agreement begins on...
Chunk 2: Either party may terminate this contract by...
Chunk 3: Confidentiality obligations survive termination...
```

**Step 5 — Batch embedding**

The Ingestion service sends all chunks to the Embedding service in one batch request.

```http
POST http://localhost:8002/embed
Content-Type: application/json

{
  "texts": [
    "This employment agreement begins on...",
    "Either party may terminate this contract by...",
    "Confidentiality obligations survive termination..."
  ]
}
```

The Embedding service returns one vector per chunk.

**Step 6 — Vector upsert**

The Ingestion service packages the chunk text, source filename, and embeddings into points and sends them to the Retrieval service.

```http
POST http://localhost:8003/upsert
Content-Type: application/json

{
  "points": [
    {
      "id": "uuid-1",
      "vector": [ ... ],
      "payload": {
        "text": "This employment agreement begins on...",
        "source": "employment_contract.pdf"
      }
    }
  ]
}
```

The Retrieval service stores those points in Qdrant, making the document searchable.

**Step 7 — Ingestion result returned**

Once indexing finishes, the Ingestion service returns a success payload.

Example response:

```json
{
  "status": "success",
  "chunks_inserted": 3,
  "document": "employment_contract.pdf"
}
```

The Gateway passes that response back to the frontend, which can then confirm that the document is ready for search and question answering.

Here is the same ingestion flow shown as a sequence trace:

![Ingestion flow sequence trace Image](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/4y1ln1w2k921xt43nriv.png)

This flow is useful because it shows that ingestion is not just file upload. It is a full indexing pipeline: parsing, chunking, embedding, and vector storage. That is what makes later RAG queries possible.


## 11. Query Processing Flow 🔍

Question answering follows a similar service-oriented path:

1. The user asks a question in the frontend.
2. The Gateway forwards the question to the RAG service.
3. The RAG service validates the input with safeguards.
4. If enabled, the ML service analyses the query for prompt injection and intent classification.
5. If enabled, the query can be rewritten into a clearer search form.
6. The query is embedded.
7. The Retrieval service performs vector search in Qdrant.
8. If enabled, a reranker improves the ordering of retrieved chunks.
9. If enabled, the ML service scores retrieval quality before generation.
10. The RAG service builds a prompt with the selected context.
11. The LLM generates an answer.
12. Output safeguards validate the response before it is returned.
13. The frontend shows the answer together with sources.

The RAG query flow looks like this:

**User Input**
A user submits a question to the system.

**Gateway**
The request is received by the Gateway API, which acts as the entry point for user queries.

**RAG Service**
The request is forwarded to the RAG orchestration service, which coordinates the entire retrieval and generation pipeline.

**Input Safeguards**
The query is validated to detect unsafe or malformed inputs.

**Query Analysis (Optional)**
A machine learning service may analyse the query to determine intent, complexity, or additional metadata.

**Query Rewriting (Optional)**
The query can be rewritten to improve retrieval accuracy.

**Embedding Generation**
The processed query is converted into a vector embedding using the embedding service.

**Retrieval Service**
The retrieval service searches for relevant document chunks using the query vector.

**Vector Database Search**
The similarity search is executed in Qdrant, which stores the document embeddings.

**Context Retrieval**
The most relevant chunks are returned as context for the language model.

**Reranking (Optional)**
A reranker model may reorder the retrieved chunks to improve relevance.

**Retrieval Scoring (Optional)**
An ML service may evaluate and score the quality of the retrieved results.

**Prompt Construction**
The prompt builder assembles the final prompt using the user query and the retrieved context.

**Model Execution**
The prompt is sent to the local model runtime powered by llama.cpp.

**Output Safeguards**
The generated response is validated to ensure safety and compliance.

**Final Response**
The system returns the answer along with source references to the user.

This is a good example of why modularity matters. The user experiences one simple chat flow, but the system is actually combining retrieval, ranking, safety checks, and generation behind the scenes.


## 12. Example Request Lifecycle 🔁

To make the architecture more concrete, here is a simplified lifecycle of a real request when a user asks a question about an uploaded document. The URLs below use the default local development ports from this repository.

### Example Request Flow


| Step | Caller    | Endpoint              | Target Service    | Description                                             |
| ---- | --------- | --------------------- | ----------------- | ------------------------------------------------------- |
| 1    | Frontend  | `/chat/`              | Gateway           | Send the user question to the public API                |
| 2    | Gateway   | `/ask`                | RAG Service       | Forward the request to the RAG orchestration layer      |
| 3    | RAG       | `/analyze` (optional) | ML Service        | Check prompt injection and classify query intent        |
| 4    | RAG       | `/embed`              | Embedding Service | Generate a vector embedding for the question            |
| 5    | RAG       | `/search`             | Retrieval Service | Retrieve the most relevant chunks                       |
| 6    | Retrieval | Vector search         | Qdrant            | Run similarity search on stored embeddings              |
| 7    | RAG       | `/score` (optional)   | ML Service        | Score retrieval quality before generation               |
| 8    | RAG       | Completion call       | LLM Runtime       | Send prompt and context to the configured model backend |
| 9    | Gateway   | Response              | Frontend          | Return the final answer and sources                     |


### User question

`What does the contract say about termination conditions?`

**Step 1 — Frontend sends the request**

The React frontend sends the user question to the Gateway.

```http
POST http://localhost:8000/chat/
Content-Type: application/json

{
  "question": "What does the contract say about termination conditions?"
}
```

**Step 2 — Gateway forwards to the RAG service**

The Gateway validates the incoming request shape and forwards it to the RAG orchestration service.

```http
POST http://localhost:8004/ask
Content-Type: application/json

{
  "question": "What does the contract say about termination conditions?"
}
```

**Step 3 — Input validation and optional ML analysis**

The RAG service first runs its input safeguards. If the optional ML service is enabled, it can also analyze the query for prompt injection and classify the query intent.

```http
POST http://localhost:8005/analyze
Content-Type: application/json

{
  "query": "What does the contract say about termination conditions?"
}
```

This step is optional and the system can continue without it if the ML service is disabled or unavailable.

**Step 4 — Query embedding**

Inside the RAG service, the question is passed to the Embedding service to generate a vector representation.

```http
POST http://localhost:8002/embed
Content-Type: application/json

{
  "text": "What does the contract say about termination conditions?"
}
```

The Embedding service returns an embedding vector for the query.

**Step 5 — Vector search**

The RAG service sends the query vector to the Retrieval service, which searches Qdrant for the most relevant chunks.

```http
POST http://localhost:8003/search
Content-Type: application/json

{
  "query_vector": [ ... ],
  "top_k": 5
}
```

The Retrieval service returns the most similar chunks, including their text and source metadata.

**Step 6 — Optional reranking and retrieval scoring**

If reranking is enabled, the RAG service reorders the retrieved chunks before generation. If the ML service is enabled, it can also score the retrieval quality.

```http
POST http://localhost:8005/score
Content-Type: application/json

{
  "query": "What does the contract say about termination conditions?",
  "chunks": [
    {
      "text": "Either party may terminate the agreement with written notice...",
      "source": "employment_contract.pdf"
    }
  ]
}
```

This lets the system estimate whether the retrieved context is strong enough before asking the model to generate an answer.

**Step 7 — Prompt construction**

The RAG service builds a grounded prompt that combines the original question with the retrieved context.

Example prompt:

```text
Context:
[Chunk 1: termination clause description...]
[Chunk 2: conditions for ending the agreement...]

Question:
What does the contract say about termination conditions?

Answer using only the provided context.
```

If query rewriting, reranking, safeguards, or ML-based scoring are enabled, those steps are applied around retrieval and prompt construction before the model is called.

**Step 8 — LLM inference**

The prompt is then sent from the RAG service to the configured LLM backend. In the default local setup, that means a call to the `llama.cpp` server configured by `LLM_URL` (typically `http://localhost:8080`).

**Step 9 — Response returned**

Once the answer is generated, the RAG service returns the result together with the source references.

Example response:

```json
{
  "question": "What does the contract say about termination conditions?",
  "answer": "The contract allows termination if either party provides 30 days written notice...",
  "sources": [
    "contract_page_4_chunk_2",
    "contract_page_5_chunk_1"
  ]
}
```

Finally, the Gateway returns that response to the frontend, and the answer is displayed in the chat interface.

Here is the same request shown as a sequence trace:


![User Question Sequence trace Image](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/193hq5su6nq90kb3kryx.png)


This section is useful because it shows the system as an actual request trace, not just a conceptual diagram. It makes it easier to see how the services collaborate and how RAG works in practice.


## 13. Improving Retrieval Quality 🎯

A basic RAG demo often stops at embedding plus vector search. This project goes further.

### Chunking strategies

Chunk size is configurable because retrieval quality depends heavily on how much meaning each chunk carries.

### Top-k retrieval

The system can retrieve a broader candidate set for search and then narrow it down before generation. That is more robust than sending only the first raw matches directly to the LLM.

### Context filtering

The architecture supports filtering and validating what reaches the model, which matters both for relevance and safety.

### Query rewriting

One of the nicer features in this repo is optional query rewriting. Short or vague questions can be expanded into clearer search queries for better embedding and retrieval, while the original user wording is preserved for the final answer.

### Reranking

The project also supports optional BGE reranking. That means vector search can fetch a wider set of candidates, and then a reranker can choose the best chunks to pass into the answer prompt.

Together, these choices make the retrieval layer more realistic than a minimal tutorial project.


## 14. Security Considerations 🔐

Local AI does not automatically mean secure AI. You still need defensive layers.

This project includes several useful security-oriented ideas:

- Input safeguards to block obvious prompt injection or disallowed patterns
- Output safeguards to block sensitive or restricted responses
- Optional ML-based injection detection
- Context controls so only selected retrieved chunks are passed to generation

Prompt injection is especially important in RAG because the model is reading untrusted document content and user instructions at the same time. Even in a local system, that risk still exists.

Input validation and context filtering are therefore just as important as model quality.

The ML and safety layer in this project looks like this:

| Step | What it does | Service / Module | Endpoint / Call Type |
|-----|-----|-----|-----|
| User Query | Incoming question | Gateway → RAG | `POST /chat` (Gateway) → `POST /ask` (RAG) |
| Input Safeguards | Validate input | Safeguard module inside RAG (`backend/services/safeguard`) | In-process `validate_input(...)` |
| Query Analysis | Injection / intent analysis (optional) | ML Service | `POST /analyze` |
| Query Rewriter | Improve query text (optional) | Query Rewriter (`backend/shared/query_rewriter`) | In-process `rewrite(...)` |
| Embedding Service | Generate query vector | Embedding Service | `POST /embed` |
| Retrieval Service | Search context chunks | Retrieval Service | `POST /search` |
| Reranker | Reorder results (optional) | Reranker (`backend/shared/reranker`, BGE) | In-process `rerank(...)` |
| ML Retrieval Scoring | Score retrieved context (optional) | ML Service | `POST /score` |
| Prompt Builder | Build final prompt with context | Prompt builder (shared helpers in RAG) | In-process prompt assembly |
| Model Runtime | LLM inference | LLM backend (e.g. llama.cpp) | RAG → LLM HTTP call (`LLM_URL`) |
| Output Safeguards | Validate model response | Safeguard module inside RAG | In-process `validate_output(...)` |
| Final Response | Return answer + sources | RAG → Gateway → Client | HTTP response |


## 15. Performance Optimization ⚡

Performance in local AI is about balancing model quality, retrieval quality, and resource usage.

Some useful optimisation levers visible in this repo are:

- Caching opportunities for repeated queries or embeddings
- Embedding reuse for already-ingested chunks
- Vector DB tuning such as `TOP_K` and retrieval candidate size
- Choosing smaller or larger local models depending on hardware
- Disabling optional steps like query rewriting or ML analysis when latency matters more than quality

The nice thing about a modular design is that you can tune each part independently instead of treating the whole system as one black box.


## 16. Advantages And Pros of a Local AI Stack ✅

If you want the short version, these are the main pros of this architecture:

- Full control over document data
- More predictable operational cost
- Freedom to customise models and providers
- Flexible service boundaries
- Better fit for internal tools and private deployments
- A path to support both web users and AI agents through the same backend

The last point is worth highlighting. This repo not only exposes a frontend. It also includes an MCP server, which means AI agents can search documents, ask grounded questions, and ingest text using the same backend services.

That matters because it turns the project from a simple web app into a more reusable AI platform. The same monorepo supports browser users, backend APIs, and agent tooling without duplicating business logic.


## 17. Limitations And Cons and Tradeoffs ⚖️

A local-first approach is powerful, but it is not magic.

If you want the short version, these are the main cons:

### Hardware requirements

Running local models well still depends on available CPU, RAM, and ideally GPU support. The better the model, the more demanding the setup tends to be.

### Model quality vs cloud providers

Strong local models can be impressive, but top hosted models may still outperform them on reasoning, instruction following, or multilingual tasks depending on the setup.

### Throughput and concurrent requests

Another important limitation is serving capacity. A local model runtime such as `llama.cpp` can work very well for development, demos, and low-volume internal tools, but multiple simultaneous requests can quickly become a bottleneck.

If several users send questions at the same time, you may see:

- queued requests
- slower response times
- higher CPU or GPU contention
- reduced throughput compared to managed cloud inference

That does not make local inference a bad choice, but it does mean you should think about expected traffic. A local-first stack is often strongest for single-user workflows, small teams, internal tools, or controlled environments rather than high-concurrency public applications.

### Maintenance overhead

When you own the stack, you also own more operational work:

- Managing model files
- Tuning chunking and retrieval
- Running vector infrastructure
- Maintaining service compatibility
- Handling upgrades and troubleshooting

That is the tradeoff for greater control.


## 18. Future Improvements 🗺️

This project already implements more than a minimal RAG demo, but there is still room to grow.

Some especially valuable next steps are:

- Hybrid search that combines vector and keyword retrieval
- More advanced reranking strategies
- ML-based query rewriting improvements
- Multi-model orchestration or query routing
- Observability for latency, retrieval quality, and answer quality
- Multi-tenant document collections

Because the project already uses stable service boundaries and config-driven backends, those improvements can be added incrementally instead of requiring a full redesign.


## 19. Refactoring Path: LangChain, LlamaIndex, or Bedrock 🛣️

One advantage of this architecture is that it does not lock the project into one implementation style forever. Because the system is already separated into services with stable contracts, it can be refactored gradually to use higher-level frameworks or managed cloud providers.

### Refactoring toward LangChain

If I wanted to adopt LangChain, I would not rewrite the whole repo at once. The cleaner approach would be to replace internal orchestration inside the RAG service first:

- Use LangChain for prompt templates, retrievers, and chain composition
- Keep the existing Gateway, frontend, and ingestion APIs unchanged
- Wrap the current Embedding, Retrieval, and LLM integrations behind LangChain-compatible adapters

That would let the repo keep its current service boundaries while using LangChain as an orchestration layer instead of making LangChain the whole architecture.

### Refactoring toward LlamaIndex

LlamaIndex would make the most sense if I wanted a more framework-driven retrieval pipeline with built-in indexing, query engines, and document abstractions.

A practical path would be:

- Move retrieval orchestration logic from the custom RAG service into LlamaIndex components
- Keep Qdrant as the vector backend if desired
- Reuse the existing ingestion and document-loading flow where it still fits
- Preserve the external API contracts so the frontend and MCP tools do not need to change

In other words, LlamaIndex could replace part of the internal RAG implementation without forcing a full product rewrite.

### Refactoring toward AWS Bedrock

Bedrock is a different kind of change because it is a provider shift rather than only a framework shift.

This repo is already designed for that direction:

- Embedding backends are configurable
- LLM backends are configurable
- The docs and code structure already anticipate Bedrock-style backend implementations

That means a Bedrock migration could be done by implementing or completing:

- a Bedrock embedding backend in the Embedding service
- a Bedrock LLM backend in the RAG service
- optional AWS-specific configuration in service settings

The important part is that the public APIs would stay the same. The frontend, Gateway, ingestion flow, and MCP integration would not need to know whether the actual model provider is local `llama.cpp`, OpenAI, or Bedrock.

### Why this matters

This is exactly why I prefer a modular monorepo for projects like this. The current stack is local-first, but the architecture leaves room for a future where:

- local inference is used in development
- Bedrock or another managed provider is used in production
- LangChain or LlamaIndex is introduced only where it adds value

That flexibility makes the project more realistic from a software engineering perspective.


## 20. Conclusion 🧵

This repository demonstrates that you can build a serious AI application without making OpenAI the centre of the architecture.

The system combines local embeddings, vector search, document ingestion, retrieval orchestration, safeguards, reranking, query rewriting, optional ML analysis, MCP-based agent access, and local LLM inference into one coherent stack. It also shows an important design principle: local-first does not have to mean rigid. By keeping the interfaces stable inside a multi-service monorepo, the system stays flexible enough to support alternative backends later.

Local AI makes the most sense when you care about privacy, predictable cost, internal deployment, and architectural control. Cloud AI may still be the better fit when you need the strongest hosted models immediately, want minimal infrastructure work, or do not mind sending data to external providers.

For me, that is the biggest takeaway from building this project: the interesting part is not just calling a model. It is designing the full pipeline around retrieval quality, data ownership, extensibility, and real product constraints.


## 21. Demoing This Repo 🎬

If you want to use this article together with a live demo, the shortest path is:

```bash
make up
make llm
make frontend
```

When everything is up and running locally, it looks like this:


![Up And Running Image](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/zvvwez4rzyvzz5cjvyxz.png)

Then:

1. Open `http://localhost:5173`
2. Upload a PDF
3. Ask a question that requires document retrieval
4. Show that the answer includes sources


## 22. Article updates

This section is at the end of the article so that:

- **First-time readers** get the full narrative (sections 1–21) without interruption.
- **Returning readers** can jump here to see what changed without re-reading the whole piece.
- **Transparency:** you know the article was updated and when, so the timeline and the optional nature of new features are clear.

**Article update (March 2025)**

The repo now includes two additive changes that the main article does not yet describe in detail:

- **LangChain (optional):** LangChain was added only inside the RAG service as an internal orchestration layer. The main practical benefit is optional **multi-query retrieval**: instead of searching with only one user phrasing, the service can generate several related search queries, retrieve a broader candidate set, deduplicate results, and then optionally rerank them. This can improve recall on short, vague, or synonym-heavy questions. It also enables optional **LangSmith tracing** for better debugging and observability. Importantly, the public architecture did not change: the Gateway, Embedding service, Retrieval service, and frontend still use the same contracts. See [LangChain + LangSmith (Optional)](https://github.com/milihwork/document_rag/blob/main/docs/langchain.md).
- **Hugging Face:** The embedding layer is now explained more explicitly as using **Hugging Face sentence-transformers models** for local embeddings. If you were already using the same default model (`BAAI/bge-small-en-v1.5`), this is not a sudden retrieval-quality jump by itself. The main benefit is **clarity and flexibility**: the backend is easier to reason about, easier to document, and easier to swap to other Hugging Face models later (for example larger, smaller, or multilingual models) while keeping the same `POST /embed` service contract. See [Adding New Backends (Modular Architecture)](https://github.com/milihwork/document_rag/blob/main/docs/backends.md) and [Architecture](https://github.com/milihwork/document_rag/blob/main/docs/architecture.md).

This note is here for transparency so readers can clearly see what was added after the original article was published. The core content above (sections 1-21) is unchanged, and the architecture and request flows described in the article remain accurate. These additions are optional enhancements rather than a rewrite of the system.