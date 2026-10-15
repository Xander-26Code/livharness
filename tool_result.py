from dataclasses import asdict, dataclass

@dataclass
class ToolError:
    code: str
    message: str
    retryable: bool = False


@dataclass
class ToolResult:
    tool: str
    status: str
    summary: str
    data: dict
    error: ToolError | None = None
    metadata: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)