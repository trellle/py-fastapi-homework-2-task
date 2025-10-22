from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid input data."},
    )

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
