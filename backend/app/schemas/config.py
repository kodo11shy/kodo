from pydantic import BaseModel


class ConfigUpdateRequest(BaseModel):
    values: dict[str, str]

