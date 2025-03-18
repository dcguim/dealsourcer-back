from fastapi import APIRouter, Depends, Path, HTTPException

from app.core.database import get_pool
from app.services.search_service import get_organization_by_id
from app.models.organization import OrganizationResponse

router = APIRouter()

@router.get("/organization/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str = Path(..., description="Organization ID (openregisters_id)"),
    pool = Depends(get_pool)
):
    """
    Get detailed information about a specific organization
    """
    try:
        result = await get_organization_by_id(pool, org_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
