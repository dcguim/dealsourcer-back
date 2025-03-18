import asyncpg
from .config import settings

# Database connection pool
pool = None

async def get_pool():
    """Get the database connection pool"""
    global pool
    return pool

async def create_connection_pool():
    """Create the database connection pool"""
    global pool
    
    if pool is None:
        try:
            pool = await asyncpg.create_pool(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                min_size=settings.DB_MIN_CONNECTIONS,
                max_size=settings.DB_MAX_CONNECTIONS
            )
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            raise
    
    return pool

async def close_connection_pool():
    """Close the database connection pool"""
    global pool
    
    if pool:
        await pool.close()
        pool = None
