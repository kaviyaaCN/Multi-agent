"""
agents/code_agent.py
====================
Code Generator Agent
====================
Generates modular, commented, production-quality Python code for the
selected academic project topic. Code is structured with clear sections:
imports, constants, helper functions, main class, and entry point.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from utils.llm_client import get_llm_client
from utils.helpers import clean_llm_output
from utils.logger import logger


@dataclass
class GeneratedCode:
    """Container for generated project code."""
    topic: str
    language: str = "Python"
    code: str = ""
    explanation: str = ""
    file_structure: dict[str, str] = field(default_factory=dict)
    run_instructions: str = ""

    def main_file(self) -> str:
        """Return the primary code file content."""
        return self.file_structure.get("main.py", self.code)


_SYSTEM_PROMPT = """You are a senior Python software engineer and AI/ML expert.
Write production-quality Python code that is:
- Modular: split into meaningful classes and functions
- Documented: every function/class has a docstring
- Commented: inline comments explain non-obvious logic
- Error-handled: use try/except where appropriate
- Complete: no TODO stubs — every function is fully implemented
- Realistic: use real libraries (numpy, pandas, sklearn, torch/tensorflow)

Never use placeholder comments like "# implement here" or "pass"."""

_CODE_TEMPLATE = """Write complete, working Python code for the following academic project:

Project Title: {topic}
Domain: {domain}
Technologies: {technologies}
Difficulty: {difficulty}

Requirements:
1. Full implementation — not a skeleton
2. Uses real ML/AI libraries where appropriate
3. Includes sample synthetic data generation so it runs without external datasets
4. Modular structure: multiple classes/functions
5. Main execution block shows a realistic demo run
6. All imports at the top

Return ONLY the Python code (no markdown fences, no prose before or after).
Start with a module docstring describing the project."""

_EXPLANATION_TEMPLATE = """Provide a technical explanation for this Python project code:

Project: {topic}
Domain: {domain}

Write 300-400 words covering:
1. High-level architecture / design pattern used
2. Key algorithms or ML techniques implemented
3. How to extend or modify the code
4. Expected output description

Write in clear, academic prose suitable for a project report."""

_FILES_TEMPLATE = """For a project titled "{topic}" using {technologies}, 
list the recommended Python files and their purpose in this JSON format:
{{
  "main.py": "Main execution script and demo",
  "model.py": "Core ML model definition",
  ...
}}
Return ONLY valid JSON."""


class CodeGeneratorAgent:
    """
    Agent that generates complete, executable Python code for a project.

    Produces:
    - Main implementation code
    - Technical explanation
    - Suggested file structure
    - Run instructions
    """

    def __init__(self, embedding_engine=None) -> None:
        self._llm = get_llm_client()
        self._engine = embedding_engine
        logger.info("CodeGeneratorAgent initialised")

    def generate(
        self,
        topic: str,
        domain: str,
        difficulty: str = "Intermediate",
        technologies: list[str] | None = None,
    ) -> GeneratedCode:
        """
        Generate full project code and explanation.

        Args:
            topic: Project title.
            domain: Technical domain.
            difficulty: Complexity level.
            technologies: List of libraries/frameworks to use.

        Returns:
            GeneratedCode instance with all fields populated.
        """
        technologies = technologies or ["Python", "scikit-learn", "numpy", "pandas", "matplotlib"]
        tech_str = ", ".join(technologies)

        logger.info("CodeAgent.generate: topic=%s", topic)

        args = dict(topic=topic, domain=domain, difficulty=difficulty, technologies=tech_str)

        # ── Generate main code ─────────────────────────────────────────────────
        code_prompt = _CODE_TEMPLATE.format(**args)
        raw_code = self._llm.generate(
            prompt=code_prompt,
            system_instruction=_SYSTEM_PROMPT,
            temperature=0.4,   # Lower temp = more deterministic code
            max_tokens=4096,
        )
        main_code = clean_llm_output(raw_code)

        # ── Generate explanation ───────────────────────────────────────────────
        exp_prompt = _EXPLANATION_TEMPLATE.format(**args)
        explanation = clean_llm_output(
            self._llm.generate(
                prompt=exp_prompt,
                system_instruction=_SYSTEM_PROMPT,
                temperature=0.6,
                max_tokens=800,
            )
        )

        # ── Generate file structure ────────────────────────────────────────────
        file_struct = self._generate_file_structure(topic, tech_str)

        # ── Run instructions ───────────────────────────────────────────────────
        run_instructions = self._build_run_instructions(technologies)

        result = GeneratedCode(
            topic=topic,
            code=main_code,
            explanation=explanation,
            file_structure={"main.py": main_code, **file_struct},
            run_instructions=run_instructions,
        )

        logger.info(
            "CodeAgent complete: code=%d chars, explanation=%d chars",
            len(main_code), len(explanation),
        )
        return result

    def _generate_file_structure(self, topic: str, tech_str: str) -> dict[str, str]:
        """Ask LLM for a recommended file structure and parse the JSON."""
        from utils.helpers import extract_json_from_text
        prompt = _FILES_TEMPLATE.format(topic=topic, technologies=tech_str)
        try:
            raw = self._llm.generate(prompt=prompt, temperature=0.3, max_tokens=400)
            data = extract_json_from_text(raw)
            if isinstance(data, dict):
                return data
        except Exception as exc:
            logger.warning("File structure generation failed: %s", exc)
        # Fallback
        return {
            "main.py": "Main script",
            "model.py": "ML model",
            "utils.py": "Utilities",
            "requirements.txt": "Dependencies",
        }

    def _build_run_instructions(self, technologies: list[str]) -> str:
        """Build human-readable setup and run instructions."""
        deps = " ".join(t.lower() for t in technologies
                        if t.lower() not in ("python",))
        return f"""## How to Run

### 1. Install Dependencies
```bash
pip install {deps}
```

### 2. Run the Main Script
```bash
python main.py
```

### 3. Expected Output
The script will train the model, evaluate performance metrics, and display
visualizations. Check the console output for accuracy/loss reports.
"""
