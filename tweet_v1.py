from typing import Any, Dict, List

from pydantic import BaseModel, validator, ValidationError


class User(BaseModel):
    id: int
    name: str
    screen_name: str
    location: str
    url: str
    description: str

    @validator('description', pre=False)
    def description_replace(cls, v):
        if len(v) > 80:
            raise ValidationError('description should be less than 80 characters')
        return v.replace('\n', ' ')


class Unwound(BaseModel):
    url: str
    title: str


class Url(BaseModel):
    url: str
    unwound: Unwound


class Entities(BaseModel):
    hashtags: List
    urls: List[Url]
    user_mentions: List


class Tweet(BaseModel):
    created_at: str
    id_str: str
    text: str
    user: User
    place: Dict[str, Any]
    entities: Entities

    @validator('text', pre=False)
    def text_replace(cls, v):
        if len(v) > 140:
            raise ValidationError('text should be less than 140 characters')
        return v.replace('\n', ' ')
