CREATE VIRTUAL TABLE IF NOT EXISTS experiments USING fts5(uuid, path, metadata);