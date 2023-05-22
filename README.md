# search
Prototype experiment search engine

Recursively walks experiments in S3 storing any json found in a postgres database for structured and free form search.

# Installation,
[Rust](https://www.rust-lang.org/tools/install)

# Sample SQl Queries
```sql
-- find all uuid's
select metadata->'uuid' from experiments;

-- find all the 'num_wells' fields
select distinct metadata->'num_wells' from experiments;

-- Print out all the metadata pretty style
select jsonb_pretty(metadata) from experiments;

-- Search all metadata fields that start with 'awbg' 
select metadata -> 'uuid' from experiments where to_tsvector('english', metadata) @@ to_tsquery('awbg:*');
```

# References
[Postgres GIN Index](https://www.postgresql.org/docs/15/gin-intro.html)

[Forget SQL vs NoSQL - Get the Best of Both Worlds with JSON in PostgreSQL](https://arctype.com/blog/json-in-postgresql/)

[How to avoid performance bottlenecks when using JSONB in PostgreSQL](https://www.metisdata.io/blog/how-to-avoid-performance-bottlenecks-when-using-jsonb-in-postgresql)