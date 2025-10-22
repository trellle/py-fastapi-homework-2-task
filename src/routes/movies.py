from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy import select, func, distinct
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import get_db, MovieModel
from src.database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from src.schemas import (
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieCreateRequestSchema,
    MovieCreateResponseSchema,
    MovieUpdateRequestSchema
)
from src.database.session_postgresql import get_postgresql_db
from src.database.utils.crud_helpers import get_or_create


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    request: Request,
    db: AsyncSession = Depends(get_postgresql_db),
    page: int = Query(1, ge=1, description="Номер сторінки"),
    per_page: int = Query(
        10, ge=1, le=20, description="Кількість фільмів на сторінку"
    )
) -> MovieListResponseSchema:
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page
    result = await db.execute(select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page))
    movies = result.scalars().all()
    if not movies or page > total_pages and total_pages != 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")
    base_url = request.url.path
    return MovieListResponseSchema(
        movies=movies,
        prev_page=f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieDetailSchema)
async def create_movie(payload: MovieCreateRequestSchema, db: AsyncSession = Depends(get_postgresql_db)) -> MovieDetailSchema:
    response = await db.execute(select(MovieModel).where((MovieModel.name == payload.name) & (MovieModel.date == payload.date)))
    if not response.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"A movie with the name '{payload.name}' and release date '{payload.date}' already exists.")
    country = await get_or_create(CountryModel, payload.country)
    languages = []
    for language_input in payload.languages:
        language = await get_or_create(LanguageModel, language_input.model_dump())
        languages.append(language)
    genres = []
    for genre_input in payload.genres:
        genre = await get_or_create(GenreModel, genre_input.model_dump())
        genres.append(genre)
    actors = []
    for actor_input in payload.actors:
        actor = await get_or_create(ActorModel, actor_input.model_dump())
        actors.append(actor)
    new_movie = MovieModel(
        name=payload.name,
        date=payload.date,
        score=payload.score,
        overview=payload.overview,
        status=payload.status,
        budget=payload.budget,
        revenue=payload.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie


@router.get("/movies/{movie_id}", response_model=MovieCreateResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_postgresql_db)):
    response = await db.execute(
        select(distinct(MovieModel))
        .where(MovieModel.id == movie_id)
        .options(joinedload(MovieModel.country))
        .options(joinedload(MovieModel.genres))
        .options(joinedload(MovieModel.actors))
        .options(joinedload(MovieModel.languages))
    )
    movie = response.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_postgresql_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_to_delete = result.scalar_one_or_none()
    if not movie_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    db.delete(movie_to_delete)
    await db.commit()
    await db.refresh(movie_to_delete)


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(movie_id: int, update_data: MovieUpdateRequestSchema, db: AsyncSession = Depends(get_postgresql_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_to_update = result.scalar_one_or_none()
    if not movie_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    if update_data.name:
        movie_to_update.name = update_data.name
    if update_data.date:
        movie_to_update.date = update_data.date
    if update_data.score:
        movie_to_update.score = update_data.score
    if update_data.overview:
        movie_to_update.overview = update_data.overview
    if update_data.status:
        movie_to_update.status = update_data.status
    if update_data.budget:
        movie_to_update.budget = update_data.budget
    if update_data.revenue:
        movie_to_update.revenue = update_data.revenue
    await db.commit()
    await db.refresh(movie_to_update)
    return {
        "detail": "Movie updated successfully."
    }
