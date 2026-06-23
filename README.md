# AI Software Engineer Agent

An autonomous AI system that analyzes, understands, and reasons about software repositories using static analysis, dependency graphs, semantic search, Retrieval-Augmented Generation (RAG), and auto-generated architecture diagrams.

---

## Progress

- ✅ Phase 1: Repository Ingestion & Tech Detection
- ✅ Phase 2: AST Parsing & Knowledge Cache
- ✅ Phase 3: Dependency Graph & Architecture Analysis
- ✅ Phase 4: Semantic Search
- ✅ Phase 5: RAG-powered Repository Assistant
- ✅ Phase 6: Architecture Diagram Generation
- ⏳ Phase 7: Bug Detection & Code Smell Analysis
- ⏳ Phase 8: Refactoring & Implementation Planning

---

## Current Capabilities

### Repository Analysis
- Clone any public GitHub repository
- Scan and map full file tree structure
- Detect programming languages, frameworks, and build tools
- Identify entry points and configuration files
- Generate structured repository manifests (JSON)

### Code Intelligence
- Full AST parsing of Python source files
- Extract classes, functions, methods, imports, and inheritance
- Cyclomatic complexity computation per function
- Docstring extraction and annotation analysis
- SQLite-backed knowledge cache (parse once, query forever)
- AST-aware code chunking for downstream AI tasks

### Architecture & Graph Intelligence
- Directed dependency graph construction with NetworkX
- PageRank-based module importance scoring
- Betweenness centrality for bridge module detection
- Circular dependency detection via strongly connected components
- God module detection (high function count + high complexity)
- Interactive dependency visualization with PyVis (HTML)
- Static dependency graph rendering with Matplotlib

### Semantic Search
- AST-aware code chunking (function, method, class, module level)
- Sentence Transformer embeddings (all-MiniLM-L6-v2)
- FAISS vector indexing for fast similarity search
- Natural language code search across entire repositories
- Cosine similarity ranking of results
- Persistent index saved to disk

### AI Repository Assistant (RAG)
- Retrieval-Augmented Generation pipeline over any codebase
- Context-aware question answering grounded in real source code
- Token-budget-aware context builder (no hallucination overflow)
- Source citations with every answer (module + line number)
- Repository architectural summarization
- Multi-turn conversation with memory

### Architecture Diagram Generation
- Module dependency diagrams (Graphviz, color-coded by complexity)
- Class inheritance hierarchy diagrams (Matplotlib)
- Layered architecture diagrams (entry / core / data / utilities / tests)
- Mermaid.js diagram generation for GitHub README embedding
- All diagrams auto-generated directly from source code — never outdated

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| GitPython | Repository cloning |
| AST (stdlib) | Source code parsing |
| SQLite | Knowledge cache |
| NetworkX | Dependency graph construction & analysis |
| PyVis | Interactive HTML graph visualization |
| FAISS | Vector similarity search |
| Sentence Transformers | Code embeddings |
| Google Gemini API | LLM for RAG generation |
| Graphviz | Architecture diagram rendering |
| Matplotlib | Static graph and hierarchy diagrams |
| NumPy | Embedding matrix operations |

---

## Architecture

```
GitHub URL
    ↓
[Phase 1] Ingestion Layer
    Clone → Scan → Detect Tech → Manifest JSON
    ↓
[Phase 2] AST Parser
    Parse Python → Extract entities → SQLite cache
    ↓
[Phase 3] Graph Builder
    Dependency graph → PageRank → Centrality → Circular deps
    ↓
[Phase 4] Semantic Search
    Chunk code → Embed → FAISS index
    ↓
[Phase 5] RAG Assistant
    Retrieve chunks → Build context → Gemini → Cited answer
    ↓
[Phase 6] Diagram Generator
    Graphviz → Matplotlib → Mermaid.js → Architecture visuals
```

---

## Roadmap

### Phase 7 — Bug Detection & Code Smell Analysis
- Cyclomatic complexity thresholds and warnings
- God class and God module detection
- Dead code detection (unreferenced functions)
- Long method and large class detection
- N+1 query pattern detection
- AST heuristics for common anti-patterns
- Pylint integration for additional rule-based checks
- Structured smell report with severity rankings

### Phase 8 — Refactoring & Implementation Planning
- AI-generated refactoring suggestions per detected smell
- Feature implementation planning from natural language spec
- Impact analysis: "what breaks if I change this module?"
- Ranked improvement recommendations with effort estimates
- Integration of graph metrics + LLM reasoning for prioritization

---

## Target Scale

Designed to handle repositories with **50,000+ lines of code** across hundreds of files. All expensive operations (AST parsing, embedding) are cached and never re-computed on repeat runs.

---

## Future: Production Deployment

The agent is architected for straightforward productionization:

| Component | Prototype | Production |
|---|---|---|
| Storage | SQLite | PostgreSQL |
| Vector DB | FAISS (local) | Pinecone / Weaviate |
| LLM | Gemini free tier | GPT-4 / Claude API |
| Embedding model | all-MiniLM-L6-v2 | CodeBERT / codet5p |
| Deployment | Google Colab | FastAPI on Railway / Render |
