"""spaCy NER model install helper for Graph RAG (step3 graph phase)."""
from __future__ import annotations

import logging
import sys

import spacy
import spacy.util

logger = logging.getLogger(__name__)

DEFAULT_SPACY_NER_MODEL = "xx_ent_wiki_sm"


def _spacy_download(model: str) -> None:
    # (en) Delegate to spaCy CLI — same as `python -m spacy download`.
    # (kr) spaCy CLI 에 위임 — `python -m spacy download` 과 동일.
    from spacy.cli import download

    download(model)


def ensure_spacy_ner_model(model: str = DEFAULT_SPACY_NER_MODEL) -> None:
    """Install the spaCy NER model if missing (idempotent)."""
    if spacy.util.is_package(model):
        logger.info("spaCy NER model already installed: %s", model)
        return

    logger.info(
        "spaCy NER model %s not found — downloading (~11MB, one-time). "
        "Graph RAG needs this; step3 runs this preflight automatically.",
        model,
    )
    _spacy_download(model)

    if not spacy.util.is_package(model):
        raise RuntimeError(
            f"spaCy NER model {model!r} download finished but is still not importable. "
            "Try manually: python -m spacy download xx_ent_wiki_sm"
        )
    logger.info("spaCy NER model ready: %s", model)


def load_spacy_ner_model(model: str = DEFAULT_SPACY_NER_MODEL):
    """Return a loaded spaCy Language pipeline, downloading the model if needed."""
    ensure_spacy_ner_model(model)
    return spacy.load(model)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        ensure_spacy_ner_model()
    except Exception as exc:
        print(
            f"spaCy NER preflight failed: {exc}\n"
            f"  pip install spacy\n"
            f"  python -m infrastructure.ingestion.spacy_model",
            file=sys.stderr,
        )
        return 1
    print(f"spaCy NER model ready: {DEFAULT_SPACY_NER_MODEL}", flush=True)
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main())
