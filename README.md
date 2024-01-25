# Braingeneers Search
Crawls the braingeneers prp bucket indexing any found metadata.json in a database and exploring a web search front end at [search.braingeneers.gi.ucsc.edu](search.braingeneers.gi.ucsc.edu)


# Running Locally
```
python crawl.py -c 10
make streamlit
```

# Running in Docker Compose
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

# References
[SQLite FTS5 Extension](https://www.sqlite.org/fts5.html)

[Quick full-text search using SQLite](https://abdus.dev/posts/quick-full-text-search-using-sqlite/)

[Allen Institute Steamlit Interface](https://github.com/nlsschim/allen_institute_connection)