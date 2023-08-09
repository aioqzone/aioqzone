from pydantic import BaseModel
from tylisten import BaseMessage

__all__ = ["qr_cancelled", "qr_fetched", "qr_refresh", "sms_code_input", "sms_code_required"]


class qr_fetched(BaseMessage, BaseModel):
    png: bytes
    """QR bytes (png format)"""
    times: int
    """QR **expire** times in this session"""


class qr_cancelled(BaseMessage, BaseModel):
    pass


class qr_refresh(BaseMessage, BaseModel):
    pass


class sms_code_required(BaseMessage, BaseModel):
    uin: int
    """uin"""
    phone: str
    """User's binded phone number."""
    nickname: str
    """Nickname of current login user."""


class sms_code_input(BaseMessage, BaseModel):
    uin: int
    """uin"""
    sms_code: str
    """User received SMS verify code."""
