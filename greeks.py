from __future__ import annotations

import numpy as np
from scipy.stats import norm

from utils import (
    EPSILON,
    compute_d1_d2,
    discounted_strike,
    restore_shape,
    to_numpy,
    validate_model_inputs,
    validate_option_type,
)


def analytical_greeks(
    spot: float | list[float] | np.ndarray,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
    option_type: str,
) -> dict[str, np.ndarray | float]:
    option_type = validate_option_type(option_type)
    spot_array, was_scalar = to_numpy(spot)
    validate_model_inputs(spot_array, strike, volatility, maturity)

    greek_values: dict[str, np.ndarray] = {
        "delta": np.zeros_like(spot_array, dtype=float),
        "gamma": np.zeros_like(spot_array, dtype=float),
        "vega": np.zeros_like(spot_array, dtype=float),
        "theta": np.zeros_like(spot_array, dtype=float),
        "rho": np.zeros_like(spot_array, dtype=float),
    }

    if maturity <= EPSILON:
        greek_values["delta"] = _piecewise_delta(spot_array, strike, option_type)
        return _restore_greeks(greek_values, was_scalar)

    if volatility <= EPSILON:
        boundary = discounted_strike(strike, rate, maturity)
        greek_values["delta"] = _piecewise_delta(spot_array, boundary, option_type)

        carry = rate * strike * np.exp(-rate * maturity)
        if option_type == "call":
            in_the_money = spot_array > boundary
            greek_values["theta"] = np.where(in_the_money, -carry, 0.0)
            greek_values["rho"] = np.where(
                in_the_money,
                strike * maturity * np.exp(-rate * maturity),
                0.0,
            )
        else:
            in_the_money = spot_array < boundary
            greek_values["theta"] = np.where(in_the_money, carry, 0.0)
            greek_values["rho"] = np.where(
                in_the_money,
                -strike * maturity * np.exp(-rate * maturity),
                0.0,
            )

        return _restore_greeks(greek_values, was_scalar)

    d1, d2 = compute_d1_d2(spot_array, strike, rate, volatility, maturity)
    sqrt_t = np.sqrt(maturity)
    discount_factor = np.exp(-rate * maturity)
    pdf_d1 = norm.pdf(d1)

    if option_type == "call":
        greek_values["delta"] = norm.cdf(d1)
        greek_values["theta"] = (
            -(spot_array * pdf_d1 * volatility) / (2.0 * sqrt_t)
            - rate * strike * discount_factor * norm.cdf(d2)
        )
        greek_values["rho"] = strike * maturity * discount_factor * norm.cdf(d2)
    else:
        greek_values["delta"] = norm.cdf(d1) - 1.0
        greek_values["theta"] = (
            -(spot_array * pdf_d1 * volatility) / (2.0 * sqrt_t)
            + rate * strike * discount_factor * norm.cdf(-d2)
        )
        greek_values["rho"] = -strike * maturity * discount_factor * norm.cdf(-d2)

    greek_values["gamma"] = pdf_d1 / (np.maximum(spot_array, EPSILON) * volatility * sqrt_t)
    greek_values["vega"] = spot_array * pdf_d1 * sqrt_t

    return _restore_greeks(greek_values, was_scalar)


def delta(*args, **kwargs) -> np.ndarray | float:
    return analytical_greeks(*args, **kwargs)["delta"]


def gamma(*args, **kwargs) -> np.ndarray | float:
    return analytical_greeks(*args, **kwargs)["gamma"]


def vega(*args, **kwargs) -> np.ndarray | float:
    return analytical_greeks(*args, **kwargs)["vega"]


def theta(*args, **kwargs) -> np.ndarray | float:
    return analytical_greeks(*args, **kwargs)["theta"]


def rho(*args, **kwargs) -> np.ndarray | float:
    return analytical_greeks(*args, **kwargs)["rho"]


def _piecewise_delta(spot: np.ndarray, boundary: float, option_type: str) -> np.ndarray:
    boundary_hits = np.isclose(spot, boundary, atol=1e-8, rtol=0.0)
    if option_type == "call":
        delta_values = np.where(spot > boundary, 1.0, 0.0)
        return np.where(boundary_hits, 0.5, delta_values)

    delta_values = np.where(spot < boundary, -1.0, 0.0)
    return np.where(boundary_hits, -0.5, delta_values)


def _restore_greeks(
    greek_values: dict[str, np.ndarray],
    was_scalar: bool,
) -> dict[str, np.ndarray | float]:
    return {
        greek_name: restore_shape(greek_array, was_scalar)
        for greek_name, greek_array in greek_values.items()
    }
