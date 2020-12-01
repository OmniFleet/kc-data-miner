import pytest
import requests

from miner import extract_telemetry, send_telemetry, VehicleTelemetry


@pytest.mark.parametrize("input", [
    [],
    None,
    {},
    "",
    0,
    0.0
])
def test_extract_telemetry_bad_data(input):
    """Assert exception on bad data"""
    with pytest.raises(Exception):
        extract_telemetry(input, "testing")


def test_extract_telemetry_valid_data(vehicle_data):
    """assert extract telemetry returns a valid VehicleTelemety object"""
    data = vehicle_data.get("entity")[0]
    result = extract_telemetry(data, "testing")
    assert isinstance(result, VehicleTelemetry)
    assert result.source == "testing"
    assert result.vehicle_id == data["vehicle"]["vehicle"]["id"]


def test_send_telemetry_no_data():
    """assert send telemetry with no data is successfull"""
    count = send_telemetry([], "")
    assert count == 0


def test_send_telemetry_vehicle_list(requests_mock, vehicle):
    server = "http://testing.ci"
    requests_mock.post(server)
    data = [vehicle] * 100
    count = send_telemetry(data, server)
    assert count == 100


def test_send_telemetry_request_exception(requests_mock, vehicle):
    """assert send telemetry handles exceptions"""
    server = "http://testing.ci"
    requests_mock.post(server, exc=requests.exceptions.ConnectTimeout)
    data = [vehicle] * 100
    count = send_telemetry(data, server)
    assert count == 0
