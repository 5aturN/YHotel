"""Модели проверки запросов и ответов API бронирования."""

import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("Укажите корректный адрес электронной почты.")
        return normalized


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("Укажите корректный адрес электронной почты.")
        return normalized


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class BookingCreate(BaseModel):
    room_id: int = Field(gt=0)
    check_in: date
    check_out: date
    guests: int = Field(ge=1, le=10)

    @model_validator(mode="after")
    def validate_stay(self) -> "BookingCreate":
        if self.check_out <= self.check_in:
            raise ValueError("Дата выезда должна быть позже даты заезда.")
        return self


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    category: str
    capacity: int
    base_price_kopecks: int
    status: str


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    room_id: int
    check_in: date
    check_out: date
    guests: int
    total_price_kopecks: int
    status: str
    created_at: datetime
