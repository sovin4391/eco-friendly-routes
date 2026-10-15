import axios from "axios";
import { getDemonstrationRoutes, calculateImpactSavings, DEMO_METADATA } from "../data/demoRoutes";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 8000,
});

/**
 * Checks live backend connectivity and service health.
 */
export async function checkBackendHealth() {
  try {
    const response = await apiClient.get("/health");
    return {
      connected: true,
      data: response.data,
      error: null,
    };
  } catch (error) {
    return {
      connected: false,
      data: null,
      error: error.response?.data?.detail || error.message,
    };
  }
}

/**
 * Fetches route recommendations and environmental emission comparisons.
 * 
 * Architecture Note:
 * Attempts live REST communication with the FastAPI backend. If the backend is
 * in its initial Phase 1 setup state (HTTP 501) or currently offline, it transparently
 * falls back to isolated demonstration data (`demoRoutes.js`), maintaining the exact
 * same response schema for seamless Phase 2 integration.
 */
export async function fetchRouteRecommendations(query) {
  const { origin, destination, vehicleType = "gasoline", travelMode = "ECO" } = query;

  try {
    // Attempt live backend call
    const response = await apiClient.post("/api/v1/routes/compare", {
      origin_name: origin,
      destination_name: destination,
      vehicle_type: vehicleType,
    });

    const rawRoutes = response.data.routes || [];
    const normalizedRoutes = rawRoutes.map((r, idx) => ({
      ...r,
      id: r.route_id || r.id || `route-${idx + 1}`,
      route_id: r.route_id || r.id || `route-${idx + 1}`,
      name: r.route_name || r.name || `Corridor ${idx + 1}`,
      route_name: r.route_name || r.name || `Corridor ${idx + 1}`,
      distanceKm: Number(r.distance_km ?? r.distanceKm ?? 0),
      distance_km: Number(r.distance_km ?? r.distanceKm ?? 0),
      durationMin: Number(r.duration_min ?? r.durationMin ?? 0),
      duration_min: Number(r.duration_min ?? r.durationMin ?? 0),
      co2Grams: Number(r.emission_estimate?.co2_grams ?? r.co2Grams ?? 0),
      energyKwh: r.emission_estimate?.energy_kwh != null
        ? Number(r.emission_estimate.energy_kwh)
        : (r.energyKwh != null ? Number(r.energyKwh) : (r.energy_kwh != null ? Number(r.energy_kwh) : null)),
      isRecommended: Boolean(r.is_recommended ?? r.isRecommended),
      is_recommended: Boolean(r.is_recommended ?? r.isRecommended),
      isFastest: Boolean(r.is_fastest ?? r.isFastest),
      is_fastest: Boolean(r.is_fastest ?? r.isFastest),
      rank: r.rank ?? idx + 1,
      color: r.color || (r.is_recommended ? "#10b981" : idx === 1 ? "#3b82f6" : "#f59e0b"),
      ecoScore: r.eco_score ?? r.ecoScore ?? 85,
      ecoScoreGrade: r.eco_score_grade ?? r.ecoScoreGrade ?? "A",
      routeCharacteristics: r.summary || r.routeCharacteristics || "Live path generated from OpenStreetMap road graph",
      coordinates: r.coordinates || [],
    }));

    return {
      success: true,
      isDemonstration: false,
      routes: normalizedRoutes,
      savings: calculateImpactSavings(normalizedRoutes, vehicleType),
      origin: response.data.origin || origin,
      destination: response.data.destination || destination,
      ecoSavingPercent: response.data.eco_saving_percent || 0.0,
      routingProvider: response.data.routing_provider || "OSRM (Open Source Routing Machine)",
      notice: response.data.notice,
      limitationsNote: response.data.limitations_note,
    };
  } catch (err) {
    // DO NOT silently fall back to demonstration routes on failed live request!
    let errorMessage = "Route calculation failed.";
    if (err.response?.data?.detail) {
      if (Array.isArray(err.response.data.detail)) {
        errorMessage = err.response.data.detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
      } else {
        errorMessage = String(err.response.data.detail);
      }
    } else if (err.message) {
      errorMessage = err.message;
    }

    return {
      success: false,
      isDemonstration: false,
      routes: [],
      savings: null,
      origin,
      destination,
      vehicleType,
      travelMode,
      notice: null,
      limitationsNote: null,
      error: errorMessage,
    };
  }
}

/**
 * Explicitly loads Phase 1 demonstration corridor routes (Connaught Place -> Cyber Hub).
 * Must only be invoked via an explicit user action (e.g. 'Load Demo Routes' button).
 */
export function getExplicitDemonstrationRoutes(vehicleType = "gasoline", travelMode = "ECO") {
  const demoRoutes = getDemonstrationRoutes(DEMO_METADATA.defaultOrigin, DEMO_METADATA.defaultDestination, vehicleType, travelMode);
  const savings = calculateImpactSavings(demoRoutes, vehicleType);

  return {
    success: true,
    isDemonstration: true,
    disclaimer: DEMO_METADATA.disclaimer,
    routes: demoRoutes,
    savings: savings,
    origin: DEMO_METADATA.defaultOrigin,
    destination: DEMO_METADATA.defaultDestination,
    vehicleType,
    travelMode,
    notice: "Demonstration Mode: Viewing pre-computed Phase 1 reference benchmark corridor (Connaught Place to Cyber Hub).",
    limitationsNote: "Demonstration benchmark data for project review presentation.",
    error: null,
  };
}

/**
 * Predicts vehicle CO2 emission rate (g/km) and route trip emission (g)
 * using the trained Random Forest model.
 */
export async function predictEmissions(vehicleParams, distanceKm = null) {
  try {
    const payload = {
      ...vehicleParams,
      distance_km: distanceKm,
    };
    const response = await apiClient.post("/api/v1/emissions/predict", payload);
    return {
      success: true,
      data: response.data,
      error: null,
    };
  } catch (err) {
    return {
      success: false,
      data: null,
      error: err.response?.data?.detail || err.message,
    };
  }
}

/**
 * Fetches verified empirical training metrics and metadata for the active ML model.
 */
export async function fetchModelMetadata() {
  try {
    const response = await apiClient.get("/api/v1/emissions/metadata");
    return {
      success: true,
      data: response.data,
      error: null,
    };
  } catch (err) {
    return {
      success: false,
      data: null,
      error: err.response?.data?.detail || err.message,
    };
  }
}

/**
 * Fetches operational status of the road damage detection model.
 */
export async function fetchRoadDamageStatus() {
  try {
    const response = await apiClient.get("/api/v1/road-damage/status");
    return {
      success: true,
      data: response.data,
      error: null,
    };
  } catch (err) {
    return {
      success: false,
      data: null,
      error: err.response?.data?.detail || err.message,
    };
  }
}

/**
 * Uploads a pavement image to perform road damage and pothole detection.
 */
export async function detectRoadDamage(file, confThreshold = 0.25) {
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiClient.post(
      `/api/v1/road-damage/detect?conf_threshold=${confThreshold}`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
    return {
      success: true,
      data: response.data,
      error: null,
    };
  } catch (err) {
    return {
      success: false,
      data: null,
      error: err.response?.data?.detail || err.message,
    };
  }
}

/**
 * Fetches verified RDD2022 pavement test samples available for instant demo.
 */
export async function fetchRoadDamageSamples() {
  try {
    const response = await apiClient.get("/api/v1/road-damage/samples");
    const samplesList = Array.isArray(response.data) ? response.data : (response.data.samples || []);
    return {
      success: true,
      samples: samplesList,
      error: null,
    };
  } catch (err) {
    return {
      success: false,
      samples: [],
      error: err.response?.data?.detail || err.message,
    };
  }
}


/**
 * Downloads a sample image as a Blob so it can be previewed and passed into detectRoadDamage.
 */
export async function fetchSampleImageBlob(url) {
  try {
    const response = await apiClient.get(url, { responseType: "blob" });
    return {
      success: true,
      blob: response.data,
      error: null,
    };
  } catch (err) {
    return {
      success: false,
      blob: null,
      error: err.response?.data?.detail || err.message,
    };
  }
}

export default apiClient;

