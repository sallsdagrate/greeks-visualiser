from __future__ import annotations

import numpy as np

from utils import (
    intrinsic_value,
    position_sign,
    restore_shape,
    to_numpy,
    validate_option_type,
)


def option_payoff(
    spot: float | list[float] | np.ndarray,
    strike: float,
    option_type: str,
    position_type: str,
) -> np.ndarray | float:
    option_type = validate_option_type(option_type)
    signed_position = position_sign(position_type)
    spot_array, was_scalar = to_numpy(spot)
    payoff = signed_position * intrinsic_value(spot_array, strike, option_type)
    return restore_shape(payoff, was_scalar)
