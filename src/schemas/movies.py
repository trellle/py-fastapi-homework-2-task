# Write your code here
import pycountry
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import timedelta, date as dateType
from typing import List, Optional
from src.database.models import MovieStatusEnum


class MovieDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: dateType
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movies: List[MovieDetailSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: Optional[str] = None


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class DateValidationMixin:
    @field_validator("date")
    def validate_date_not_too_far(cls, value: dateType):
        today = dateType.today()
        max_allowed = today + timedelta(days=365)
        if value > max_allowed:
            raise ValueError("The date must not be more than one year in the future.")
        return value


class MovieCreateRequestSchema(BaseModel, DateValidationMixin):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(max_length=255)
    date: dateType
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("country")
    def validate_country(cls, value: str):
        if not pycountry.countries.get(alpha_3=value.upper()):
            raise ValueError(f"Invalid country code: {value}")
        return value.upper()


class MovieCreateResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: dateType
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]


class MovieUpdateRequestSchema(BaseModel, DateValidationMixin):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    date: Optional[dateType] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
