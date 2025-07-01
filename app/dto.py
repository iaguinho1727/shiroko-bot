import typing as t
from pydantic import BaseModel
class ConversationDTO(BaseModel):
    content: str
    sender: str
    timestamp: str


class ConversationChannelDTO(BaseModel):
    conversations: t.List[ConversationDTO]
    dm: bool
    origin: str