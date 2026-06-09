from pydantic import BaseModel


class AuthVerifyOut(BaseModel):
    ok: bool
    app_name: str
