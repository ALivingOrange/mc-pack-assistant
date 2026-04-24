"""Pre-import test fixtures.

The customizer package (`modules.customizer.agents`) has heavy side
effects at import time: it reads a cached API key from disk, loads item
IDs and recipe JSON, and constructs a sentence-transformer model.
For unit tests we don't want any of that, so this conftest runs *before*
tests import project code and:

  * creates a scratch cache/ with a dummy .api_key and empty data files
  * stubs out `sentence_transformers.SentenceTransformer` with a no-op class
    so importing the agent module doesn't download ~200 MB of model weights
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)

# Dummy API key — only created if missing so a real dev key isn't clobbered.
API_KEY = CACHE / ".api_key"
if not API_KEY.exists():
    API_KEY.write_text("test-dummy-key\n")

# Minimal item-ID and recipe caches. Individual tests that need specific
# contents should monkeypatch VALID_ITEM_IDS / ALL_RECIPES on the module.
IDS = CACHE / "modpack_item_ids.txt"
if not IDS.exists():
    IDS.write_text("minecraft:dirt\nminecraft:stone\nminecraft:oak_planks\n")
RECIPES = CACHE / "dumped_recipes.json"
if not RECIPES.exists():
    RECIPES.write_text("[]")

# Stub sentence_transformers so agent module import doesn't hit the network
# or take tens of seconds. Keep the real module if already installed — tests
# still don't call the embedding path.
if "sentence_transformers" not in sys.modules:
    fake = types.ModuleType("sentence_transformers")

    class _FakeSentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, texts, **kwargs):
            import numpy as np

            if isinstance(texts, str):
                return np.zeros(3)
            return np.zeros((len(texts), 3))

    fake.SentenceTransformer = _FakeSentenceTransformer
    sys.modules["sentence_transformers"] = fake
