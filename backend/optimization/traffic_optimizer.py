"""
Traffic Signal Timing Optimizer for Indian Road Intersections.
Calculates dynamic phase allocations, clearance intervals, and pedestrian safety timings.
"""
from typing import Any, Dict


class TrafficSignalOptimizer:
    """Calculates dynamically optimized signal timings satisfying Indian traffic domain constraints."""

    # Domain constraints (Indian Road Congress / IRC standards)
    MIN_GREEN_SECONDS = 15
    MAX_GREEN_SECONDS = 90
    MIN_PEDESTRIAN_SECONDS = 12
    MAX_PEDESTRIAN_SECONDS = 40
    DEFAULT_YELLOW_SECONDS = 5
    MIN_CYCLE_SECONDS = 40
    MAX_CYCLE_SECONDS = 180

    def __init__(self):
        self.model = None
        print("Traffic Signal Optimizer initialized")

    def optimize_signals(
        self,
        junction_id: str,
        traffic_data: Dict[str, Any],
        weather_data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Compute safe, dynamic signal timings based on real-time traffic volume and environmental conditions.

        Args:
            junction_id: Identifier of the junction.
            traffic_data: Dict containing 'vehicle_count' and optionally 'pedestrian_count'.
            weather_data: Dict containing 'condition' (e.g., 'rain', 'fog').

        Returns:
            Dict containing 'optimized_timings' and 'congestion_level'.
        """
        # 1. Extract and sanitize inputs
        try:
            vehicle_count = max(0, int(traffic_data.get("vehicle_count", 0)))
        except (ValueError, TypeError):
            vehicle_count = 0

        try:
            pedestrian_count = max(0, int(traffic_data.get("pedestrian_count", 0)))
        except (ValueError, TypeError):
            pedestrian_count = 0

        # 2. Base timing calculations
        # Green time scales with vehicle volume (5 vehicles per 1s green increment)
        green_time = max(30, min(60, 30 + (vehicle_count // 5)))

        # Pedestrian crossing time scales with pedestrian density (3 pedestrians per 1s increment)
        pedestrian_time = max(15, min(30, 15 + (pedestrian_count // 3)))

        yellow_time = self.DEFAULT_YELLOW_SECONDS

        # 3. Weather impact multiplier (adverse weather demands longer clearance)
        weather_factor = 1.0
        if weather_data and isinstance(weather_data, dict):
            condition = str(weather_data.get("condition", "")).lower()
            if "rain" in condition or "wet" in condition:
                weather_factor = 1.2
            elif "fog" in condition or "mist" in condition:
                weather_factor = 1.3
            elif "night" in condition:
                weather_factor = 1.1

        # Apply multiplier and enforce hard bounds
        green_time = int(
            max(self.MIN_GREEN_SECONDS, min(self.MAX_GREEN_SECONDS, green_time * weather_factor))
        )
        pedestrian_time = int(
            max(self.MIN_PEDESTRIAN_SECONDS, min(self.MAX_PEDESTRIAN_SECONDS, pedestrian_time * weather_factor))
        )

        # 4. Phase synchronization
        # Opposite phase red clearance time includes cross-street green + yellow + pedestrian phase
        red_time = green_time + (yellow_time * 2) + pedestrian_time

        # Calculate estimated intersection congestion index (0.0 = free flow, 1.0 = gridlock)
        congestion_level = round(min(1.0, vehicle_count / 100.0), 2)

        # Total cycle length
        cycle_length = green_time + yellow_time + pedestrian_time + yellow_time
        cycle_length = max(self.MIN_CYCLE_SECONDS, min(self.MAX_CYCLE_SECONDS, cycle_length))

        optimized_timings = {
            "north_south": {
                "green": green_time,
                "yellow": yellow_time,
                "red": red_time,
            },
            "east_west": {
                "green": max(self.MIN_GREEN_SECONDS, int(green_time * 0.8)),
                "yellow": yellow_time,
                "red": red_time,
            },
            "pedestrian": {
                "crossing_time": pedestrian_time,
                "clearance_interval": yellow_time,
            },
            "cycle_length": cycle_length,
        }

        return {
            "junction_id": junction_id,
            "optimized_timings": optimized_timings,
            "congestion_level": congestion_level,
            "cycle_length": cycle_length,
            "weather_factor_applied": weather_factor,
            "is_optimized": True,
        }
