"""
Dependency injection functions for FastAPI endpoints.

Provides reusable dependencies for database sessions, authentication,
pagination, and other cross-cutting concerns.
"""

from typing import AsyncGenerator

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_manager
from src.core.schemas import PaginationParams


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.

    Yields:
        Database session

    Example:
        ```python
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            items = await db.execute(select(Item))
            return items.scalars().all()
        ```
    """
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        yield session


def get_pagination(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    sort_by: str | None = Query(None, description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
) -> PaginationParams:
    """
    Get pagination parameters dependency.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)

    Returns:
        Pagination parameters

    Example:
        ```python
        @router.get("/items")
        async def get_items(pagination: PaginationParams = Depends(get_pagination)):
            offset = pagination.offset
            limit = pagination.limit
            # ... query with offset and limit
        ```
    """
    return PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


# TODO: Add authentication dependencies when implementing Task 5.8
# async def get_current_user(
#     api_key: str = Header(..., alias="X-API-Key")
# ) -> User:
#     """Verify API key and return current user."""
#     ...

# async def require_admin(
#     user: User = Depends(get_current_user)
# ) -> User:
#     """Require admin privileges."""
#     if not user.is_admin:
#         raise HTTPException(status_code=403, detail="Admin access required")
#     return user

