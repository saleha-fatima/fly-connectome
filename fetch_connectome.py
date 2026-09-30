"""Download the small LC4/LPLC2 -> DNp01 circuit from MaleCNS neuPrint.

The public neuPrint endpoint currently permits these queries without a token.
If that changes, set NEUPRINT_TOKEN to a token copied from your neuPrint profile.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_SERVER = "https://neuprint.janelia.org"
DEFAULT_DATASET = "male-cns:v1.0"

NEURON_QUERY = """
MATCH (source:Neuron)-[:ConnectsTo]->(target:Neuron)
WHERE source.type IN ["LC4", "LPLC2"] AND target.type = "DNp01"
WITH collect(DISTINCT source) + collect(DISTINCT target) AS circuit_nodes
UNWIND circuit_nodes AS n
RETURN DISTINCT
  n.bodyId AS body_id,
  n.type AS type,
  n.instance AS instance,
  n.somaSide AS side,
  n.status AS status,
  n.superclass AS superclass,
  n.consensusNt AS consensus_neurotransmitter,
  n.predictedNtConfidence AS neurotransmitter_confidence,
  n.pre AS presynaptic_sites,
  n.post AS postsynaptic_sites
ORDER BY type, instance, body_id
""".strip()

CONNECTION_QUERY = """
MATCH (source:Neuron)-[connection:ConnectsTo]->(target:Neuron)
WHERE source.type IN ["LC4", "LPLC2"] AND target.type = "DNp01"
RETURN
  source.bodyId AS source_body_id,
  source.type AS source_type,
  source.instance AS source_instance,
  target.bodyId AS target_body_id,
  target.type AS target_type,
  target.instance AS target_instance,
  connection.weight AS synapse_count
ORDER BY target_body_id, source_type, source_body_id
""".strip()

SUMMARY_QUERY = """
MATCH (source:Neuron)-[connection:ConnectsTo]->(target:Neuron)
WHERE source.type IN ["LC4", "LPLC2"] AND target.type = "DNp01"
RETURN
  source.type AS source_type,
  source.instance AS source_instance,
  target.bodyId AS target_body_id,
  target.instance AS target_instance,
  count(source) AS connected_source_neurons,
  sum(connection.weight) AS synapse_count,
  min(connection.weight) AS minimum_per_neuron,
  max(connection.weight) AS maximum_per_neuron
ORDER BY target_body_id, source_type
""".strip()


def request_json(
    url: str, payload: dict[str, str] | None = None
) -> dict[str, object]:
    headers = {"Accept": "application/json", "User-Agent": "fly-connectome/1.0"}
    token = os.environ.get("NEUPRINT_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")

    request = Request(url, data=body, headers=headers, method="POST" if body else "GET")
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def run_query(server: str, dataset: str, cypher: str) -> dict[str, object]:
    result = request_json(
        f"{server.rstrip('/')}/api/custom/custom",
        {"dataset": dataset, "cypher": cypher},
    )
    if "columns" not in result or "data" not in result:
        raise RuntimeError(f"Unexpected neuPrint response: {result}")
    return result


def write_csv(path: Path, result: dict[str, object]) -> None:
    columns = result["columns"]
    rows = result["data"]
    assert isinstance(columns, list) and isinstance(rows, list)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default=DEFAULT_SERVER)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    neurons = run_query(args.server, args.dataset, NEURON_QUERY)
    connections = run_query(args.server, args.dataset, CONNECTION_QUERY)
    summary = run_query(args.server, args.dataset, SUMMARY_QUERY)

    neuron_path = args.output_dir / "escape_neurons.csv"
    connection_path = args.output_dir / "escape_connections.csv"
    summary_path = args.output_dir / "escape_connection_summary.csv"
    write_csv(neuron_path, neurons)
    write_csv(connection_path, connections)
    write_csv(summary_path, summary)

    neuron_rows = neurons["data"]
    connection_rows = connections["data"]
    assert isinstance(neuron_rows, list) and isinstance(connection_rows, list)
    type_counts = Counter(row[1] for row in neuron_rows)

    datasets = request_json(f"{args.server.rstrip('/')}/api/dbmeta/datasets")
    dataset_metadata = datasets.get(args.dataset, {})
    metadata = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "server": args.server,
        "dataset": args.dataset,
        "dataset_uuid": dataset_metadata.get("uuid"),
        "dataset_last_modified": dataset_metadata.get("last-mod"),
        "selection": "All LC4 and LPLC2 neurons with a direct ConnectsTo edge to DNp01, plus the target DNp01 neurons.",
        "semantics": "Each connection row is one neuron-to-neuron edge; synapse_count is neuPrint ConnectsTo.weight.",
        "counts": {
            "neurons": len(neuron_rows),
            "connections": len(connection_rows),
            "neurons_by_type": dict(sorted(type_counts.items())),
            "synapses": sum(int(row[-1]) for row in connection_rows),
        },
        "queries": {
            "neurons": NEURON_QUERY,
            "connections": CONNECTION_QUERY,
            "summary": SUMMARY_QUERY,
        },
        "files": {
            neuron_path.name: {"sha256": sha256(neuron_path)},
            connection_path.name: {"sha256": sha256(connection_path)},
            summary_path.name: {"sha256": sha256(summary_path)},
        },
    }
    metadata_path = args.output_dir / "escape_circuit_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(
        f"Saved {len(neuron_rows)} neurons, {len(connection_rows)} connections, "
        f"and {metadata['counts']['synapses']} synapses to {args.output_dir}"
    )


if __name__ == "__main__":
    main()
