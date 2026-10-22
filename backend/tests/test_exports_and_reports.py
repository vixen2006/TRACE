"""
Tests for report generation and CSV export authorization.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_report_generation_and_retrieval(client: AsyncClient, auth_headers_user_a: dict):
    # Generate report
    gen_resp = await client.post(
        "/api/v1/reports",
        json={"report_type": "weekly_summary"},
        headers=auth_headers_user_a,
    )
    assert gen_resp.status_code == 201
    report_data = gen_resp.json()
    assert report_data["report_type"] == "weekly_summary"
    report_id = report_data["id"]

    # Fetch report by ID
    get_resp = await client.get(f"/api/v1/reports/{report_id}", headers=auth_headers_user_a)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == report_id


@pytest.mark.asyncio
async def test_csv_export_endpoint(client: AsyncClient, auth_headers_user_a: dict):
    csv_resp = await client.get("/api/v1/exports/csv", headers=auth_headers_user_a)
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"].startswith("text/csv")
    assert "Contribution ID,Summary,Role" in csv_resp.text
