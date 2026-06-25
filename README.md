# AI Software Engineer Agent

An autonomous AI system that analyzes, understands, and reasons 
about software repositories using static analysis, dependency graphs, 
semantic search, Retrieval-Augmented Generation (RAG), 
auto-generated architecture diagrams, and AI-powered planning.

---

## What It Does

Point it at any public GitHub repository. It will:

1. Map the entire codebase structure and detect the tech stack
2. Parse every Python file using AST and build a knowledge cache
3. Construct a dependency graph and run graph algorithms on it
4. Embed all source code into a FAISS vector index
5. Answer natural language questions about the codebase via RAG
6. Auto-generate architecture and dependency diagrams
7. Detect code smells and anti-patterns with severity rankings
8. Generate AI-powered refactoring and feature implementation plans

---

## Progress

- ✅ Phase 1: Repository Ingestion & Tech Detection
- ✅ Phase 2: AST Parsing & Knowledge Cache
- ✅ Phase 3: Dependency Graph & Architecture Analysis
- ✅ Phase 4: Semantic Search
- ✅ Phase 5: RAG-powered Repository Assistant
- ✅ Phase 6: Architecture Diagram Generation
- ✅ Phase 7: Bug Detection & Code Smell Analysis
- ✅ Phase 8: Refactoring & Implementation Planning

---

## Quick Start

1. Open the notebook in Google Colab
2. Run the bootstrap cell
3. Set your GitHub URL in the reset cell
4. Run phases 1 through 8 in order
5. No local setup. No credit card. Works on any public repo.

Add your Gemini API key via Colab Secrets (key name: `GEMINI_API_KEY`).

---

## Capabilities

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
- Docstring extraction and type annotation analysis
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
- Token-budget-aware context builder
- Source citations with every answer (module + line number)
- Repository architectural summarization
- Multi-turn conversation with memory

### Architecture Diagram Generation
- Module dependency diagrams (Graphviz, color-coded by complexity)
- Class inheritance hierarchy diagrams (Matplotlib)
- Layered architecture diagrams (entry / core / data / utilities / tests)
- Mermaid.js diagram generation for GitHub README embedding
- All diagrams generated directly from source code

### Bug Detection & Code Smell Analysis
- Cyclomatic complexity detection (McCabe threshold > 10/20)
- God class detection (method count thresholds)
- Long method detection (> 50/100 lines)
- Deep nesting detection (> 4/6 levels)
- Too many arguments detection (> 5/8 parameters)
- Large file detection (> 300/500 lines)
- Severity classification: Critical / High / Medium / Low
- Structured JSON audit report with per-file findings
- Actionable refactoring suggestions per smell

### Refactoring & Implementation Planning
- AI-generated refactoring plans per detected smell
- Priority classification (P0 / P1 / P2 / P3)
- Effort estimation (Low / Medium / High / Epic)
- Step-by-step implementation instructions
- Affected file analysis and risk identification
- Natural language feature planning
- Implementation order based on dependency analysis

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
| Google Gemini API | LLM for RAG and planning |
| Graphviz | Architecture diagram rendering |
| Matplotlib | Static graph and hierarchy diagrams |
| NumPy | Embedding matrix operations |
| Radon | Maintainability index & complexity metrics |
| Pylint | Rule-based static analysis |

---

## Architecture

GitHub URL ↓ [Phase 1] Ingestion Layer Clone → Scan → Detect Tech → Manifest JSON ↓ [Phase 2] AST Parser Parse Python → Extract entities → SQLite cache ↓ [Phase 3] Graph Builder Dependency graph → PageRank → Centrality → Circular deps ↓ [Phase 4] Semantic Search Chunk code → Embed → FAISS index ↓ [Phase 5] RAG Assistant Retrieve chunks → Build context → Gemini → Cited answer ↓ [Phase 6] Diagram Generator Graphviz → Matplotlib → Mermaid.js → Architecture visuals ↓ [Phase 7] Audit Engine 6 smell detectors → Severity ranking → JSON report ↓ [Phase 8] Planner Smell + RAG + Gemini → Refactoring & feature plans

---

## Design Decisions

**Why NetworkX over Neo4j?** At repo scale (hundreds of nodes), 
NetworkX runs in-process with zero server overhead. Neo4j is the 
right call at millions of nodes.

**Why FAISS over Pinecone?** Free, offline, in-process. 
Same architectural reasoning applies in production — swap to 
Pinecone when you need managed infrastructure.

**Why SQLite over PostgreSQL?** Zero config, file-based, 
survives notebook restarts. Schema is identical to PostgreSQL — 
one connection string change to migrate.

**Why shallow clone (depth=1)?** We do static analysis, not 
history analysis. Shallow clones are 10x faster and use 10x 
less disk. No tradeoff for our use case.

**Why AST-aware chunking?** Naive character-based chunking 
splits functions in half. AST chunking guarantees every 
embedded chunk is a complete, semantically meaningful unit.

---

## Target Scale

Designed to handle repositories with 50,000+ lines of code 
across hundreds of files. All expensive operations (AST parsing, 
embedding) are cached and never re-computed on repeat runs.

---

## Roadmap

- [ ] FastAPI backend wrapper
- [ ] React frontend
- [ ] PostgreSQL + Pinecone for production storage
- [ ] Support for JavaScript / TypeScript repositories
- [ ] GitHub Actions integration for CI smell detection
- [ ] Web deployment on Railway / Render
