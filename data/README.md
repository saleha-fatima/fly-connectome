# Escape circuit data

These files are a small, reproducible extract from the Janelia MaleCNS neuPrint
dataset `male-cns:v1.0`:

- `escape_neurons.csv`: the 126 LC4 cells, 185 LPLC2 cells, and bilateral DNp01
  (Giant Fiber) cells participating in the selected direct circuit;
- `escape_connections.csv`: one row per direct LC4/LPLC2-to-DNp01 edge;
- `escape_connection_summary.csv`: totals grouped by source type and side; and
- `escape_circuit_metadata.json`: dataset UUID, retrieval time, exact Cypher
  queries, row counts, and checksums.

Regenerate the extract from the project root with:

```bash
python fetch_connectome.py
```

The endpoint currently allows public queries. If authentication is requested,
create a neuPrint account and set `NEUPRINT_TOKEN` in your shell; the script
will use it without writing it to disk.

MaleCNS is provided under CC BY. Dataset source and access documentation:
https://male-cns.janelia.org/download/
