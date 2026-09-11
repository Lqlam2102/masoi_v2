from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class JoinMsg(BaseModel):
    type: Literal["join"]
    room: str | None = None
    name: str = "Người chơi"
    token: str | None = None


class ConfigMsg(BaseModel):
    type: Literal["config"]
    disabled_roles: list[str] = Field(default_factory=list)
    timers: dict[str, int] = Field(default_factory=dict)


class StartMsg(BaseModel):
    type: Literal["start"]


class ActionMsg(BaseModel):
    type: Literal["action"]
    targets: list[str] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict)


class VoteMsg(BaseModel):
    type: Literal["vote"]
    target: str | None = None


ClientMsg = JoinMsg | ConfigMsg | StartMsg | ActionMsg | VoteMsg

_BY_TYPE: dict[str, type[BaseModel]] = {
    "join": JoinMsg,
    "config": ConfigMsg,
    "start": StartMsg,
    "action": ActionMsg,
    "vote": VoteMsg,
}


def parse_client_msg(raw: dict) -> ClientMsg:
    model = _BY_TYPE.get(raw.get("type", ""))
    if model is None:
        raise ValueError(f"Loại message không hợp lệ: {raw.get('type')!r}")
    return model.model_validate(raw)
