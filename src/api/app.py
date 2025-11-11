"""
FastAPI application for Claude Config Version Control System.

Provides REST API endpoints for managing snapshots, paths, and changes.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.core.config import get_settings
from src.core.database import init_database, close_database
from src.api.middleware import RequestLoggingMiddleware
from src.api.exceptions import add_exception_handlers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle events.

    Handles:
    - Database initialization on startup
    - Database cleanup on shutdown
    """
    settings = get_settings()

    # Startup: Initialize database
    logger.info("Starting Claude Config API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url}")

    try:
        await init_database(
            database_url=settings.database_url,
            echo=settings.environment == "development",
        )
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise

    yield

    # Shutdown: Close database connections
    logger.info("Shutting down Claude Config API")
    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}", exc_info=True)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    # Create FastAPI app with metadata
    app = FastAPI(
        title="Claude Config Version Control API",
        description="""
        REST API for managing Claude configuration snapshots and tracking changes.

        ## Features

        * **Snapshot Management**: Create, retrieve, and manage configuration snapshots
        * **Path Tracking**: Query and analyze configuration file paths
        * **Change Detection**: Compare snapshots and track changes over time
        * **Tag & Annotate**: Organize snapshots with tags and annotations
        * **MCP Server Tracking**: Monitor MCP server configurations
        * **Export/Import**: Export snapshot data in various formats

        ## Authentication

        (Optional) API key or JWT token authentication will be added in future releases.

        ## Rate Limiting

        Currently no rate limiting. Will be added in production deployment.
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Add exception handlers
    add_exception_handlers(app)

    # Add routes
    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """Redirect root to API documentation."""
        return RedirectResponse(url="/docs")

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """
        Basic health check endpoint.

        Returns:
            Health status message
        """
        return {
            "status": "healthy",
            "service": "Claude Config API",
            "version": "1.0.0",
        }

    # Include routers
    from src.api.routes import snapshots, claude_config, paths, mcp

    app.include_router(
        snapshots.router,
        prefix="/api/v1",
        tags=["Snapshots"],
    )

    app.include_router(
        claude_config.router,
        prefix="/api/v1",
        tags=["Claude Config"],
    )

    app.include_router(
        paths.router,
        prefix="/api/v1",
        tags=["Paths"],
    )

    app.include_router(
        mcp.router,
        prefix="/api/v1",
        tags=["MCP Servers"],
    )

    # TODO: Add more routers as they're implemented
    # from src.api.routes import changes
    # app.include_router(changes.router, prefix="/api/v1", tags=["Changes"])

    logger.info(f"FastAPI app created: {app.title}")

    return app


# Create app instance
app = create_app()
