"""Runtime environment names; unrelated to factory/business configuration."""

from typing import Literal, TypeAlias

Environment: TypeAlias = Literal["development", "test", "production"]
