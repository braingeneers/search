# Braingeneers Search
NOTE: In process to refactor to support on demand access to NWB on the NRP

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

# h5wasm
[h5wasm](https://github.com/usnistgov/h5wasm) enables the full hdf5 library to run natively in the browser. Using [Emscripten FS.createLazyFile](https://emscripten.org/docs/api_reference/Filesystem-API.html) enables providing h5wasm a virtual file backed by [http that can use range requests](https://github.com/emscripten-core/emscripten/blob/524b94f1040115355cedda92bcff240b7bcd4a2a/src/library_fs.js#L1650) to incrementally access the h5 file over the wire. The paves the way to provide a presigned s3 URL so that a browser based app can directly access an h5 file in a cloud store. Unfortunately you can only generate a presigned URL for a single HTTP method, and h5wasm performs a HEAD to get capabilities (like range requests) before making a GET. To work around this the flask server in thie repo responds to the HEAD request directly and then provides a presigned URL redirection for the GET request so that the browser is directly pulling data from s3. This requires that the headers in the HEAD request provide the right capabilities. This approach has the downside of a redirect for every chunk from the proxy to the client. Another approach taken by flatiron's dendro is to fork h5wasm and use an [aborted fetch to just get the content length](https://github.com/flatironinstitute/dendro/blob/99d8869f8bc143754370b71e15c8a03e4081075b/src/RemoteH5File/RemoteH5Worker.js#L7) Here is the detailed sequence of requests and responses that h5wasm makes then leads to this incremental reading:

## h5wasm HEAD Request and Response
```
HEAD /data/aff5f64d-9a69-4ff3-a6fe-13a3f30dca50 HTTP/1.1
Accept: */*
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Connection: keep-alive
Host: localhost:5282
Referer: http://localhost:5282/static/worker.js
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15

HTTP/1.1 200 OK
Accept-Ranges: bytes
Cache-Control: max-age=3600
Connection: keep-alive
Content-Length: 4966709395
Content-Type: application/octet-stream
Date: Mon, 18 Mar 2024 15:17:34 GMT
ETag: W/"11795069-4966709395-2024-03-11T19:11:17.335Z"
Keep-Alive: timeout=5
Last-Modified: Mon, 11 Mar 2024 19:11:17 GMT
```

## h5wasm First GET Request and Response
```
GET /data/aff5f64d-9a69-4ff3-a6fe-13a3f30dca50 HTTP/1.1
Accept: */*
Accept-Encoding: identity
Accept-Language: en-US,en;q=0.9
Connection: keep-alive
Host: localhost:5282
Range: bytes=0-1048575
Referer: http://localhost:5282/static/worker.js
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15

HTTP/1.1 206 Partial Content
Accept-Ranges: bytes
Cache-Control: max-age=3600
Connection: keep-alive
Content-Length: 1048576
Content-Range: bytes 0-1048575/4966709395
Content-Type: application/octet-stream
Date: Mon, 18 Mar 2024 15:17:34 GMT
ETag: W/"11795069-4966709395-2024-03-11T19:11:17.335Z"
Keep-Alive: timeout=5
Last-Modified: Mon, 11 Mar 2024 19:11:17 GMT
```

# Sample NWB Files on NRP
```
s3://braingeneers/ephys/2023-04-02-e-hc328_unperturbed/shared/hc3.28_hckcr1_chip16835_plated34.2_rec4.2.nwb
s3://braingeneers/ephys/2023-04-02-e-hc328_unperturbed/shared/hc3.28_hckcr1_chip16835_plated34.2_rec4.2_kilosort2_curated_s1.nwb
```

# References

## Indexing
[SQLite FTS5 Extension](https://www.sqlite.org/fts5.html)

[Quick full-text search using SQLite](https://abdus.dev/posts/quick-full-text-search-using-sqlite/)

[Allen Institute Steamlit Interface](https://github.com/nlsschim/allen_institute_connection)

## NWB
[Neurodata Without Borders(NWB)](https://www.nwb.org)

[A NWB-based dataset and processing pipeline of human single-neuron activity during a declarative memory task](https://www.nature.com/articles/s41597-020-0415-9)

[NWB Examples](https://github.com/HSUPipeline/NWBExamples)

[h5wasm](https://github.com/usnistgov/h5wasm)

[h5wasm wrapper for h5 from http](https://github.com/garrettmflynn/hdf5-io)

[How h5wasm accesses files over http via Emscripten lazy loading](https://emscripten.org/docs/porting/files/Synchronous-Virtual-XHR-Backed-File-System-Usage.html)

[GitHub thread on access h5 via range requests](https://github.com/usnistgov/h5wasm/issues/12)

[Chunking and indexing note in an issue](https://github.com/usnistgov/h5wasm/issues/47#issuecomment-1482683578)

[React components to visualize and graph h5 data (uses h5wasm)](https://github.com/silx-kit/h5web?tab=readme-ov-file)

## Flask + React
[How To Create a React + Flask Project](https://blog.miguelgrinberg.com/post/how-to-create-a-react--flask-project)

[React with TypeScript or JavaScript: Which is Better?](https://www.emizentech.com/blog/react-with-typescript-or-javascript.html)