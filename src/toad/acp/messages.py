from dataclasses import dataclass

from textual.message import Message


class ACPAgentMessage(Message):
    pass


@dataclass
class ACPThinking(ACPAgentMessage):
    type: str
    text: str


@dataclass
class ACPUpdate(ACPAgentMessage):
    type: str
    text: str
