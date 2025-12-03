import re
from pathlib import Path
from config import MINIF2F_LEAN_SRC

def load_minif2f_problem_ids():
    """
    Returns a set of true MiniF2F problem identifiers extracted from
    minif2f_import.lean. This filters out helper lemmas and other
    non-problem declarations.
    """
    imp_path = MINIF2F_LEAN_SRC / "minif2f_import.lean"
    text = imp_path.read_text()

    # Find all words (identifiers)
    candidates = set(re.findall(r'\b([A-Za-z0-9_]+)\b', text))

    IGNORE = {
        "import", "open", "open_locale", "namespace", "end",
        "theorem", "lemma", "def"
    }

    # Filter
    return {c for c in candidates if c not in IGNORE}
