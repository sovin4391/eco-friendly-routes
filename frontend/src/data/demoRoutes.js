/**
 * Phase 1 Demonstration Route Data
 * 
 * IMPORTANT:
 * This file contains isolated demonstration route geometries and simulated emission metrics
 * for the Phase 1 project presentation.
 * 
 * In subsequent project phases, this data contract will be supplied dynamically by:
 * - Real routing engine (OSRM / OpenRouteService) for geometry
 * - Scikit-learn regression model for CO2 predictions
 * - Dynamic Eco Score algorithm
 */

export const DEMO_METADATA = {
  isDemonstrationData: true,
  disclaimer: "Demonstration Values for Phase 1 Project Review — Not Live Machine Learning Predictions",
  defaultOrigin: "Connaught Place, Central City",
  defaultDestination: "Cyber Hub, Tech Corridor",
};

// Polyline coordinate paths [latitude, longitude]
export const ROUTE_GEOMETRIES = {
  eco: [
    [28.6315, 77.2167],
    [28.6189, 77.2088],
    [28.5982, 77.1950],
    [28.5723, 77.1732],
    [28.5489, 77.1550],
    [28.5270, 77.1350],
    [28.5085, 77.1120],
    [28.4950, 77.0980],
    [28.4890, 77.0890],
    [28.4940, 77.0880],
  ],
  fast: [
    [28.6315, 77.2167],
    [28.6250, 77.2350],
    [28.5950, 77.2450],
    [28.5600, 77.2280],
    [28.5200, 77.1850],
    [28.4950, 77.1250],
    [28.4850, 77.0950],
    [28.4940, 77.0880],
  ],
  short: [
    [28.6315, 77.2167],
    [28.6150, 77.2100],
    [28.5850, 77.1900],
    [28.5550, 77.1700],
    [28.5300, 77.1450],
    [28.5100, 77.1200],
    [28.4980, 77.0950],
    [28.4940, 77.0880],
  ],
};

/**
 * Multipliers by vehicle powertrain
 */
const VEHICLE_EMISSION_FACTORS = {
  gasoline: 1.0,
  diesel: 0.92,
  hybrid: 0.55,
  ev: 0.15, // lifecycle equivalent grid carbon
};

/**
 * Returns candidate routes dynamically adjusted for vehicle type and travel mode preference.
 */
export function getDemonstrationRoutes(origin = DEMO_METADATA.defaultOrigin, destination = DEMO_METADATA.defaultDestination, vehicleType = "gasoline", travelMode = "ECO") {
  const factor = VEHICLE_EMISSION_FACTORS[vehicleType.toLowerCase()] || 1.0;

  const baseEcoCO2 = Math.round(1350 * factor);
  const baseFastCO2 = Math.round(2180 * factor);
  const baseShortCO2 = Math.round(2620 * factor);

  const rawRoutes = [
    {
      id: "route-eco",
      name: "Ring Corridor (Green Choice)",
      routeCategory: "ECO",
      rank: 1,
      isRecommended: true,
      distanceKm: 18.4,
      durationMin: 32,
      co2Grams: baseEcoCO2,
      energyKwh: (18.4 * 0.18 * (vehicleType === "ev" ? 1.0 : 0.8)).toFixed(1),
      ecoScore: 94,
      ecoScoreGrade: "A+",
      congestionLevel: "Low (Free Flow)",
      elevationGainM: 28,
      routeCharacteristics: "Optimal average speed (45 km/h), minimal traffic bottlenecks, steady momentum",
      color: "#10b981", // Emerald
      coordinates: ROUTE_GEOMETRIES.eco,
    },
    {
      id: "route-fast",
      name: "Expressway Bypass",
      routeCategory: "FAST",
      rank: 2,
      isRecommended: false,
      distanceKm: 22.1,
      durationMin: 27,
      co2Grams: baseFastCO2,
      energyKwh: (22.1 * 0.22 * (vehicleType === "ev" ? 1.0 : 0.8)).toFixed(1),
      ecoScore: 74,
      ecoScoreGrade: "B+",
      congestionLevel: "Moderate (High Speed)",
      elevationGainM: 42,
      routeCharacteristics: "Higher cruising speed (75 km/h), greater aerodynamic drag, longer travel distance",
      color: "#3b82f6", // Blue
      coordinates: ROUTE_GEOMETRIES.fast,
    },
    {
      id: "route-short",
      name: "Direct City Arterial",
      routeCategory: "BALANCED",
      rank: 3,
      isRecommended: false,
      distanceKm: 16.5,
      durationMin: 44,
      co2Grams: baseShortCO2,
      energyKwh: (16.5 * 0.28 * (vehicleType === "ev" ? 1.0 : 0.8)).toFixed(1),
      ecoScore: 56,
      ecoScoreGrade: "C",
      congestionLevel: "Severe (Stop & Go)",
      elevationGainM: 35,
      routeCharacteristics: "Shortest geometric distance, 14 signalized intersections, frequent idling and deceleration",
      color: "#f59e0b", // Amber
      coordinates: ROUTE_GEOMETRIES.short,
    },
  ];

  // Re-order recommended route based on chosen travel mode
  if (travelMode === "FAST") {
    return [
      { ...rawRoutes[1], rank: 1, isRecommended: true },
      { ...rawRoutes[0], rank: 2, isRecommended: false },
      { ...rawRoutes[2], rank: 3, isRecommended: false },
    ];
  } else if (travelMode === "BALANCED") {
    return [
      { ...rawRoutes[0], rank: 1, isRecommended: true },
      { ...rawRoutes[1], rank: 2, isRecommended: false },
      { ...rawRoutes[2], rank: 3, isRecommended: false },
    ];
  }

  // Default ECO mode
  return rawRoutes;
}

/**
 * Computes comparative environmental impact savings between the recommended route and the baseline fastest route.
 */
export function calculateImpactSavings(routes, vehicleType = "gasoline") {
  if (!routes || routes.length === 0) return null;

  const recommended = routes.find((r) => r.isRecommended || r.is_recommended) || routes[0];
  const fastest = routes.find((r) => (r.isFastest || r.is_fastest || r.id === "route-fast")) || (routes.length > 1 ? routes[1] : routes[0]);
  const baseline = fastest || recommended;

  const recCO2 = Number(recommended.co2Grams ?? recommended.emission_estimate?.co2_grams ?? 0);
  const baseCO2 = Number(baseline.co2Grams ?? baseline.emission_estimate?.co2_grams ?? recCO2);

  const co2DifferenceGrams = Math.max(0, Math.round(baseCO2 - recCO2));
  const percentageSaved = baseCO2 > 0 
    ? Math.round((co2DifferenceGrams / baseCO2) * 100) 
    : 0;

  // Tree absorption equivalent: 1 mature urban tree absorbs ~21.7 kg CO2 / year (~60 g CO2 / day)
  const treeAbsorptionDays = (co2DifferenceGrams / 60).toFixed(1);

  // Fuel saved equivalent: 1 liter gasoline ≈ 2,392g CO2
  const fuelSavedLiters = (co2DifferenceGrams / 2392).toFixed(2);

  const recDur = Number(recommended.durationMin ?? recommended.duration_min ?? 0);
  const baseDur = Number(baseline.durationMin ?? baseline.duration_min ?? recDur);

  // EV Electricity savings
  const recEnergy = recommended.energyKwh != null 
    ? Number(recommended.energyKwh) 
    : (recommended.emission_estimate?.energy_kwh != null ? Number(recommended.emission_estimate.energy_kwh) : null);
  const baseEnergy = baseline.energyKwh != null 
    ? Number(baseline.energyKwh) 
    : (baseline.emission_estimate?.energy_kwh != null ? Number(baseline.emission_estimate.energy_kwh) : null);

  const energySavedKwh = (recEnergy != null && baseEnergy != null && baseEnergy > recEnergy)
    ? Number((baseEnergy - recEnergy).toFixed(2))
    : 0.0;
  
  const energyPercentageSaved = (baseEnergy != null && baseEnergy > 0 && energySavedKwh > 0)
    ? Math.round((energySavedKwh / baseEnergy) * 100)
    : 0;

  const isEv = (vehicleType && vehicleType.toLowerCase() === "ev") || (recCO2 === 0 && baseCO2 === 0);

  return {
    recommendedRouteName: recommended.name || recommended.route_name,
    baselineRouteName: baseline.name || baseline.route_name,
    co2SavedGrams: co2DifferenceGrams,
    co2SavedKg: (co2DifferenceGrams / 1000).toFixed(2),
    percentageSaved,
    treeAbsorptionDays,
    fuelSavedLiters,
    timeTradeoffMin: Math.max(0, Math.round(recDur - baseDur)),
    isEv,
    recEnergyKwh: recEnergy,
    baseEnergyKwh: baseEnergy,
    energySavedKwh,
    energyPercentageSaved,
  };
}

