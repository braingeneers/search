# Braingeneers Search
Crawls the braingeneers prp bucket indexing any found metadata.json in a database and exploring a web search front end at [search.braingeneers.gi.ucsc.edu](search.braingeneers.gi.ucsc.edu)

# Running
NOTE: Not ready for running off the shelf, but can get some running via:
```
make build
make debug
or
make up
make follow
...
make shell
python crawl.py
```

docker-compose.yml is configured to be run from the braingeneers server so that it integrates into the mission control reverse proxy exposing this as search.braingeneers.gi.ucsc.edu

# Sample SQl Queries
```sql
-- find all uuid's
select metadata->'uuid' from experiments limit 5;

-- find all the 'num_wells' fields
select distinct metadata->'num_wells' from experiments;

-- Print out all the metadata pretty style
select jsonb_pretty(metadata) from experiments limit 5;

-- Find key for all metadata that has a field value that starts includes awbg:
select metadata -> 'uuid' from experiments where to_tsvector('english', metadata) @@ to_tsquery('awbg:*');

-- Pretty print metadata for a single experiment by uuid
select jsonb_pretty(metadata) from experiments where metadata->>'uuid' = '2020-02-10-i-HUVECS';
```

# References
[Postgres Full Text Search vs the rest](https://supabase.com/blog/postgres-full-text-search-vs-the-rest)


[Postgres GIN Index](https://www.postgresql.org/docs/15/gin-intro.html)

[Forget SQL vs NoSQL - Get the Best of Both Worlds with JSON in PostgreSQL](https://arctype.com/blog/json-in-postgresql/)

[How to avoid performance bottlenecks when using JSONB in PostgreSQL](https://www.metisdata.io/blog/how-to-avoid-performance-bottlenecks-when-using-jsonb-in-postgresql)

[JSON in PostgreSQL: The Ultimate Guide](https://www.databasestar.com/postgresql-json/)

[Allen Institute Steamlit Interface](https://github.com/nlsschim/allen_institute_connection)