"""MCP server for Document RAG: exposes search_documents, ask_rag, ingest_document as tools."""

from fastmcp import FastMCP

from . import rag_tools

mcp = FastMCP(
    name="Document RAG",
    instructions="RAG tools: search documents, ask questions, ingest text into the knowledge base.",
)


@mcp.tool()
async def search_documents(query: str) -> str:
    """Vector similarity search over the document knowledge base. Returns top matching chunks and metadata."""
    chunks = await rag_tools.search_documents_impl(query)
    if not chunks:
        return "No matching documents found."
    lines = []
    for i, c in enumerate(chunks, 1):
        text = c.get("text", "")
        source = c.get("source", "unknown")
        lines.append(f"[{i}] (source: {source})\n{text}")
    return "\n\n---\n\n".join(lines)


@mcp.tool()
async def ask_rag(question: str) -> str:
    """RAG question answering: retrieve relevant chunks and generate an answer using the LLM."""
    data = await rag_tools.ask_rag_impl(question)
    answer = data.get("answer", "")
    sources = data.get("sources", [])
    if sources:
        return f"{answer}\n\nSources: {', '.join(sources)}"
    return answer


@mcp.tool()
async def ingest_document(document: str, source: str = "mcp") -> str:
    """Add document text to the knowledge base: chunk, embed, and store in the vector store."""
    data = await rag_tools.ingest_document_impl(document, source)
    status = data.get("status", "unknown")
    inserted = data.get("chunks_inserted", 0)
    doc = data.get("document", source)
    return f"Ingestion {status}: {inserted} chunks stored for document '{doc}'."


if __name__ == "__main__":
    mcp.run()
