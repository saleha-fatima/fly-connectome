import csv
import json
from collections import Counter
from pathlib import Path


DATA_DIR = Path(__file__).parents[1] / "data"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def test_escape_circuit_contains_expected_bilateral_pathway() -> None:
    neurons = read_csv("escape_neurons.csv")
    connections = read_csv("escape_connections.csv")

    assert Counter(row["type"] for row in neurons) == {
        "DNp01": 2,
        "LC4": 126,
        "LPLC2": 185,
    }
    assert {row["target_body_id"] for row in connections} == {"10001", "10010"}
    assert len(connections) == 311
    assert sum(int(row["synapse_count"]) for row in connections) == 11_224


def test_metadata_matches_dataset_files() -> None:
    metadata = json.loads(
        (DATA_DIR / "escape_circuit_metadata.json").read_text(encoding="utf-8")
    )

    assert metadata["dataset"] == "male-cns:v1.0"
    assert metadata["dataset_uuid"] == "4b2087c0fbe046bfaf0d60bc970e3e5d"
    assert metadata["counts"]["neurons"] == 313
    assert metadata["counts"]["connections"] == 311
