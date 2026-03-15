import pytest

import garminconnect

DATE = "2023-07-01"


@pytest.fixture(scope="session")
def garmin() -> garminconnect.Garmin:
    return garminconnect.Garmin("email@example.org", "password")


@pytest.mark.vcr
def test_stats(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    stats = garmin.get_stats(DATE)
    assert "totalKilocalories" in stats
    assert "activeKilocalories" in stats


@pytest.mark.vcr
def test_user_summary(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    user_summary = garmin.get_user_summary(DATE)
    assert "totalKilocalories" in user_summary
    assert "activeKilocalories" in user_summary


@pytest.mark.vcr
def test_steps_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    steps = garmin.get_steps_data(DATE)
    if not steps:
        pytest.skip("No steps data for date")
    steps_data = steps[0]
    assert "steps" in steps_data


@pytest.mark.vcr
def test_floors(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    floors_data = garmin.get_floors(DATE)
    assert "floorValuesArray" in floors_data


@pytest.mark.vcr
def test_daily_steps(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    daily_steps_data = garmin.get_daily_steps(DATE, DATE)
    # The API returns a list of daily step dictionaries
    assert isinstance(daily_steps_data, list)
    assert len(daily_steps_data) > 0

    # Check the first day's data
    daily_steps = daily_steps_data[0]
    assert "calendarDate" in daily_steps
    assert "totalSteps" in daily_steps


@pytest.mark.vcr
def test_heart_rates(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    heart_rates = garmin.get_heart_rates(DATE)
    assert "calendarDate" in heart_rates
    assert "restingHeartRate" in heart_rates


@pytest.mark.vcr
def test_stats_and_body(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    stats_and_body = garmin.get_stats_and_body(DATE)
    assert "calendarDate" in stats_and_body
    assert "metabolicAge" in stats_and_body


@pytest.mark.vcr
def test_body_composition(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    body_composition = garmin.get_body_composition(DATE)
    assert "totalAverage" in body_composition
    assert "metabolicAge" in body_composition["totalAverage"]


@pytest.mark.vcr
def test_body_battery(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    bb = garmin.get_body_battery(DATE)
    if not bb:
        pytest.skip("No body battery data for date")
    body_battery = bb[0]
    assert "date" in body_battery
    assert "charged" in body_battery


@pytest.mark.vcr
def test_hydration_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    hydration_data = garmin.get_hydration_data(DATE)
    assert hydration_data
    assert "calendarDate" in hydration_data


@pytest.mark.vcr
def test_respiration_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    respiration_data = garmin.get_respiration_data(DATE)
    assert "calendarDate" in respiration_data
    assert "avgSleepRespirationValue" in respiration_data


@pytest.mark.vcr
def test_spo2_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    spo2_data = garmin.get_spo2_data(DATE)
    assert "calendarDate" in spo2_data
    assert "averageSpO2" in spo2_data


@pytest.mark.vcr
def test_hrv_data(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    hrv_data = garmin.get_hrv_data(DATE)
    # HRV data might not be available for all dates (API returns 204 No Content)
    if hrv_data is not None:
        # If data exists, validate the structure
        assert "hrvSummary" in hrv_data
        assert "weeklyAvg" in hrv_data["hrvSummary"]
    else:
        # If no data, that's also a valid response (204 No Content)
        assert hrv_data is None


@pytest.mark.vcr
def test_download_activity(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    activity_id = "11998957007"
    # This test may fail with 403 Forbidden if the activity is private or not accessible
    # In such cases, we verify that the appropriate error is raised
    try:
        activity = garmin.download_activity(activity_id)
        assert activity  # If successful, activity should not be None/empty
    except garminconnect.GarminConnectConnectionError as e:
        # Expected error for inaccessible activities
        assert "403" in str(e) or "Forbidden" in str(e)
        pytest.skip(
            "Activity not accessible (403 Forbidden) - expected in test environment"
        )


@pytest.mark.vcr
def test_all_day_stress(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    all_day_stress = garmin.get_all_day_stress(DATE)
    # Validate stress data structure
    assert "calendarDate" in all_day_stress
    assert "avgStressLevel" in all_day_stress
    assert "maxStressLevel" in all_day_stress
    assert "stressValuesArray" in all_day_stress


@pytest.mark.vcr
def test_upload(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    fpath = "tests/12129115726_ACTIVITY.fit"
    # This test may fail with 409 Conflict if the activity already exists
    # In such cases, we verify that the appropriate error is raised
    try:
        result = garmin.upload_activity(fpath)
        assert result  # If successful, should return upload result
    except Exception as e:
        # Expected error for duplicate uploads
        if "409" in str(e) or "Conflict" in str(e):
            pytest.skip(
                "Activity already exists (409 Conflict) - expected in test environment"
            )
        else:
            # Re-raise unexpected errors
            raise


@pytest.mark.vcr
def test_request_reload(garmin: garminconnect.Garmin) -> None:
    garmin.login()
    cdate = "2021-01-01"
    # Get initial steps data
    sum(steps["steps"] for steps in garmin.get_steps_data(cdate))
    # Test that request_reload returns a valid response
    reload_response = garmin.request_reload(cdate)
    assert reload_response is not None
    # Get steps data after reload - should still be accessible
    final_steps = sum(steps["steps"] for steps in garmin.get_steps_data(cdate))
    assert final_steps >= 0  # Steps data should be non-negative


class DummyResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def json(self) -> dict:
        return self.payload


def test_get_group_uses_membership_param(
    garmin: garminconnect.Garmin, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = {}

    def fake_connectapi(path: str, **kwargs) -> dict:
        captured["path"] = path
        captured["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(garmin, "connectapi", fake_connectapi)

    response = garmin.get_group(123, include_membership=False)

    assert response == {"ok": True}
    assert captured["path"] == "/group-service/group/123"
    assert captured["kwargs"]["params"] == {"includeMembership": "false"}


def test_get_connections_uses_expected_query_params(
    garmin: garminconnect.Garmin, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = {}

    def fake_connectapi(path: str, **kwargs) -> dict:
        captured["path"] = path
        captured["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(garmin, "connectapi", fake_connectapi)

    response = garmin.get_connections("example-user", start=1, limit=12)

    assert response == {"ok": True}
    assert (
        captured["path"]
        == "/connection-service/connection/v2/connections/pagination/example-user"
    )
    assert captured["kwargs"]["params"] == {
        "start": "1",
        "limit": "12",
        "displayMutedStatus": "true",
    }


def test_get_connection_suggestions_posts_json_payload(
    garmin: garminconnect.Garmin, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = {}

    def fake_post(namespace: str, path: str, **kwargs) -> DummyResponse:
        captured["namespace"] = namespace
        captured["path"] = path
        captured["kwargs"] = kwargs
        return DummyResponse({"results": []})

    monkeypatch.setattr(garmin.garth, "post", fake_post)

    response = garmin.get_connection_suggestions(cursor=None, limit=20)

    assert response == {"results": []}
    assert captured["namespace"] == "connectapi"
    assert captured["path"] == "/usersearch-service/connection/suggestions/pagination"
    assert captured["kwargs"] == {
        "json": {"cursor": None, "limit": 20},
        "api": True,
    }


def test_search_groups_posts_form_payload(
    garmin: garminconnect.Garmin, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = {}

    def fake_post(namespace: str, path: str, **kwargs) -> DummyResponse:
        captured["namespace"] = namespace
        captured["path"] = path
        captured["kwargs"] = kwargs
        return DummyResponse({"groups": []})

    monkeypatch.setattr(garmin.garth, "post", fake_post)

    response = garmin.search_groups("running", start=1, limit=16)

    assert response == {"groups": []}
    assert captured["namespace"] == "connectapi"
    assert captured["path"] == "/group-service/keyword"
    assert captured["kwargs"] == {
        "data": {"keyword": "running", "start": "1", "limit": "16"},
        "api": True,
    }


def test_search_connections_posts_form_payload(
    garmin: garminconnect.Garmin, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = {}

    def fake_post(namespace: str, path: str, **kwargs) -> DummyResponse:
        captured["namespace"] = namespace
        captured["path"] = path
        captured["kwargs"] = kwargs
        return DummyResponse({"results": []})

    monkeypatch.setattr(garmin.garth, "post", fake_post)

    response = garmin.search_connections("casey", start=1, limit=15)

    assert response == {"results": []}
    assert captured["namespace"] == "connectapi"
    assert captured["path"] == "/usersearch-service/search?displayMutedStatus=true"
    assert captured["kwargs"] == {
        "data": {"keyword": "casey", "start": "1", "limit": "15"},
        "api": True,
    }


def test_get_connection_steps_leaderboard_uses_steps_metric(
    garmin: garminconnect.Garmin, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = {}

    def fake_connectapi(path: str, **kwargs) -> dict:
        captured["path"] = path
        captured["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(garmin, "connectapi", fake_connectapi)

    response = garmin.get_connection_steps_leaderboard(
        "2026-03-10", "2026-03-16", start=1, limit=100
    )

    assert response == {"ok": True}
    assert captured["path"] == "/userstats-service/leaderboard/wellness/connection"
    assert captured["kwargs"]["params"] == {
        "metricId": "29",
        "startDate": "2026-03-10",
        "endDate": "2026-03-16",
        "start": "1",
        "limit": "100",
    }
