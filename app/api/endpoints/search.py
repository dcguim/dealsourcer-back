from typing import Optional, List, Any
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.logger import logger
import asyncpg
import json

from app.models import SearchParams, SearchResponse, PaginatedResponse, OrganizationResponse
from app.core.dbconn import get_pool
from app.services.search_service import search_organizations_advanced

router = APIRouter()

# Helper function to parse JSON fields in results
def parse_json_fields(results):
    json_fields = ['participations', 'addresses', 'phone_infos', 'bank_info', 'capital', 'inferences', 'seat']
    parsed_results = []
    
    for result in results:
        parsed_result = dict(result)
        
        # Parse each potential JSON field
        for field in json_fields:
            if field in parsed_result and parsed_result[field]:
                try:
                    if isinstance(parsed_result[field], str) and parsed_result[field].lower() != 'null':
                        parsed_result[field] = json.loads(parsed_result[field])
                except (json.JSONDecodeError, ValueError):
                    # If parsing fails, keep as string
                    pass
        
        parsed_results.append(parsed_result)
    
    return parsed_results

@router.get("/search", 
            response_model=None,  # Remove response_model to allow custom response
            summary="Search Organizations",
            description="Search for organizations using various criteria")
async def search_orgs(
    # Existing organization-level parameters
    name: Optional[str] = Query(None, description="Organization name", min_length=2, max_length=255),
    description: Optional[str] = Query(None, description="Description keywords", min_length=2, max_length=500),
    jurisdiction: Optional[str] = Query(None, description="Jurisdiction", max_length=100),
    legal_form: Optional[str] = Query(None, description="Legal form", max_length=100),
    status: Optional[str] = Query(None, description="Status", max_length=50),
    
    # New participant-related parameters
    participant_name: Optional[str] = Query(None, description="Participant name", max_length=255),
    participant_birth_year: Optional[int] = Query(None, description="Participant birth year", ge=1900, le=2025),
    participant_birth_year_range: Optional[int] = Query(2, description="Range for birth year search", ge=0, le=10),
    
    # Pagination parameters
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Number of results to skip", ge=0),
    pool = Depends(get_pool)
):
    """
    Search for organizations using comprehensive criteria.
    
    Supports searching by:
    - Organization details (name, description, jurisdiction, etc.)
    - Participant details (name, birth year)
    
    Requires at least one search parameter to be provided.
    Returns a paginated list of organizations matching the search criteria.
    
    Validation:
    - At least one search parameter must be non-null
    - Enforces string length constraints
    - Limits result set size
    
    Returns:
    - Dictionary containing:
      * List of matching organizations
      * Pagination metadata
    
    Raises:
    - HTTPException 400 if no search parameters are provided
    - HTTPException 500 if database error occurs
    """
    # Validate that at least one search parameter is provided
    if not any([
        name, description, jurisdiction, legal_form, status,
        participant_name, participant_birth_year
    ]):
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
        participant_name=participant_name,
        participant_birth_year=participant_birth_year,
        participant_birth_year_range=participant_birth_year_range,
        limit=limit,
        offset=offset
    )
    
    try:
        # Execute search using the connection pool
        results, total_count = await search_organizations_advanced(pool, search_params)
        
        # Parse JSON fields in results
        parsed_results = parse_json_fields(results)
        
        # Log search details for monitoring
        logger.info(
            f"Comprehensive organization search: "
            f"params={search_params.dict()}, "
            f"total_results={total_count}"
        )
        
        # Return custom response structure to match test expectations
        # without relying on the model for shape
        return {
            "results": parsed_results,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
        }
    
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

