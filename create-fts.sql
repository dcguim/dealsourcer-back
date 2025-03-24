-- Ensure the textsearch extension is available
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Function to safely add textsearch column
CREATE OR REPLACE FUNCTION add_organization_textsearch_column()
RETURNS void AS $$
BEGIN
    -- Check if column doesn't exist before adding
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'organization' 
          AND column_name = 'textsearch'
    ) THEN
        ALTER TABLE organization 
        ADD COLUMN textsearch tsvector;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to create or update the textsearch index
CREATE OR REPLACE FUNCTION create_organization_textsearch_index()
RETURNS void AS $$
BEGIN
    -- Create GIN index if it doesn't exist
    IF NOT EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE tablename = 'organization' 
          AND indexname = 'idx_org_textsearch'
    ) THEN
        CREATE INDEX idx_org_textsearch 
        ON organization USING GIN(textsearch);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to update textsearch column
CREATE OR REPLACE FUNCTION update_org_textsearch() 
RETURNS trigger AS $$
BEGIN
    NEW.textsearch :=
        setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', 
            COALESCE(
                array_to_string(
                    (SELECT array_agg(
                        COALESCE(
                            (p -> 'name' ->> 'first_name')::text, 
                            ''
                        ) || ' ' ||
                        COALESCE(
                            (p -> 'name' ->> 'last_name')::text, 
                            ''
                        ) || ' ' ||
                        COALESCE(
                            (SELECT string_agg(elem::text, ' ')
                             FROM jsonb_array_elements_text(p -> 'name' -> 'other_names') elem
                            ),
                            ''
                        )
                    ) FROM jsonb_array_elements(NEW.participations) p), 
                    ' '
                ),
                ''
            )
        ), 'C');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- Function to create or replace the trigger
CREATE OR REPLACE FUNCTION create_organization_textsearch_trigger()
RETURNS void AS $$
BEGIN
    -- Drop existing trigger if it exists
    IF EXISTS (
        SELECT 1 
        FROM information_schema.triggers 
        WHERE event_object_table = 'organization' 
          AND trigger_name = 'trig_org_textsearch'
    ) THEN
        DROP TRIGGER trig_org_textsearch ON organization;
    END IF;

    -- Create new trigger
    CREATE TRIGGER trig_org_textsearch
    BEFORE INSERT OR UPDATE ON organization
    FOR EACH ROW EXECUTE FUNCTION update_org_textsearch();
END;
$$ LANGUAGE plpgsql;

-- Comprehensive setup function
CREATE OR REPLACE FUNCTION setup_organization_full_text_search()
RETURNS void AS $$
BEGIN
    -- Add textsearch column
    PERFORM add_organization_textsearch_column();

    -- Backfill existing data
    UPDATE organization 
    SET textsearch = 
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
        setweight(to_tsvector('english', 
            COALESCE(
                array_to_string(
                    (SELECT array_agg(
                        COALESCE(
                            (p -> 'name' ->> 'first_name')::text, 
                            ''
                        ) || ' ' ||
                        COALESCE(
                            (p -> 'name' ->> 'last_name')::text, 
                            ''
                        ) || ' ' ||
                        COALESCE(
                            (SELECT string_agg(elem::text, ' ')
                             FROM jsonb_array_elements_text(p -> 'name' -> 'other_names') elem
                            ),
                            ''
                        )
                    ) FROM jsonb_array_elements(participations) p), 
                    ' '
                ),
                ''
            )
        ), 'C');

    -- Create index
    PERFORM create_organization_textsearch_index();

    -- Create trigger
    PERFORM create_organization_textsearch_trigger();
END;
$$ LANGUAGE plpgsql;

-- Execute the setup
SELECT setup_organization_full_text_search();
