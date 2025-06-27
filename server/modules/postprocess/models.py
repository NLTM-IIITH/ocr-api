from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PostprocessRequest(BaseModel):
    lexicon: list[str] | str
    vocabulary: list[str] | str
    words: list[dict]