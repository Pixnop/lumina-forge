"""HTTP API contract tests against the mini-vault fixture."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from optimizer.api.app import create_app


@pytest.fixture
def client(mini_vault: Path) -> Iterator[TestClient]:
    """FastAPI TestClient bound to the shared mini-vault fixture."""
    app = create_app(vault_dir=mini_vault)
    with TestClient(app) as c:
        yield c


def test_health_returns_ok_and_version(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"]


def test_vault_info_reports_fixture_counts(client: TestClient) -> None:
    response = client.get("/vault/info")
    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "characters": 1,
        "pictos": 6,
        "weapons": 2,
        "luminas": 4,
        "skills": 3,
        "synergies": 0,
    }


def test_vault_reload_is_idempotent(client: TestClient) -> None:
    before = client.get("/vault/info").json()
    reload_resp = client.post("/vault/reload")
    assert reload_resp.status_code == 200
    assert reload_resp.json() == before


def test_optimize_happy_path(
    client: TestClient, sample_inventory_dict: dict[str, Any]
) -> None:
    response = client.post(
        "/optimize",
        json={"inventory": sample_inventory_dict, "top": 3, "mode": "dps"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["builds"]) == 3

    # Ranks are 1-based and contiguous
    assert [b["rank"] for b in payload["builds"]] == [1, 2, 3]
    # Scores strictly non-increasing
    scores = [b["total_score"] for b in payload["builds"]]
    assert scores == sorted(scores, reverse=True)
    # Loadout echoes the inputs as slugs
    top = payload["builds"][0]
    assert top["loadout"]["character"] == "gustave"
    assert top["loadout"]["weapon"] in {"noahram", "heavy-hammer"}
    assert len(top["loadout"]["pictos"]) == 3


def test_optimize_rejects_unknown_character(
    client: TestClient, sample_inventory_dict: dict[str, Any]
) -> None:
    broken = dict(sample_inventory_dict, character="nobody")
    response = client.post("/optimize", json={"inventory": broken})
    assert response.status_code == 404
    assert "nobody" in response.json()["detail"]


def test_optimize_rejects_malformed_inventory(client: TestClient) -> None:
    response = client.post("/optimize", json={"inventory": {"character": 42}})
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


def test_optimize_honours_mode_balanced(
    client: TestClient, sample_inventory_dict: dict[str, Any]
) -> None:
    dps_top = client.post(
        "/optimize",
        json={"inventory": sample_inventory_dict, "top": 1, "mode": "dps"},
    ).json()["builds"][0]["total_score"]
    bal_top = client.post(
        "/optimize",
        json={"inventory": sample_inventory_dict, "top": 1, "mode": "balanced"},
    ).json()["builds"][0]["total_score"]

    # balanced adds utility × weight — never strictly smaller than pure DPS
    assert bal_top >= dps_top
