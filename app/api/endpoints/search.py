from typing import Optional, List, Any
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.logger import logger
import asyncpg

from app.models import SearchParams, SearchResponse, PaginatedResponse, OrganizationResponse
from app.core.dbconn import get_pool
from app.services.search_service import search_organizations

router = APIRouter()

@router.get("/search", 
            response_model=SearchResponse, 
            summary="Search Organizations",
            description="Search for organizations using various criteria")
async def search_orgs(
    name: Optional[str] = Query(None, description="Organization name", min_length=2, max_length=255),
    description: Optional[str] = Query(None, description="Description keywords", min_length=2, max_length=500),
    jurisdiction: Optional[str] = Query(None, description="Jurisdiction", max_length=100),
    legal_form: Optional[str] = Query(None, description="Legal form", max_length=100),
    status: Optional[str] = Query(None, description="Status", max_length=50),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Number of results to skip", ge=0),
    pool = Depends(get_pool)
) -> SearchResponse:
    """
    Search for organizations using various criteria.
    
    Requires at least one search parameter to be provided.
    Returns a paginated list of organizations matching the search criteria.
    
    Validation:
    - At least one search parameter must be non-null
    - Enforces string length constraints
    - Limits result set size
    
    Returns:
    - SearchResponse containing:
      * List of matching organizations
      * Pagination metadata
    
    Raises:
    - HTTPException 400 if no search parameters are provided
    - HTTPException 500 if database error occurs
    """
    # Validate that at least one search parameter is provided
    if not any([name, description, jurisdiction, legal_form, status]):
        raise HTTPException(
            status_code=400, 
            detail="At least one search parameter must be provided"
        )
    
    # Create search parameters object
    search_params = SearchParams(
        name=name,
        description=description,
        jurisdiction=jurisdiction,
        legal_form=legal_form,
        status=status,
        limit=limit,
        offset=offset
    )
    
    try:
        # Execute search using the connection pool
        results, total_count = await search_organizations(pool, search_params)
        
        # Log search details for monitoring
        logger.info(
            f"Organization search: "
            f"params={search_params.dict()}, "
            f"total_results={total_count}"
        )
        
        # Create and return response
        return SearchResponse(
            results=results,
            pagination=PaginatedResponse(
                total=total_count,
                limit=limit,
                offset=offset,
                has_more=(offset + limit) < total_count
            )
        )
    
    except asyncpg.PostgresError as e:
        # Log database-specific errors
        logger.error(f"PostgreSQL error in organization search: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Database error occurred while searching organizations"
        )
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in organization search: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while searching organizations"
        )
