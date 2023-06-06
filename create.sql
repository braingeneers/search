DROP TABLE IF EXISTS experiments;

CREATE TABLE experiments (
    -- id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    key VARCHAR(1024) PRIMARY KEY,
    metadata jsonb
);

CREATE INDEX gin_metadata ON experiments USING gin(to_tsvector('english', metadata));
