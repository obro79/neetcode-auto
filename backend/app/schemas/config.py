from pydantic import BaseModel


class PublicConfigOut(BaseModel):
    slug_aliases: dict[str, str]
    sync_only_daily_set: bool
