"""Experimental local SLM components.

PyTorch is optional. Import the concrete model or trainer only after installing
Reflection AI with the ``slm`` extra.
"""

from reflection_ai.slm.config import GenerationConfig, SLMConfig
from reflection_ai.slm.tokenizer import ByteTokenizer

__all__ = ["ByteTokenizer", "GenerationConfig", "SLMConfig"]
