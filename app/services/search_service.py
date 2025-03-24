from typing import List, Dict, Any, Tuple, Optional
from asyncpg.pool import Pool
import logging
import pdb
from psycopg2 import sql
from app.models.organization import SearchParams
import time

logger = logging.getLogger(__name__)

async def search_organizations_advanced(
    pool: Pool, 
    search_params: SearchParams
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Perform comprehensive full-text search on organizations.
    """
    start_time = time.time()
    
    # Validate input parameters
    limit = max(1, min(search_params.limit, 100))
    offset = max(0, search_params.offset)
    
    # Prepare dynamic search conditions
    where_conditions = []
    query_params = []
    
    # Process name and description searches - these work with textsearch column
    name_search_terms = []
    if search_params.name:
        name_search_terms.append(search_params.name)
    if search_params.description:
        name_search_terms.append(search_params.description)
    if search_params.participant_name:
        name_search_terms.append(search_params.participant_name)
    
    # If we have any text search terms, add them to the textsearch condition
    if name_search_terms:
        combined_terms = " ".join(name_search_terms)
        where_conditions.append("textsearch @@ plainto_tsquery(${})")
        query_params.append(combined_terms)
    
    # For birth year, use a direct JSON path query which is more reliable
    if search_params.participant_birth_year is not None:
        # Find organizations with a participant born in the specified year
        where_conditions.append("""
            EXISTS (
                SELECT 1 FROM jsonb_array_elements(participations) as p
                WHERE SUBSTRING(p->'participant'->>'birth_date', 1, 4) = ${}
            )
        """)
        query_params.append(str(search_params.participant_birth_year))
    
    # Additional organization filters
    additional_filters = [
        ('jurisdiction', search_params.jurisdiction),
        ('legal_form', search_params.legal_form),
        ('status', search_params.status)
    ]
    
    # Add additional filters
    for column, value in additional_filters:
        if value:
            where_conditions.append(f"{column} = ${{}}")
            query_params.append(value)
    
    async with pool.acquire() as conn:
        try:
            # Construct base query
            query = "SELECT * FROM organization"
            count_query = "SELECT COUNT(*) FROM organization"
            
            # Add WHERE conditions
            if where_conditions:
                # Dynamically number the placeholders
                numbered_conditions = []
                numbered_params = []
                param_index = 1
                
                for condition in where_conditions:
                    # Replace {} with actual parameter numbers
                    numbered_condition = condition.format(*[param_index + i for i in range(condition.count('${}'))])
                    numbered_conditions.append(numbered_condition)
    
                    # Add corresponding number of parameters
                    param_count = condition.count('${}')
                    numbered_params.extend(query_params[param_index-1:param_index-1+param_count])
                    param_index += param_count
                
                where_clause = " WHERE " + " AND ".join(numbered_conditions)
                query += where_clause
                count_query += where_clause
                
                # Store the parameters for the WHERE conditions separately
                count_params = numbered_params.copy()
                query_params = numbered_params
            else:
                count_params = []
            
            # Add ordering
            if name_search_terms:
                query += f" ORDER BY ts_rank(textsearch, plainto_tsquery(${len(query_params) + 1})) DESC"
                query_params.append(" ".join(name_search_terms))
            else:
                query += " ORDER BY name"
            
            # Add pagination
            query += f" LIMIT ${len(query_params) + 1} OFFSET ${len(query_params) + 2}"
            query_params.extend([limit, offset])
            
            # Print query for debugging
            debug_query = query
            for i, param in enumerate(query_params):
                debug_query = debug_query.replace(f"${i+1}", f"'{param}'")
            logger.debug(f"Executing query: {debug_query}")
            
            # Execute queries
            query_start_time = time.time()
            results = await conn.fetch(query, *query_params)
            query_time = time.time() - query_start_time
            
            count_start_time = time.time()
            total_count = await conn.fetchval(count_query, *count_params)
            count_time = time.time() - count_start_time
            
            # Log performance metrics
            total_time = time.time() - start_time
            logger.info(
                f"Search performance: "
                f"Total={total_time:.3f}s, "
                f"Query={query_time:.3f}s, "
                f"Count={count_time:.3f}s, "
                f"Results={len(results)}, "
                f"ParamCount={len(query_params)}"
            )
            
            return results, total_count
        
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise

        
async def search_organizations(
    pool: Pool, 
    search_params: SearchParams
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Perform full-text search on organizations leveraging textsearch column.
    
    Args:
        pool: Database connection pool
        search_params: Search parameters
        
    Returns:
        Tuple containing list of organization dictionaries and total count.
    """
    # Validate input parameters
    limit = max(1, min(search_params.limit, 100))  # Ensure limit is between 1 and 100
    offset = max(0, search_params.offset)  # Offset cannot be negative

    # Query conditions
    where_conditions = []
    query_values = []
    
    # Full-text search condition
    if search_params.name or search_params.description:
        search_terms = []
        if search_params.name:
            search_terms.append(search_params.name)
        if search_params.description:
            search_terms.append(search_params.description)
        
        where_conditions.append("textsearch @@ plainto_tsquery($1)")
        query_values.append(" ".join(search_terms))  # Combine terms into one query string

    # Additional filters
    filter_mappings = [
        ('jurisdiction', search_params.jurisdiction),
        ('legal_form', search_params.legal_form),
        ('status', search_params.status)
    ]

    param_index = len(query_values) + 1  # Ensure placeholder indices are correct
    for column, value in filter_mappings:
        if value:
            where_conditions.append(f"{column} = ${param_index}")
            query_values.append(value)
            param_index += 1  # Increment for next parameter

    async with pool.acquire() as conn:
        try:
            # Construct query dynamically
            query = "SELECT * FROM organization"
            count_query = "SELECT COUNT(*) FROM organization"

            # Add WHERE conditions
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
                count_query += " WHERE " + " AND ".join(where_conditions)

            # Add ORDER BY
            if search_params.name or search_params.description:
                query += f" ORDER BY ts_rank(textsearch, plainto_tsquery($1)) DESC"
            else:
                query += " ORDER BY name"

            # Add LIMIT and OFFSET
            query += f" LIMIT ${param_index} OFFSET ${param_index + 1}"
            query_values.append(limit)
            query_values.append(offset)

            # Debug: Print the final query
            print("Executing query:", query)
            print("With values:", query_values)

            # Execute queries
            result = await conn.fetch(query, *query_values)
            total_count = await conn.fetchval(count_query, *query_values[:-2])  # Exclude limit/offset
            print(result)
            print(total_count)
            return result, total_count

        except Exception as e:
            logger.error(f"Full-text search error: {str(e)}")
            raise
        
async def get_organization_by_id(pool: Pool, org_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve an organization by its unique identifier
    
    Args:
        pool: Database connection pool
        org_id: Unique organization identifier
    
    Returns:
        Organization details or None if not found
    """
    if not org_id:
        return None
    
    try:
        async with pool.acquire() as conn:
            # Construct query with parameterized identifier
            query = sql.SQL("SELECT * FROM organization WHERE openregisters_id = %s")
            
            row = await conn.fetchrow(str(query), org_id)
            return dict(row) if row else None
    
    except Exception as e:
        logger.error(f"Error retrieving organization by ID: {str(e)}")
        raise

async def get_organization_statistics(pool: Pool) -> Dict[str, Any]:
    """
    Retrieve aggregate statistics about organizations
    
    Args:
        pool: Database connection pool
    
    Returns:
        Dictionary of organization statistics
    """
    try:
        async with pool.acquire() as conn:
            # Total organization count
            total_count_query = sql.SQL("SELECT COUNT(*) FROM organization")
            total_count = await conn.fetchval(str(total_count_query))
            
            # Prepare statistical queries with safe formatting
            async def safe_aggregate_query(query_str: str) -> List[Dict[str, Any]]:
                try:
                    query = sql.SQL(query_str)
                    rows = await conn.fetch(str(query))
                    return [dict(row) for row in rows]
                except Exception as e:
                    logger.error(f"Aggregate query error: {str(e)}")
                    return []
            
            # Prepare statistical queries
            status_query = """
                SELECT status, COUNT(*) as count 
                FROM organization 
                WHERE status IS NOT NULL
                GROUP BY status
                ORDER BY count DESC
                LIMIT 10
            """
            
            jurisdiction_query = """
                SELECT jurisdiction, COUNT(*) as count 
                FROM organization 
                WHERE jurisdiction IS NOT NULL
                GROUP BY jurisdiction 
                ORDER BY count DESC 
                LIMIT 10
            """
            
            legal_form_query = """
                SELECT legal_form, COUNT(*) as count 
                FROM organization 
                WHERE legal_form IS NOT NULL
                GROUP BY legal_form 
                ORDER BY count DESC 
                LIMIT 10
            """
            
            # Execute aggregate queries
            status_counts = await safe_aggregate_query(status_query)
            jurisdiction_counts = await safe_aggregate_query(jurisdiction_query)
            legal_form_counts = await safe_aggregate_query(legal_form_query)
            
            # Return comprehensive statistics
            return {
                "total_organizations": total_count,
                "by_status": status_counts,
                "top_jurisdictions": jurisdiction_counts,
                "top_legal_forms": legal_form_counts
            }
    
    except Exception as e:
        logger.error(f"Organization statistics error: {str(e)}")
        raise
