from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from app.core.dbconn import get_pool
from app.services.search_service import search_organizations
from app.models.organization import SearchParams, SearchResponse, PaginatedResponse

router = APIRouter()

@router.get("/search", response_model=SearchResponse)
async def search_orgs(
    name: Optional[str] = Query(None, description="Organization name"),
    description: Optional[str] = Query(None, description="Description keywords"),
    jurisdiction: Optional[str] = Query(None, description="Jurisdiction"),
    legal_form: Optional[str] = Query(None, description="Legal form"),
    status: Optional[str] = Query(None, description="Status"),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Number of results to skip", ge=0),
    pool = Depends(get_pool)
):
    """
    Search for organizations using various criteria
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
        # Execute search
        results, total_count = await search_organizations(pool, search_params)
        
        # Create response
        return SearchResponse(
            results=results,
            pagination=PaginatedResponse(
                total=total_count,
                limit=limit,
                offset=offset,
                has_more=(offset + limit) < total_count
            )
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
