"""A minimal stand-in for the OpenAI client so tests never hit the network."""

from types import SimpleNamespace

from app.config import get_settings


def fake_vector(seed: float = 0.1) -> list[float]:
    return [seed] * get_settings().embedding_dimensions


class FakeEmbeddings:
    def __init__(self) -> None:
        self.calls: list[list[str] | str] = []

    async def create(self, model: str, input: list[str] | str) -> SimpleNamespace:
        self.calls.append(input)
        count = 1 if isinstance(input, str) else len(input)
        return SimpleNamespace(data=[SimpleNamespace(embedding=fake_vector()) for _ in range(count)])


class FakeCompletions:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls: list[list[dict[str, str]]] = []

    async def create(self, model: str, messages: list[dict[str, str]], **_: object) -> SimpleNamespace:
        self.calls.append(messages)
        message = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeOpenAI:
    def __init__(self, reply: str = "") -> None:
        self.embeddings = FakeEmbeddings()
        self.chat = SimpleNamespace(completions=FakeCompletions(reply))
