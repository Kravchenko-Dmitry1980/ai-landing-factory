from pathlib import Path

from app.schemas.landing_contract import LandingContract

TEMPLATES_DIR = Path(__file__).parent / "templates"


class PromptEngine:
    """
    Loads versioned prompts and builds LLM-ready messages from LandingContract.
    MVP: file-based templates only; no API calls.
    """

    def __init__(self, templates_dir: Path | None = None) -> None:
        self._dir = templates_dir or TEMPLATES_DIR

    def load_template(self, name: str) -> str:
        path = self._dir / name
        if not path.exists():
            raise FileNotFoundError(f"Prompt template not found: {path}")
        return path.read_text(encoding="utf-8")

    def build_generation_prompt(self, contract: LandingContract) -> str:
        template = self.load_template("landing_generation.txt")
        blocks_text = "\n\n".join(
            f"## {b.title}\n{b.content}\n"
            + ("\n".join(f"- {x}" for x in b.bullets) if b.bullets else "")
            for b in contract.blocks
        )
        return template.format(
            client=contract.client or "N/A",
            style=contract.style.value,
            goals=", ".join(contract.goals) or "N/A",
            blocks=blocks_text,
        )
