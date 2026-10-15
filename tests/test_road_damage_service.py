"""
Automated unit and integration tests for Road Damage Detection Service and API.
"""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from backend.services.road_damage_service import road_damage_service, RoadDamageService


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture
def sample_jpeg_bytes():
    """Generates a small valid in-memory JPEG image."""
    img = Image.new("RGB", (200, 200), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestRoadDamageServiceUnit:
    """Verifies service interface and class mappings."""

    def test_supported_classes_schema(self):
        classes = road_damage_service.get_supported_classes()
        assert len(classes) == 4
        codes = [c["code"] for c in classes]
        assert "D00" in codes  # Longitudinal Crack
        assert "D10" in codes  # Transverse Crack
        assert "D20" in codes  # Alligator Crack
        assert "D40" in codes  # Pothole

        # Verify pothole has highest severity weight
        pothole = next(c for c in classes if c["code"] == "D40")
        assert pothole["severity_weight"] == 3.0

    def test_service_unloaded_model_raises_runtime_error(self, sample_jpeg_bytes):
        # Create instance pointing to nonexistent weights
        from pathlib import Path
        svc = RoadDamageService(weights_path=Path("nonexistent_model.pt"))
        assert svc.is_available() is False
        with pytest.raises(RuntimeError, match="model is not loaded"):
            svc.detect_damage(sample_jpeg_bytes)

    def test_corrupted_image_raises_value_error(self):
        # Even if mock model available, corrupted bytes must raise ValueError
        svc = RoadDamageService(weights_path=Path("dummy.pt"))
        svc.model_loaded = True
        with pytest.raises(ValueError, match="not a valid, readable image"):
            svc.detect_damage(b"Not an image at all")


class TestRoadDamageFastAPIEndpoints:
    """Verifies HTTP endpoints under /api/v1/road-damage."""

    def test_status_endpoint_success(self, client):
        resp = client.get("/api/v1/road-damage/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "model_loaded" in data
        assert "supported_classes" in data
        assert len(data["supported_classes"]) == 4

    def test_detect_endpoint_rejects_unsupported_mime_type(self, client):
        # Uploading a text file
        files = {"file": ("test.txt", b"plain text content", "text/plain")}
        resp = client.post("/api/v1/road-damage/detect", files=files)
        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json()["detail"]

    def test_detect_endpoint_rejects_empty_file(self, client):
        files = {"file": ("empty.jpg", b"", "image/jpeg")}
        resp = client.post("/api/v1/road-damage/detect", files=files)
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"]

    def test_detect_endpoint_handles_missing_model_gracefully(self, client, sample_jpeg_bytes):
        # When model is not loaded, endpoint must return 503 without fake detections
        if not road_damage_service.is_available():
            files = {"file": ("road.jpg", sample_jpeg_bytes, "image/jpeg")}
            resp = client.post("/api/v1/road-damage/detect", files=files)
            assert resp.status_code == 503
            assert "unavailable" in resp.json()["detail"].lower()

    def test_detect_endpoint_live_inference_when_model_loaded(self, client, sample_jpeg_bytes):
        if road_damage_service.is_available():
            files = {"file": ("road.jpg", sample_jpeg_bytes, "image/jpeg")}
            resp = client.post("/api/v1/road-damage/detect?confidence_threshold=0.25", files=files)
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_model_loaded"] is True
            assert "detections" in data
            assert isinstance(data["detections"], list)
            assert "damage_severity_score" in data
            assert "pavement_status" in data
            assert data["image_dimensions"]["width"] == 200
            assert data["image_dimensions"]["height"] == 200

    def test_samples_list_endpoint(self, client):
        resp = client.get("/api/v1/road-damage/samples")
        assert resp.status_code == 200
        data = resp.json()
        assert "samples" in data
        assert len(data["samples"]) >= 1
        first_sample = data["samples"][0]
        assert "filename" in first_sample
        assert "url" in first_sample

    def test_sample_image_download_and_path_traversal_protection(self, client):
        # Valid sample download
        resp = client.get("/api/v1/road-damage/samples/India_000168.jpg")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"
        assert len(resp.content) > 1000

        # Non-whitelisted image returns 404
        bad_resp = client.get("/api/v1/road-damage/samples/unauthorized.jpg")
        assert bad_resp.status_code == 404

        # Path traversal rejected with 404
        traversal_resp = client.get("/api/v1/road-damage/samples/..%2F..%2Fmain.py")
        assert traversal_resp.status_code in [404, 400]


class TestExistingServicesUnaffected:
    """Confirms that adding road damage did not break emissions or routing endpoints."""

    def test_emissions_predict_still_works(self, client):
        payload = {"distance_km": 15.0, "vehicle_type": "gasoline"}
        resp = client.post("/api/v1/emissions/predict", json=payload)
        assert resp.status_code == 200
        assert resp.json()["trip_co2_grams"] > 0

    def test_route_comparison_still_works(self, client):
        payload = {
            "origin_name": "Connaught Place, Central City",
            "destination_name": "Cyber Hub, Tech Corridor",
            "vehicle_type": "gasoline"
        }
        resp = client.post("/api/v1/routes/compare", json=payload)
        assert resp.status_code == 200
        assert len(resp.json()["routes"]) >= 1
