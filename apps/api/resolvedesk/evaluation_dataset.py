"""Versioned authored fixtures; expected labels never belong in model context."""

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

VERSION = "meridian-support-2026-11-19-v1"


class Article(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str = Field(max_length=120)
    body: str = Field(max_length=10000)
    publication: Literal["published", "archived", "conflict_only"]

    def content(self):
        return f"# {self.title}\n\n{self.body}\n"


class SupportCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    split: Literal["tuning", "held_out"]
    subject: str = Field(max_length=200)
    body: str = Field(max_length=4000)
    expected_sources: list[str]
    expected_abstention: bool
    category: str
    conflict_source_active: bool
    private_probe: bool


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    description: str
    split_policy: str
    live_sample: list[str] = Field(max_length=10)
    articles: list[Article] = Field(min_length=20, max_length=30)
    cases: list[SupportCase] = Field(min_length=40, max_length=60)

    @model_validator(mode="after")
    def consistent_labels(self):
        article_ids = {a.id for a in self.articles}
        case_ids = {c.id for c in self.cases}
        if len(article_ids) != len(self.articles) or len(case_ids) != len(self.cases):
            raise ValueError("Dataset identifiers must be unique.")
        if len(set(self.live_sample)) != len(self.live_sample):
            raise ValueError("Live sample identifiers must be unique.")
        if not set(self.live_sample) <= {c.id for c in self.cases if c.split == "held_out"}:
            raise ValueError("The bounded live sample must use held-out cases.")
        if any(not set(c.expected_sources) <= article_ids for c in self.cases):
            raise ValueError("Expected sources must identify authored articles.")
        return self


def load_dataset(version: str = VERSION):
    if version != VERSION:
        raise ValueError("This dataset version is not available.")
    raw = (Path(__file__).parent / "datasets" / f"{VERSION}.json").read_bytes()
    dataset = Dataset.model_validate_json(raw)
    if dataset.version != version:
        raise ValueError("Dataset version does not match its file.")
    return dataset, hashlib.sha256(raw).hexdigest()
