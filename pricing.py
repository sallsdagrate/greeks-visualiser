from __future__ import annotations

import numpy as np
from scipy.stats import norm

from utils import (
    EPSILON,
    compute_d1_d2,
    deterministic_option_value,
    intrinsic_value,
    restore_shape,
    to_numpy,
    validate_model_inputs,
    validate_option_type,
)


def black_scholes_price(
    spot: float | list[float] | np.ndarray,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
    option_type: str,
) -> np.ndarray | float:
    option_type = validate_option_type(option_type)
    spot_array, was_scalar = to_numpy(spot)
    validate_model_inputs(spot_array, strike, volatility, maturity)

    if maturity <= EPSILON:
        price = intrinsic_value(spot_array, strike, option_type)
        return restore_shape(price, was_scalar)

    if volatility <= EPSILON:
        price = deterministic_option_value(spot_array, strike, rate, maturity, option_type)
        return restore_shape(price, was_scalar)

    d1, d2 = compute_d1_d2(spot_array, strike, rate, volatility, maturity)
    discount_factor = np.exp(-rate * maturity)

    if option_type == "call":
        price = spot_array * norm.cdf(d1) - strike * discount_factor * norm.cdf(d2)
    else:
        price = strike * discount_factor * norm.cdf(-d2) - spot_array * norm.cdf(-d1)

    return restore_shape(price, was_scalar)
