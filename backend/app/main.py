"""FastAPI application entrypoint with router registration and lifespan events."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.utils.logging import setup_logging, get_logger
from app.api import applications, sboms, reports, graph, portfolio, evaluation


settings = get_settings()
setup_logging(debug=settings.DEBUG)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events — startup and shutdown."""
    logger.info("Starting SBOM Risk Scorer API")
    yield
    logger.info("Shutting down SBOM Risk Scorer API")


app = FastAPI(
    title="SBOM Risk Scorer",
    description="Software Supply Chain Risk Analysis Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(
    applications.router,
    prefix=settings.API_V1_PREFIX + "/applications",
    tags=["Applications"],
)
app.include_router(
    sboms.router,
    prefix=settings.API_V1_PREFIX + "/sboms",
    tags=["SBOMs"],
)
app.include_router(
    reports.router,
    prefix=settings.API_V1_PREFIX + "/reports",
    tags=["Reports"],
)
app.include_router(
    graph.router,
    prefix=settings.API_V1_PREFIX + "/graph",
    tags=["Graph"],
)
app.include_router(
    portfolio.router,
    prefix=settings.API_V1_PREFIX + "/portfolio",
    tags=["Portfolio"],
)
app.include_router(
    evaluation.router,
    prefix=settings.API_V1_PREFIX + "/evaluation",
    tags=["Evaluation"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "sbom-risk-scorer"}
