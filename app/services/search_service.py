from typing import List, Dict, Any, Tuple, Optional
from asyncpg.pool import Pool
from app.models.organization import SearchParams

async def search_organizations(
    pool: Pool, 
    search_params: SearchParams
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Search for organizations based on the provided parameters
    
    Args:
        pool: Database connection pool
        search_params: Search parameters
        
    Returns:
        Tuple containing list of organization dictionaries and total count
    """
    # Base query - we'll build on this
    params = []
    param_pos = 0  # For parameter positioning
    
    # Determine search type and build query
    if search_params.name or search_params.description:
        # Use the full-text search capabilities
        search_terms = []
        
        if search_params.name:
            param_pos += 1
            search_terms.append(f"textsearch @@ plainto_tsquery('english', ${param_pos})")
            params.append(search_params.name)
        
        if search_params.description:
            param_pos += 1
            search_terms.append(f"textsearch @@ plainto_tsquery('english', ${param_pos})")
            params.append(search_params.description)
        
        # Start building the query with text search
        query = f"""
        SELECT * FROM organization 
        WHERE {' AND '.join(search_terms)}
        """
        
        # For counting total results
        count_query = f"""
        SELECT COUNT(*) FROM organization 
        WHERE {' AND '.join(search_terms)}
        """
        
        # Add sorting by relevance
        sort_clause = """
        ORDER BY ts_rank(textsearch, plainto_tsquery('english', $1)) DESC
        """
    else:
        # Standard field-based search
        query = "SELECT * FROM organization WHERE 1=1"
        count_query = "SELECT COUNT(*) FROM organization WHERE 1=1"
        sort_clause = "ORDER BY name"
    
    # Add additional filters
    if search_params.jurisdiction:
        param_pos += 1
        query += f" AND jurisdiction ILIKE ${param_pos}"
        count_query += f" AND jurisdiction ILIKE ${param_pos}"
        params.append(f"%{search_params.jurisdiction}%")
    
    if search_params.legal_form:
        param_pos += 1
        query += f" AND legal_form ILIKE ${param_pos}"
        count_query += f" AND legal_form ILIKE ${param_pos}"
        params.append(f"%{search_params.legal_form}%")
    
    if search_params.status:
        param_pos += 1
        query += f" AND status = ${param_pos}"
        count_query += f" AND status = ${param_pos}"
        params.append(search_params.status)
    
    # Add sorting
    if search_params.name or search_params.description:
        query += f" {sort_clause}"
    
    # Add pagination
    param_pos += 1
    query += f" LIMIT ${param_pos}"
    params.append(search_params.limit)
    
    param_pos += 1
    query += f" OFFSET ${param_pos}"
    params.append(search_params.offset)
    
    async with pool.acquire() as conn:
        # Execute search query
        rows = await conn.fetch(query, *params)
        
        # Get total count for pagination
        total_count = await conn.fetchval(count_query, *params[:-2])  # Exclude LIMIT and OFFSET params
        
        # Format results
        results = [dict(row) for row in rows]
        
        return results, total_count

async def get_organization_by_id(pool: Pool, org_id: str) -> Optional[Dict[str, Any]]:
    """
    Get organization by its ID
    
    Args:
        pool: Database connection pool
        org_id: Organization ID
        
    Returns:
        Organization as a dictionary, or None if not found
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM organization WHERE openregisters_id = $1",
            org_id
        )
        
        if not row:
            return None
            
        return dict(row)

async def get_statistics(pool: Pool) -> Dict[str, Any]:
    """
    Get database statistics
    
    Args:
        pool: Database connection pool
        
    Returns:
        Dictionary with statistics
    """
    async with pool.acquire() as conn:
        # Get total count
        total_count = await conn.fetchval("SELECT COUNT(*) FROM organization")
        
        # Get count by status
        status_rows = await conn.fetch("""
            SELECT status, COUNT(*) as count 
            FROM organization 
            WHERE status IS NOT NULL
            GROUP BY status
            ORDER BY count DESC
        """)
        status_counts = [dict(row) for row in status_rows]
        
        # Get count by jurisdiction
        jurisdiction_rows = await conn.fetch("""
            SELECT jurisdiction, COUNT(*) as count 
            FROM organization 
            WHERE jurisdiction IS NOT NULL
            GROUP BY jurisdiction 
            ORDER BY count DESC 
            LIMIT 10
        """)
        jurisdiction_counts = [dict(row) for row in jurisdiction_rows]
        
        # Get count by legal form
        legal_form_rows = await conn.fetch("""
            SELECT legal_form, COUNT(*) as count 
            FROM organization 
            WHERE legal_form IS NOT NULL
            GROUP BY legal_form 
            ORDER BY count DESC 
            LIMIT 10
        """)
        legal_form_counts = [dict(row) for row in legal_form_rows]
        
        return {
            "total_organizations": total_count,
            "by_status": status_counts,
            "top_jurisdictions": jurisdiction_counts,
            "top_legal_forms": legal_form_counts
        }
