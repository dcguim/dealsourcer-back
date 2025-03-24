import sqlite3
import psycopg2
import json
import random
from psycopg2.extras import Json
import time

# Database connection parameters
SQLITE_DB_PATH = "/Users/dguim/work/dealsourcing/back/data.db"  # Update with your SQLite file path
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DATABASE = "dealsourcer_dev"
PG_USER = "dev_user"
PG_PASSWORD = "dev"
SAMPLE_PERCENTAGE = 20  # 20% of the data

def get_sqlite_schema():
    """Get the schema of the organization table from SQLite"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute("PRAGMA table_info(organization);")
    schema = cursor.fetchall()
    
    # Format schema information
    columns = []
    for col in schema:
        cid, name, data_type, not_null, default_val, is_pk = col
        columns.append({
            "name": name,
            "type": data_type,
            "not_null": bool(not_null),
            "is_pk": bool(is_pk)
        })
    
    conn.close()
    return columns

def create_postgres_table(pg_conn):
    """Create the organization table in PostgreSQL with appropriate column types"""
    cursor = pg_conn.cursor()
    
    # Get SQLite schema
    columns = get_sqlite_schema()
    
    # Map SQLite types to PostgreSQL types
    type_mapping = {
        "VARCHAR": "TEXT",
        "TEXT": "TEXT",
        "INTEGER": "INTEGER",
        "REAL": "REAL",
        "DATE": "DATE",
        "DATETIME": "TIMESTAMP",
        "JSON": "JSONB",
        "BLOB": "BYTEA"
    }
    
    # Build CREATE TABLE statement
    column_defs = []
    primary_keys = []
    
    for col in columns:
        name = col["name"]
        pg_type = type_mapping.get(col["type"].upper(), "TEXT")
        
        # Handle JSON columns
        if col["type"] == "JSON":
            pg_type = "JSONB"
        
        column_def = f"\"{name}\" {pg_type}"
        
        if col["not_null"]:
            column_def += " NOT NULL"
            
        column_defs.append(column_def)
        
        if col["is_pk"]:
            primary_keys.append(f"\"{name}\"")
    
    # Add primary key constraint if any
    if primary_keys:
        pk_constraint = f"PRIMARY KEY ({', '.join(primary_keys)})"
        column_defs.append(pk_constraint)
    
    # Create the table
    create_table_sql = f"""
    DROP TABLE IF EXISTS organization;
    CREATE TABLE organization (
        {', '.join(column_defs)}
    );
    """
    
    cursor.execute(create_table_sql)
    
    # Create indexes for better query performance
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_org_jurisdiction ON organization(jurisdiction);
    CREATE INDEX IF NOT EXISTS idx_org_legal_form ON organization(legal_form);
    CREATE INDEX IF NOT EXISTS idx_org_status ON organization(status);
    """)
    
    # Create trigram indexes for name and description
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_org_name_trgm ON organization USING gin (name gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS idx_org_description_trgm ON organization USING gin (description gin_trgm_ops);
    """)
    
    pg_conn.commit()
    print("PostgreSQL table created with indexes")

def process_json_value(value):
    """Process JSON string to be inserted correctly into PostgreSQL"""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return Json(json.loads(value))
        except json.JSONDecodeError:
            return value
    return value

def prepare_row_for_postgres(row, columns):
    """Process a SQLite row for insertion into PostgreSQL"""
    processed_row = []
    
    for i, col in enumerate(columns):
        value = row[i]
        
        # Handle JSON columns
        if col["type"] == "JSON":
            value = process_json_value(value)
            
        processed_row.append(value)
    
    return processed_row

def migrate_sample_data():
    """Migrate a sample of data from SQLite to PostgreSQL"""
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get column schema for processing
    columns = get_sqlite_schema()
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )
    
    # Create the table structure in PostgreSQL
    create_postgres_table(pg_conn)
    
    # Get total row count
    sqlite_cursor.execute("SELECT COUNT(*) FROM organization")
    total_rows = sqlite_cursor.fetchone()[0]
    
    # Calculate sample size (20% of total)
    sample_size = int(total_rows * SAMPLE_PERCENTAGE / 100)
    print(f"Total rows: {total_rows}")
    print(f"Sample size (20%): {sample_size}")
    
    # Get all primary keys
    sqlite_cursor.execute("SELECT openregisters_id FROM organization")
    all_ids = [row[0] for row in sqlite_cursor.fetchall()]
    
    # Randomly select 20% of IDs
    sample_ids = random.sample(all_ids, sample_size)
    
    # Get column names for insert statement
    column_names = [col["name"] for col in columns]
    
    # Get primary key column indexes
    pk_indexes = [i for i, col in enumerate(columns) if col["is_pk"]]
    
    # Create a ON CONFLICT DO NOTHING clause for PostgreSQL upsert
    insert_sql = f"""
    INSERT INTO organization ({', '.join([f'"{name}"' for name in column_names])})
    VALUES ({', '.join(['%s' for _ in column_names])})
    ON CONFLICT DO NOTHING
    """
    
    # Process in batches
    batch_size = 1000
    start_time = time.time()
    processed_rows = 0
    inserted_rows = 0
    
    pg_cursor = pg_conn.cursor()
    
    try:
        # Process IDs in batches
        for i in range(0, len(sample_ids), batch_size):
            batch_ids = sample_ids[i:i+batch_size]
            placeholders = ", ".join(["?" for _ in batch_ids])
            
            # Fetch data for this batch of IDs
            sqlite_cursor.execute(
                f"SELECT * FROM organization WHERE openregisters_id IN ({placeholders})",
                batch_ids
            )
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                continue
                
            # Process batch
            batch_values = []
            for row in rows:
                processed_row = prepare_row_for_postgres(row, columns)
                batch_values.append(processed_row)

            # Insert with ON CONFLICT DO NOTHING to handle duplicates
            pg_cursor.executemany(insert_sql, batch_values)
            
            # Get number of rows affected by the insert
            rows_affected = pg_cursor.rowcount
            inserted_rows += rows_affected
            
            pg_conn.commit()
            
            processed_rows += len(rows)
            
            # Print progress
            progress = (processed_rows / sample_size) * 100
            elapsed = time.time() - start_time
            remaining = (elapsed / processed_rows) * (sample_size - processed_rows) if processed_rows > 0 else 0
            
            print(f"Progress: {progress:.2f}% ({processed_rows}/{sample_size}) - "
                  f"Inserted: {inserted_rows} rows - "
                  f"Elapsed: {elapsed:.2f}s - "
                  f"Estimated remaining: {remaining:.2f}s")
    
    except Exception as e:
        pg_conn.rollback()
        print(f"Error during migration: {str(e)}")
        raise
    
    finally:
        # Close all connections
        pg_cursor.close()
        pg_conn.close()
        sqlite_cursor.close()
        sqlite_conn.close()
    
    total_time = time.time() - start_time
    print(f"Migration completed in {total_time:.2f} seconds")

def setup_postgres_fts():
    """Set up PostgreSQL full-text search"""
    pg_conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )
    cursor = pg_conn.cursor()
    
    try:
        print("Setting up PostgreSQL full-text search...")
        
        # Create a tsvector column for fast full-text search
        cursor.execute("""
        ALTER TABLE organization ADD COLUMN IF NOT EXISTS textsearch tsvector;
        UPDATE organization SET textsearch = 
            setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B');
        CREATE INDEX IF NOT EXISTS idx_org_textsearch ON organization USING GIN(textsearch);
        """)
        
        # Create a function to update the tsvector column automatically
        cursor.execute("""
        CREATE OR REPLACE FUNCTION update_org_textsearch() RETURNS trigger AS $$
        BEGIN
            NEW.textsearch :=
                setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """)
        
        # Create a trigger to call the function
        cursor.execute("""
        DROP TRIGGER IF EXISTS trigger_update_organization_textsearch ON organization;
        CREATE TRIGGER trigger_update_organization_textsearch
            BEFORE INSERT OR UPDATE ON organization
            FOR EACH ROW
            EXECUTE FUNCTION update_org_textsearch();
        """)
        
        pg_conn.commit()
        print("PostgreSQL full-text search setup completed")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"Error setting up PostgreSQL full-text search: {str(e)}")
        raise
    
    finally:
        cursor.close()
        pg_conn.close()

if __name__ == "__main__":
    print("Starting sample data migration from SQLite to PostgreSQL...")
    migrate_sample_data()
    print("\nSetting up full-text search capabilities...")
    setup_postgres_fts()
    print("\nMigration and setup complete!")
