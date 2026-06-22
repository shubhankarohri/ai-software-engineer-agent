# AI Software Engineer Agent

An autonomous AI system that analyzes, understands, and reasons about software repositories using static analysis, dependency graphs, semantic search, and Retrieval-Augmented Generation (RAG).

## Features

- Clone and analyze GitHub repositories
- Detect programming languages, frameworks, and project structure
- Generate repository manifests
- Parse source code into an AST knowledge base
- Store repository intelligence in SQLite
- Build dependency and inheritance graphs
- Detect circular dependencies and architectural bottlenecks
- Generate interactive repository visualizations
- Perform semantic code search using Sentence Transformers
- Build FAISS vector indexes for natural language code retrieval
- Answer repository questions using Retrieval-Augmented Generation (RAG)

---

## Progress

- ✅ Phase 1: Repository Ingestion & Tech Detection
- ✅ Phase 2: AST Parsing & Knowledge Cache
- ✅ Phase 3: Dependency Graph & Architecture Analysis
- ✅ Phase 4: Semantic Search
- ✅ Phase 5: RAG-powered Repository Assistant
- ⏳ Phase 6: Architecture Diagram Generation
- ⏳ Phase 7: Bug Detection & Code Smell Analysis
- ⏳ Phase 8: Refactoring & Implementation Planning

---

## Current Capabilities

### Repository Analysis

- Repository cloning and scanning
- Technology and framework detection
- Repository manifest generation

### Code Intelligence

- AST parsing
- Function, class, and method extraction
- Import analysis
- Cyclomatic complexity extraction
- SQLite knowledge cache
- Intelligent code chunking

### Architecture Intelligence

- Dependency graph construction
- Inheritance graph analysis
- Circular dependency detection
- God module detection
- Bridge module detection
- Interactive dependency visualization

### Semantic Search

- AST-aware code chunking
- Sentence Transformer embeddings
- FAISS vector indexing
- Natural language code search
- Semantic retrieval of functions, classes, methods, and modules
- Cosine similarity ranking

### AI Repository Assistant

- Retrieval-Augmented Generation (RAG)
- Context-aware repository question answering
- Repository summarization
- Source-grounded responses with citations
- Multi-turn conversations over an entire codebase

---

## Tech Stack

- Python
- SQLite
- NetworkX
- FAISS
- Sentence Transformers
- Google Gemini API
- PyVis
- Matplotlib
- GitPython
- NumPy

---

## Roadmap

### Phase 6 — Architecture Diagram Generation

- Auto-generate C4 architecture diagrams
- Interactive dependency graph visualization
- Module dependency visualization
- SVG diagram export
- Mermaid.js integration

### Phase 7 — Bug Detection & Code Smell Analysis

- Detect architectural anti-patterns
- Cyclomatic complexity analysis
- Dead code detection
- God class detection
- N+1 query detection
- AST heuristics + Pylint integration

### Phase 8 — Refactoring & Implementation Planning

- AI-generated refactoring suggestions
- Feature implementation planning
- Impact analysis for code changes
- Ranked improvement recommendations
