from fastapi import APIRouter, Depends, HTTPException

from app.core.dbconn import get_pool
from app.services.search_service import get_organization_statistics
from app.core.security import get_current_user

from app.models.organization import StatsResponse

router = APIRouter()

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    pool = Depends(get_pool),
    current_user: dict = Depends(get_current_user)
):
    """
    Get basic statistics about the database
    
    Requires authentication.
    """
    try:
        stats = await get_organization_statistics(pool)
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
