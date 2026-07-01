from dataclasses import dataclass, field
from pydantic import BaseModel, Field


@dataclass
class Server:
    id: int
    name: str
    host: str
    port: int
    status: str = "unknown"
    tags: list[str] = field(default_factory=list)
    health_path: str = "/health"

    def base_url(self) -> str:
        protocol = "https" if self.port == 443 else "http"
        return f"{protocol}://{self.host}:{self.port}"


class ServerIn(BaseModel):
    name: str
    host: str
    port: int = Field(default=8080, ge=1, le=65535)
    tags: list[str] = []
    health_path: str = "/health"


class ServerOut(BaseModel):
    id: int
    name: str
    host: str
    port: int
    status: str
    tags: list[str] = []
    health_path: str = "/health"

    model_config = {"from_attributes": True}
