from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Integer

class Audiobook(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    author: str
    description: str
    file_data: bytes  # сам аудіофайл
    file_name: str    # ім'я файлу
    file_content_type: str  # тип файлу (наприклад audio/mpeg)
    image_data: bytes | None = None  # сама картинка
    image_name: str | None = None  # назва картинки
    image_content_type: str | None = None  # тип картинки (наприклад png/jpg)
    user: str | None = None # ім'я користувача, який додав книгу

class User(SQLModel, table=True):
    id: int | None = Field(primary_key=True, index=True)
    username: str | None = Field(unique=True, index=True)
    hashed_password: str
