from __future__ import annotations

import numpy as np

EPSILON = 1e-10
VALID_OPTION_TYPES = {"call", "put"}
VALID_POSITION_TYPES = {"long", "short"}


def to_numpy(value: float | list[float] | np.ndarray) -> tuple[np.ndarray, bool]:
    array = np.asarray(value, dtype=float)
    return array, array.ndim == 0


def restore_shape(value: np.ndarray | float, was_scalar: bool) -> np.ndarray | float:
    array = np.asarray(value, dtype=float)
    return float(array) if was_scalar else array


def validate_option_type(option_type: str) -> str:
    normalized = option_type.strip().lower()
    if normalized not in VALID_OPTION_TYPES:
        raise ValueError(f"Unsupported option type: {option_type!r}")
    return normalized


def validate_position_type(position_type: str) -> str:
    normalized = position_type.strip().lower()
    if normalized not in VALID_POSITION_TYPES:
        raise ValueError(f"Unsupported position type: {position_type!r}")
    return normalized


def validate_model_inputs(
    spot: np.ndarray,
    strike: float,
    volatility: float,
    maturity: float,
) -> None:
    if np.any(spot < 0.0):
        raise ValueError("Spot price must be non-negative.")
    if strike <= 0.0:
        raise ValueError("Strike price must be strictly positive.")
    if volatility < 0.0:
        raise ValueError("Volatility must be non-negative.")
    if maturity < 0.0:
        raise ValueError("Time to maturity must be non-negative.")


def intrinsic_value(spot: np.ndarray, strike: float, option_type: str) -> np.ndarray:
    option_type = validate_option_type(option_type)
    if option_type == "call":
        return np.maximum(spot - strike, 0.0)
    return np.maximum(strike - spot, 0.0)


def discounted_strike(strike: float, rate: float, maturity: float) -> float:
    return strike * np.exp(-rate * maturity)


def deterministic_option_value(
    spot: np.ndarray,
    strike: float,
    rate: float,
    maturity: float,
    option_type: str,
) -> np.ndarray:
    forward_boundary = discounted_strike(strike, rate, maturity)
    if option_type == "call":
        return np.maximum(spot - forward_boundary, 0.0)
    return np.maximum(forward_boundary - spot, 0.0)


def compute_d1_d2(
    spot: np.ndarray,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
) -> tuple[np.ndarray, np.ndarray]:
    sqrt_t = np.sqrt(maturity)
    safe_spot = np.maximum(spot, EPSILON)
    numerator = np.log(safe_spot / strike) + (rate + 0.5 * volatility**2) * maturity
    denominator = volatility * sqrt_t
    d1 = numerator / denominator
    d2 = d1 - volatility * sqrt_t
    return d1, d2


def create_price_grid(spot: float, strike: float, num_points: int = 301) -> np.ndarray:
    reference = max(float(spot), float(strike), 1.0)
    span = max(0.5 * reference, 1.35 * abs(float(spot) - float(strike)), 10.0)
    lower = max(0.0, min(strike - span, spot - 0.25 * span))
    upper = max(strike + span, spot + 0.25 * span)
    return np.linspace(lower, upper, num_points)


def position_sign(position_type: str) -> int:
    position_type = validate_position_type(position_type)
    return 1 if position_type == "long" else -1
