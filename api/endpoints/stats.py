from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_pool
from app.services.search_service import get_statistics
from app.models.organization import StatsResponse

router = APIRouter()

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    pool = Depends(get_pool)
):
    """
    Get basic statistics about the database
    """
    try:
        stats = await get_statistics(pool)
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
