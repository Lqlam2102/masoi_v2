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
    # Client gửi `roles` dạng {role_id: bật/tắt}; `disabled_roles` là dạng cũ.
    roles: dict[str, bool] = Field(default_factory=dict)
    disabled_roles: list[str] = Field(default_factory=list)
    timers: dict[str, int] = Field(default_factory=dict)
    # Cài đặt tuỳ chọn — có thể gửi bất kỳ lúc nào (kể cả sau ván)
    reveal_role_on_death: bool | None = None
    # Danh sách role đầy đủ do host tự cấu hình (flat list, len == số người chơi)
    role_list: list[str] = Field(default_factory=list)


class StartMsg(BaseModel):
    type: Literal["start"]


class ActionMsg(BaseModel):
    type: Literal["action"]
    targets: list[str] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict)


class VoteMsg(BaseModel):
    type: Literal["vote"]
    target: str | None = None


class LeaveMsg(BaseModel):
    type: Literal["leave"]


class SkipMsg(BaseModel):
    type: Literal["skip"]


class ChatMsg(BaseModel):
    type: Literal["chat"]
    text: str = ""


class AdvanceMsg(BaseModel):
    """Host chốt pha sớm, không chờ hết giờ."""

    type: Literal["advance"]


class RematchMsg(BaseModel):
    """Host mở ván mới trong cùng phòng, kéo theo người đang ngồi chờ."""

    type: Literal["rematch"]


ClientMsg = (
    JoinMsg | ConfigMsg | StartMsg | ActionMsg | VoteMsg | LeaveMsg | SkipMsg
    | ChatMsg | AdvanceMsg | RematchMsg
)

_BY_TYPE: dict[str, type[BaseModel]] = {
    "join":   JoinMsg,
    "config": ConfigMsg,
    "start":  StartMsg,
    "action": ActionMsg,
    "vote":   VoteMsg,
    "leave":  LeaveMsg,
    "skip":   SkipMsg,
    "chat":   ChatMsg,
    "advance": AdvanceMsg,
    "rematch": RematchMsg,
}


def parse_client_msg(raw: dict) -> ClientMsg:
    model = _BY_TYPE.get(raw.get("type", ""))
    if model is None:
        raise ValueError(f"Loại message không hợp lệ: {raw.get('type')!r}")
    return model.model_validate(raw)
