import asyncpg
from .config import settings

# Database connection pool
pool = None

logger = logging.getLogger("app.db")

async def get_pool():
    """Get the database connection pool"""
    global pool
    return pool

async def create_connection_pool():
    """Create the database connection pool"""
    global pool
    
    if pool is None:
        try:
            logger.info(f"Connecting to database at {settings.DB_HOST}:{settings.DB_PORT}")
            pool = await asyncpg.create_pool(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                min_size=settings.DB_MIN_CONNECTIONS,
                max_size=settings.DB_MAX_CONNECTIONS
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}\n{traceback.format_exc()}")
            raise
    
    return pool

async def close_connection_pool():
    """Close the database connection pool"""
    global pool
    
    if pool:
        await pool.close()
        pool = None
