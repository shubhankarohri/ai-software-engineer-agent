
import google.generativeai as genai

from .context_builder import ContextBuilder


SYSTEM_PROMPT = """You are an expert software engineering assistant that analyzes source code repositories.

You will be given:
1. A question about a codebase
2. Relevant source code excerpts retrieved from that codebase

Your job:
- Answer only from the provided code
- Reference specific functions, classes, and files
- Say clearly if the context is insufficient
- Be concise but technically accurate
- Organize answers into sections when helpful

Do not invent information.
Do not reference external documentation.
"""


class RepoAssistant:

    def __init__(
        self,
        search_index,
        embedder,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        top_k: int = 8,
    ):
        self.search_index = search_index
        self.embedder = embedder
        self.context_builder = ContextBuilder()
        self.top_k = top_k

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
        )

        self.chat = self.model.start_chat(history=[])
        self.conversation_history = []

    def ask(self, question: str, verbose: bool = False) -> dict:
        query_vec = self.embedder.embed_query(question)

        results = self.search_index.search(
            query_vec,
            top_k=self.top_k,
        )

        if not results:
            return {
                "question": question,
                "answer": "No relevant code found in the index.",
                "sources": [],
                "chunks_used": 0,
            }

        context = self.context_builder.build(results)

        if verbose:
            print(f"\n📦 Retrieved {context.chunks_used} chunks:")
            for src in context.sources:
                print(f"   - {src}")

        prompt = self._build_prompt(
            question,
            context.context_text,
        )

        try:
            response = self.chat.send_message(prompt)
            answer = response.text
        except Exception as e:
            answer = f"LLM error: {e}"

        self.conversation_history.append(
            {
                "question": question,
                "answer": answer,
                "sources": context.sources,
            }
        )

        return {
            "question": question,
            "answer": answer,
            "sources": context.sources,
            "chunks_used": context.chunks_used,
        }

    def _build_prompt(
        self,
        question: str,
        context_text: str,
    ) -> str:
        return f"""Here is relevant source code from the repository.

---
{context_text}
---

Question:
{question}

Please answer only using the code shown above.
"""

    def reset_conversation(self) -> None:
        self.chat = self.model.start_chat(history=[])
        self.conversation_history = []
        print("✓ Conversation reset.")

    def summarize_repo(self, manifest: dict) -> str:
        repo_name = manifest["repository"]["name"]
        lang = manifest["tech_profile"]["primary_language"]
        frameworks = manifest["tech_profile"]["frameworks"]
        entry_points = manifest.get("entry_points", [])

        query_vec = self.embedder.embed_query(
            "main application setup initialization entry point"
        )

        results = self.search_index.search(
            query_vec,
            top_k=6,
        )

        context = self.context_builder.build(results)

        prompt = f"""Analyze this repository.

Repository: {repo_name}
Primary Language: {lang}
Frameworks: {", ".join(frameworks) if frameworks else "None detected"}
Entry Points: {", ".join(entry_points) if entry_points else "None detected"}

Relevant source code:
---
{context.context_text}
---

Provide:

1. Purpose
2. Architecture
3. Key Components
4. Entry Points
5. Notable Design Patterns
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating summary: {e}"
