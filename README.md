# Options Payoff & Greeks Visualiser

A compact Streamlit app for exploring European option payoffs and Black-Scholes sensitivities, extended with guided learning pages for beginners who are mathematically comfortable but new to options. The project is designed as a small quantitative finance portfolio piece: lightweight, mathematically grounded, source-backed, and structured like a real application rather than a notebook or monolithic script.

## Project Overview

This app lets you:

- Price European calls and puts with the Black-Scholes model
- Visualise expiry payoff profiles for long and short option positions
- Inspect the five main analytical Greeks across a range of underlying prices
- Explore how spot, strike, volatility, rates, and maturity change the shape of the option profile
- Learn where the model variables come from, how payoffs are constructed, and how traders talk about options in practice

## Features

- Black-Scholes pricing for European call and put options
- Analytical Delta, Gamma, Vega, Theta, and Rho
- Expiry payoff charts for:
  - Long call
  - Short call
  - Long put
  - Short put
- Interactive Streamlit controls for core model inputs
- Clean Plotly visualisations for payoff, theoretical value, and Greeks
- Vectorised NumPy implementation with edge-case handling for very small maturity and volatility
- Guided learning sections for:
  - Option basics and payoff construction
  - Variable origins and model inputs
  - Black-Scholes formula anatomy and assumptions
  - European vs American exercise styles
  - Junior-trader notes and quick self-checks
- Source-backed educational content with links to OIC and CME references

## Screenshots

### Overview

![Overview](assets/screenshots/app-overview.png)

### Payoff And Desk Notes

![Payoff and desk notes](assets/screenshots/payoff-desk-notes.png)

### Greeks Panel

![Greeks panel](assets/screenshots/greeks-panel.png)

## Learning Mode

The app now includes multiple sections in the sidebar:

- `Explorer`: the desk-style view for payoff, premium, and Greeks
- `Option Basics`: explains contract rights, payoff formulas, intrinsic value, and time value
- `Black-Scholes Lab`: breaks down `d1`, `d2`, model assumptions, and one-factor sensitivity sweeps
- `Exercise Styles`: compares European and American options, assignment risk, and why early exercise changes pricing
- `Junior Trader Notes`: introduces desk intuition, Greek interpretation, and interactive self-checks
- `Sources`: lists the external references used to support the educational content

## Tech Stack

- Python
- NumPy
- SciPy
- Plotly
- Streamlit

## Black-Scholes Model Summary

For spot price `S`, strike `K`, volatility `sigma`, risk-free rate `r`, and time to maturity `T`:

```text
d1 = [ln(S / K) + (r + 0.5 * sigma^2) * T] / (sigma * sqrt(T))
d2 = d1 - sigma * sqrt(T)
```

European call and put prices are:

```text
Call = S * N(d1) - K * exp(-rT) * N(d2)
Put  = K * exp(-rT) * N(-d2) - S * N(-d1)
```

where `N(.)` is the standard normal CDF.

For very small `T` or `sigma`, the implementation switches to stable limiting cases instead of forcing the standard formulas through numerically unstable inputs.

## What Each Greek Represents

- `Delta`: sensitivity of the option value to a small change in the underlying price
- `Gamma`: sensitivity of Delta to a small change in the underlying price
- `Vega`: sensitivity of the option value to a change in implied volatility
- `Theta`: sensitivity of the option value to the passage of time
- `Rho`: sensitivity of the option value to a change in the risk-free rate

## European vs American Options

- `European`: exercise is allowed only at expiry
- `American`: exercise is allowed at any time up to expiry
- The classic Black-Scholes closed form is a European-option model
- American exercise adds flexibility and often requires numerical pricing methods
- For short positions, early assignment is an operational risk on American-style products

## Project Structure

```text
.
├── assets/
│   └── screenshots/
│       ├── app-overview.png
│       ├── greeks-panel.png
│       └── payoff-desk-notes.png
├── app.py
├── education.py
├── greeks.py
├── payoff.py
├── pricing.py
├── requirements.txt
├── utils.py
└── README.md
```

## How To Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Launch the app:

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in your terminal.

## Example Use Cases

- Compare the asymmetric payoff of a long call against the capped profile of a short call
- See how Gamma and Vega concentrate around the strike as expiry approaches
- Observe the effect of higher rates on call versus put Rho
- Inspect how Theta changes when an option moves from out-of-the-money to at-the-money
- Learn how `S`, `K`, `sigma`, `T`, and `r` enter the Black-Scholes formula
- Teach a beginner the difference between intrinsic value, time value, and model premium
- Explain to a junior trader why European vs American exercise changes both pricing and assignment risk

## Limitations

- European exercise only
- Constant volatility assumption
- Constant risk-free rate
- No dividends or carry adjustments
- Black-Scholes assumptions may not match real market microstructure or volatility smiles

## Future Improvements

- Multi-leg strategies and spreads
- Implied volatility solver and smile visualisation
- Monte Carlo pricing for path-dependent or non-closed-form products

## References And Further Reading

- Options Industry Council, `Options Pricing`:
  https://www.optionseducation.org/optionsoverview/options-pricing
- Options Industry Council, `Black-Scholes Formula`:
  https://www.optionseducation.org/advancedconcepts/black-scholes-formula
- Options Industry Council, `Volatility & the Greeks`:
  https://www.optionseducation.org/advancedconcepts/volatility-the-greeks
- Options Industry Council, `What is the Difference Between American-style and European-style Options?`:
  https://www.optionseducation.org/news/what-is-the-difference-between-american-style-and
- Options Industry Council, `Option Exercise and Assignment`:
  https://www.optionseducation.org/videolibrary/option-exercise-and-assignment
- CME Group, `Understanding the Difference: European vs. American Style Options`:
  https://www.cmegroup.com/education/courses/introduction-to-options/understanding-the-difference-european-vs-american-style-options
- CME Group, `Option Greeks`:
  https://www.cmegroup.com/education/courses/option-greeks.html
- CME Group, `Glossary: Black-Scholes Option Pricing Model`:
  https://www.cmegroup.com/education/glossary.html
