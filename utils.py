# Copyright (c) 2025 VerNe.
# All rights reserved.
#
# This code is for personal academic use only.
# Unauthorized use, copying, or distribution of this code is strictly prohibited.

"""
Utility functions for the MES optimization project.
"""

def calculate_annuity_factor(interest_rate: float, lifetime: int) -> float:
    """
    Calculates the annuity factor (also known as Capital Recovery Factor, CRF).

    This factor is used to convert a present value (like an investment cost) 
    into a series of equal annual payments over a given number of years,
    at a specified interest rate.

    Args:
        interest_rate: The annual interest rate (e.g., 0.08 for 8%).
        lifetime: The lifetime of the asset in years.

    Returns:
        The annuity factor.
    """
    if lifetime == 0:
        return 1 # Avoid division by zero; implies full cost is borne in one year
    if interest_rate == 0:
        return 1 / lifetime
        
    i = interest_rate
    n = lifetime
    return (i * (1 + i)**n) / ((1 + i)**n - 1)

print("Utility file 'utils.py' created successfully.")