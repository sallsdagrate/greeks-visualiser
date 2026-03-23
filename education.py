from __future__ import annotations

OPTION_INPUT_GUIDE = [
    {
        "symbol": "S",
        "label": "Spot price",
        "plain_english": "The current price of the underlying asset today.",
        "where_from": "Observed directly in the market or chosen as the starting point in a model.",
        "math_role": "Appears in the log-moneyness term ln(S / K) and scales the option's exposure.",
        "desk_note": "Spot relative to strike determines whether the option is ITM, ATM, or OTM.",
    },
    {
        "symbol": "K",
        "label": "Strike price",
        "plain_english": "The fixed exercise price written into the option contract.",
        "where_from": "Set by the listed contract specification or negotiated OTC terms.",
        "math_role": "Defines the payoff kink and enters both the payoff and discount term.",
        "desk_note": "Strike is the contract's reference level, not a market forecast.",
    },
    {
        "symbol": "sigma",
        "label": "Volatility",
        "plain_english": "The annualized standard deviation used by the pricing model.",
        "where_from": "In practice traders often infer it from market prices as implied volatility; in a model it can be assumed directly.",
        "math_role": "Controls the dispersion of future prices and enters through sigma * sqrt(T).",
        "desk_note": "Higher volatility generally lifts both call and put premiums because optionality becomes more valuable.",
    },
    {
        "symbol": "T",
        "label": "Time to maturity",
        "plain_english": "How much time remains until expiration, measured in years.",
        "where_from": "Derived from the expiration date minus today's date, expressed on an annual basis.",
        "math_role": "Scales both the drift and diffusion terms in the model.",
        "desk_note": "More time usually means more time value, but it also changes the shape of the Greeks.",
    },
    {
        "symbol": "r",
        "label": "Risk-free rate",
        "plain_english": "The financing rate used to discount the strike and form the risk-neutral drift.",
        "where_from": "Approximated from government curves, OIS curves, or a simplified constant input in a toy model.",
        "math_role": "Appears in the discounted strike K * exp(-rT) and in the carry term of d1.",
        "desk_note": "Rho is often small for short-dated equity options but matters more for long-dated contracts or rate-sensitive products.",
    },
]

BLACK_SCHOLES_ASSUMPTIONS = [
    "The underlying follows a continuous stochastic process that leads to lognormal prices in the model.",
    "Volatility and the risk-free rate are treated as constant over the life of the option.",
    "The classic closed-form solution is for European exercise, meaning exercise happens only at expiry.",
    "The frictionless textbook setup assumes continuous trading, no transaction costs, and no arbitrage.",
    "The model gives a theoretical fair value under its assumptions; the traded market premium can differ.",
]

GREEK_GUIDE = [
    {
        "name": "Delta",
        "math": "dV / dS",
        "plain_english": "First-order sensitivity of option value to the underlying price.",
        "desk_use": "Often used as a hedge ratio for small spot moves.",
        "watch": "Delta changes as spot, time, and volatility move, so a hedge based only on Delta can drift quickly.",
    },
    {
        "name": "Gamma",
        "math": "d^2V / dS^2",
        "plain_english": "Sensitivity of Delta to the underlying price.",
        "desk_use": "Measures convexity and how quickly your hedge ratio changes.",
        "watch": "Gamma is often largest near the strike and close to expiry.",
    },
    {
        "name": "Vega",
        "math": "dV / d sigma",
        "plain_english": "Sensitivity of option value to implied volatility.",
        "desk_use": "Tracks exposure to repricing of uncertainty rather than direction alone.",
        "watch": "In trading jargon, volatility is often quoted in vol points, so a move from 20% to 21% is a one-point move.",
    },
    {
        "name": "Theta",
        "math": "time sensitivity",
        "plain_english": "Sensitivity of option value to the passage of time.",
        "desk_use": "Explains time decay for long options and time carry for short options.",
        "watch": "Market tools often quote theta per day, while models may use annualized units. Always check the convention.",
    },
    {
        "name": "Rho",
        "math": "dV / dr",
        "plain_english": "Sensitivity of option value to interest rates.",
        "desk_use": "Usually a second-order concern for short-dated equity options, but more relevant for long-dated or rate-linked products.",
        "watch": "Calls and puts usually have opposite-sign rho under standard assumptions.",
    },
]

EXERCISE_STYLE_COMPARISON = [
    {
        "topic": "Exercise timing",
        "european": "Can be exercised only at expiration.",
        "american": "Can be exercised at any time up to and including expiration.",
    },
    {
        "topic": "Short-position assignment risk",
        "european": "No early assignment; assignment happens at expiry.",
        "american": "Early assignment is possible before expiry.",
    },
    {
        "topic": "Typical pricing approach",
        "european": "Classic Black-Scholes closed form applies in the textbook setting.",
        "american": "Often priced numerically because early exercise changes the problem.",
    },
    {
        "topic": "Common examples",
        "european": "Many index-style or futures-style options.",
        "american": "Many standard U.S. equity options.",
    },
]

JUNIOR_TRADER_NOTES = [
    {
        "title": "Premium is not just payoff",
        "body": "An option can trade above immediate exercise value because it still has time and uncertainty remaining. That extra amount is time value or extrinsic value.",
    },
    {
        "title": "Spot, volatility, time, and rates all matter at once",
        "body": "An option is a multi-factor instrument. Even if your directional view is right, the premium can move against you if implied volatility falls or time decay dominates.",
    },
    {
        "title": "Long optionality buys convexity",
        "body": "Long options usually lose carry over time, but they gain nonlinear upside in large moves. Short options collect carry but take convexity and assignment risk.",
    },
    {
        "title": "ATM options concentrate risk",
        "body": "At-the-money options tend to have large gamma, theta, and vega, especially as expiry approaches. That is why near-strike positions can become unstable quickly.",
    },
    {
        "title": "Implied volatility is a market quote",
        "body": "Historical volatility is backward-looking. Implied volatility is the volatility consistent with today's traded option premium and is therefore a market-implied number.",
    },
    {
        "title": "Contract specs still matter",
        "body": "A junior trader should always check contract multiplier, settlement style, exercise style, ex-dividend dates, and whether the product is cash- or physically-settled.",
    },
]

LEARNING_CHECKS = [
    {
        "question": "If Delta is 0.60, what is the first-order estimate for a $1 increase in spot?",
        "options": [
            "About +$0.60 in option value",
            "About +$1.60 in option value",
            "No change in option value",
            "About -$0.60 in option value",
        ],
        "answer": "About +$0.60 in option value",
        "explanation": "Delta is the local first derivative with respect to spot, so a small $1 move maps to about Delta times $1.",
    },
    {
        "question": "What does a positive Vega mean?",
        "options": [
            "The option gains value when implied volatility rises",
            "The option gains value when rates fall",
            "The option gains value when time passes",
            "The option gains value only if it finishes ITM",
        ],
        "answer": "The option gains value when implied volatility rises",
        "explanation": "Vega measures sensitivity to implied volatility, not to direction, rates, or final exercise alone.",
    },
    {
        "question": "Which style assumption is built into the classic Black-Scholes closed form?",
        "options": [
            "European exercise",
            "American exercise",
            "Bermudan exercise",
            "Path-dependent exercise",
        ],
        "answer": "European exercise",
        "explanation": "The textbook Black-Scholes formula assumes the option can be exercised only at expiry.",
    },
]

SOURCE_LIBRARY = [
    {
        "title": "Options Pricing",
        "url": "https://www.optionseducation.org/optionsoverview/options-pricing",
        "publisher": "Options Industry Council",
        "why": "Premium decomposition, intrinsic value, time value, and the main premium drivers.",
    },
    {
        "title": "Black-Scholes Formula",
        "url": "https://www.optionseducation.org/advancedconcepts/black-scholes-formula",
        "publisher": "Options Industry Council",
        "why": "Model inputs, European exercise context, and practical limits of the formula.",
    },
    {
        "title": "Volatility & the Greeks",
        "url": "https://www.optionseducation.org/advancedconcepts/volatility-the-greeks",
        "publisher": "Options Industry Council",
        "why": "Compact definitions of Gamma, Vega, Theta, and Rho from an options-education source.",
    },
    {
        "title": "What is the Difference Between American-style and European-style Options?",
        "url": "https://www.optionseducation.org/news/what-is-the-difference-between-american-style-and",
        "publisher": "Options Industry Council",
        "why": "Exercise-style difference, U.S. index-style context, and the Black-Scholes connection.",
    },
    {
        "title": "Option Exercise and Assignment",
        "url": "https://www.optionseducation.org/videolibrary/option-exercise-and-assignment",
        "publisher": "Options Industry Council",
        "why": "Rights and obligations of buyers versus sellers, plus assignment process context.",
    },
    {
        "title": "Understanding the Difference: European vs. American Style Options",
        "url": "https://www.cmegroup.com/education/courses/introduction-to-options/understanding-the-difference-european-vs-american-style-options",
        "publisher": "CME Group",
        "why": "Concise exercise-style comparison from an exchange education source.",
    },
    {
        "title": "Option Greeks",
        "url": "https://www.cmegroup.com/education/courses/option-greeks.html",
        "publisher": "CME Group",
        "why": "Overview of why Greeks exist and which risk factors move option prices.",
    },
    {
        "title": "Glossary: Black-Scholes Option Pricing Model",
        "url": "https://www.cmegroup.com/education/glossary.html",
        "publisher": "CME Group",
        "why": "Model definition and the lognormal-price assumption.",
    },
]
