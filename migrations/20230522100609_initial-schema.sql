CREATE TABLE experiments (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    key VARCHAR(1024) NOT NULL,
    metadata jsonb
);
