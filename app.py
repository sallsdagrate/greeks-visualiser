from __future__ import annotations

from html import escape

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from education import (
    BLACK_SCHOLES_ASSUMPTIONS,
    EXERCISE_STYLE_COMPARISON,
    GREEK_GUIDE,
    JUNIOR_TRADER_NOTES,
    LEARNING_CHECKS,
    OPTION_INPUT_GUIDE,
    SOURCE_LIBRARY,
)
from greeks import analytical_greeks
from payoff import option_payoff
from pricing import black_scholes_price
from utils import EPSILON, compute_d1_d2, create_price_grid, discounted_strike, position_sign

APP_BG = "#050909"
PANEL_BG = "#0a1513"
PANEL_ALT = "#0d1b18"
PANEL_BORDER = "#173530"
TEXT = "#e6fff8"
MUTED = "#84a79f"
PRIMARY = "#53f3a6"
ACCENT = "#4dd5ff"
AMBER = "#f7b955"
NEGATIVE = "#ff6b6b"
NEUTRAL = "#a8c1bb"
GRID = "#1b3933"
FONT_STACK = "'IBM Plex Mono', 'SFMono-Regular', Menlo, Monaco, Consolas, monospace"

SECTIONS = [
    "Explorer",
    "Option Basics",
    "Black-Scholes Lab",
    "Exercise Styles",
    "Junior Trader Notes",
    "Sources",
]


def main() -> None:
    st.set_page_config(
        page_title="Options Payoff & Greeks Visualiser",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_styles()

    sidebar_state = _render_sidebar()
    context = _build_context(
        spot=sidebar_state["spot"],
        strike=sidebar_state["strike"],
        rate=sidebar_state["rate"],
        volatility=sidebar_state["volatility"],
        maturity=sidebar_state["maturity"],
        option_type=sidebar_state["option_type"],
        position_type=sidebar_state["position_type"],
    )

    section = sidebar_state["section"]
    if section == "Explorer":
        _render_explorer(context)
    elif section == "Option Basics":
        _render_option_basics(context)
    elif section == "Black-Scholes Lab":
        _render_black_scholes_lab(context)
    elif section == "Exercise Styles":
        _render_exercise_styles(context)
    elif section == "Junior Trader Notes":
        _render_junior_trader_notes(context)
    else:
        _render_sources_page(context)


def _render_sidebar() -> dict[str, object]:
    """Collect the navigation state and model inputs from the sidebar."""
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-shell">
                <div class="sidebar-kicker">Learning Terminal</div>
                <h2>Model Deck</h2>
                <p>
                    Use the same contract inputs across all sections. The explorer behaves like a desk tool,
                    while the other sections turn the model into a guided learning app.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        section = st.radio("Section", options=SECTIONS, index=0)

        st.markdown("### Contract Inputs")
        spot = st.number_input("Spot price", min_value=0.01, value=100.0, step=1.0)
        strike = st.number_input("Strike price", min_value=0.01, value=100.0, step=1.0)
        volatility = (
            st.slider("Volatility (%)", min_value=0.0, max_value=150.0, value=20.0, step=0.5)
            / 100.0
        )
        maturity = st.slider(
            "Time to maturity (years)",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.05,
        )
        rate = (
            st.slider(
                "Risk-free rate (%)",
                min_value=-5.0,
                max_value=15.0,
                value=5.0,
                step=0.1,
            )
            / 100.0
        )
        option_type = st.radio("Option type", options=["call", "put"], horizontal=True)
        position_type = st.radio("Position type", options=["long", "short"], horizontal=True)

        st.markdown(
            """
            <div class="sidebar-footnote">
                The learning sections explain the variables in the Black-Scholes model. Greeks here are annualized,
                while many desks quote theta per day and volatility in vol points.
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "section": section,
        "spot": spot,
        "strike": strike,
        "volatility": volatility,
        "maturity": maturity,
        "rate": rate,
        "option_type": option_type,
        "position_type": position_type,
    }


def _build_context(
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
    option_type: str,
    position_type: str,
) -> dict[str, object]:
    """Build all model quantities once so every page reads from the same scenario."""
    position_multiplier = position_sign(position_type)
    price_grid = create_price_grid(spot, strike)

    option_value = float(
        black_scholes_price(spot, strike, rate, volatility, maturity, option_type)
    )
    value_curve = np.asarray(
        black_scholes_price(price_grid, strike, rate, volatility, maturity, option_type)
    )
    payoff_curve = np.asarray(option_payoff(price_grid, strike, option_type, position_type))

    greek_snapshot = analytical_greeks(spot, strike, rate, volatility, maturity, option_type)
    greek_curves = analytical_greeks(price_grid, strike, rate, volatility, maturity, option_type)
    signed_snapshot = {
        greek_name: position_multiplier * float(greek_value)
        for greek_name, greek_value in greek_snapshot.items()
    }
    signed_greek_curves = {
        greek_name: position_multiplier * np.asarray(greek_value)
        for greek_name, greek_value in greek_curves.items()
    }

    intrinsic_now = _intrinsic_value(spot, strike, option_type)
    extrinsic_now = max(option_value - intrinsic_now, 0.0)
    regime = _classify_moneyness(spot, strike, option_type)
    pricing_mode = _pricing_mode(volatility, maturity)

    d1_value: float | None = None
    d2_value: float | None = None
    log_moneyness: float | None = None
    carry_term: float | None = None
    sigma_sqrt_t: float | None = None

    if maturity > EPSILON and volatility > EPSILON:
        d1_array, d2_array = compute_d1_d2(
            np.asarray([spot], dtype=float),
            strike,
            rate,
            volatility,
            maturity,
        )
        d1_value = float(d1_array[0])
        d2_value = float(d2_array[0])
        log_moneyness = float(np.log(spot / strike))
        carry_term = float((rate + 0.5 * volatility**2) * maturity)
        sigma_sqrt_t = float(volatility * np.sqrt(maturity))

    return {
        "spot": spot,
        "strike": strike,
        "rate": rate,
        "volatility": volatility,
        "maturity": maturity,
        "option_type": option_type,
        "position_type": position_type,
        "position_multiplier": position_multiplier,
        "price_grid": price_grid,
        "option_value": option_value,
        "value_curve": value_curve,
        "payoff_curve": payoff_curve,
        "greek_snapshot": greek_snapshot,
        "greek_curves": greek_curves,
        "signed_snapshot": signed_snapshot,
        "signed_greek_curves": signed_greek_curves,
        "signed_option_value": position_multiplier * option_value,
        "signed_value_curve": position_multiplier * value_curve,
        "regime": regime,
        "pricing_mode": pricing_mode,
        "moneyness": spot / strike,
        "break_even": _break_even_price(strike, option_value, option_type),
        "discounted_strike": discounted_strike(strike, rate, maturity),
        "intrinsic_now": intrinsic_now,
        "extrinsic_now": extrinsic_now,
        "d1": d1_value,
        "d2": d2_value,
        "log_moneyness": log_moneyness,
        "carry_term": carry_term,
        "sigma_sqrt_t": sigma_sqrt_t,
    }


def _render_explorer(context: dict[str, object]) -> None:
    """Desk-style explorer for users who already know the model."""
    st.markdown(
        _build_banner(
            kicker="Terminal Research / Explorer",
            title="Options Payoff & Greeks Visualiser",
            subtitle=(
                "Desk-style valuation view for the selected contract. If you are new to options, "
                "switch to the learning sections in the left deck."
            ),
            badges=[
                ("BLACK-SCHOLES", "cyan"),
                ("EUROPEAN MODEL", "neutral"),
                (f"{str(context['position_type']).upper()} {str(context['option_type']).upper()}", "green" if context["position_type"] == "long" else "red"),
                (str(context["regime"]), "amber"),
                (str(context["pricing_mode"]), "neutral"),
            ],
            command_line=(
                f"EXPLORE S={context['spot']:.2f} K={context['strike']:.2f} "
                f"SIGMA={context['volatility'] * 100:.2f}% R={context['rate'] * 100:.2f}% "
                f"T={context['maturity']:.2f}Y"
            ),
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="page-orientation">
            <span><strong>Explorer</strong> is the trader view.</span>
            <span><strong>Option Basics</strong> explains payoffs and moneyness.</span>
            <span><strong>Black-Scholes Lab</strong> breaks down the formula and variables.</span>
            <span><strong>Exercise Styles</strong> covers European versus American exercise.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_metric_grid(
        [
            ("Position value", float(context["signed_option_value"]), ACCENT),
            ("Delta", float(context["signed_snapshot"]["delta"]), PRIMARY),
            ("Gamma", float(context["signed_snapshot"]["gamma"]), ACCENT),
            ("Vega", float(context["signed_snapshot"]["vega"]), AMBER),
            ("Theta", float(context["signed_snapshot"]["theta"]), NEGATIVE),
            ("Rho", float(context["signed_snapshot"]["rho"]), NEUTRAL),
        ]
    )

    left_column, right_column = st.columns((1.35, 0.65), gap="large")
    with left_column:
        st.markdown(
            _panel_header(
                kicker="Payoff Trace",
                title="Expiry Profile vs Theoretical Mark",
                subtitle="Terminal payoff is shown against the current Black-Scholes value curve for the selected position.",
            ),
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            _build_payoff_figure(
                price_grid=np.asarray(context["price_grid"]),
                payoff_curve=np.asarray(context["payoff_curve"]),
                value_curve=np.asarray(context["signed_value_curve"]),
                spot=float(context["spot"]),
                strike=float(context["strike"]),
                position_type=str(context["position_type"]),
            ),
            width="stretch",
        )

    with right_column:
        st.markdown(
            _panel_header(
                kicker="Desk Notes",
                title="Research Summary",
                subtitle="Compact diagnostics for screenshots and quick interpretation.",
            ),
            unsafe_allow_html=True,
        )
        _render_notes_panel(context)

    st.markdown(
        _panel_header(
            kicker="Risk Sheet",
            title="Greeks Across The Underlying Path",
            subtitle="Sensitivities are shown with the sign of the selected position, so short options invert the long-risk profile.",
        ),
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        _build_greeks_figure(
            price_grid=np.asarray(context["price_grid"]),
            greek_curves=context["signed_greek_curves"],
            spot=float(context["spot"]),
        ),
        width="stretch",
    )


def _render_option_basics(context: dict[str, object]) -> None:
    """Beginner page that starts from contract rights and expiry payoffs."""
    st.markdown(
        _build_banner(
            kicker="Learning Mode / Option Basics",
            title="Start With The Contract, Not The Formula",
            subtitle=(
                "A trader first understands the rights and obligations in the option contract, then layers on pricing. "
                "This page explains what the current selection means in plain English."
            ),
            badges=[
                ("PAYOFFS", "green"),
                ("MONEYNESS", "amber"),
                ("VARIABLES", "cyan"),
            ],
            command_line=(
                f"BASICS {str(context['position_type']).upper()} {str(context['option_type']).upper()} "
                f"AT K={context['strike']:.2f} WITH S={context['spot']:.2f}"
            ),
        ),
        unsafe_allow_html=True,
    )

    summary_column, sandbox_column = st.columns((1.05, 0.95), gap="large")

    with summary_column:
        st.markdown(
            _panel_header(
                kicker="Plain English",
                title="What This Position Means",
                subtitle="The contract language is the starting point for every later formula.",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _learning_card(
                "Contract Summary",
                _position_plain_english(context),
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _learning_card(
                "Intrinsic And Time Value",
                (
                    f"Using the current spot as a reference point, the option's immediate exercise value is "
                    f"{context['intrinsic_now']:.4f} and the remaining time value is {context['extrinsic_now']:.4f}. "
                    "That extra value exists because the contract still has time and uncertainty left."
                ),
            ),
            unsafe_allow_html=True,
        )

    with sandbox_column:
        st.markdown(
            _panel_header(
                kicker="Expiry Sandbox",
                title="Payoff At A Chosen Terminal Price",
                subtitle="Move the terminal underlying price and see how expiry payoff differs from today's premium.",
            ),
            unsafe_allow_html=True,
        )
        terminal_spot = st.slider(
            "Terminal underlying price at expiry",
            min_value=float(np.asarray(context["price_grid"])[0]),
            max_value=float(np.asarray(context["price_grid"])[-1]),
            value=float(context["spot"]),
            step=0.5,
        )
        include_premium = st.checkbox("Include today's model premium to show net expiry P&L", value=True)
        expiry_payoff = float(
            option_payoff(
                terminal_spot,
                float(context["strike"]),
                str(context["option_type"]),
                str(context["position_type"]),
            )
        )
        expiry_pnl = expiry_payoff - float(context["signed_option_value"])
        sandbox_metrics = [
            ("Terminal spot", terminal_spot, NEUTRAL),
            ("Expiry payoff", expiry_payoff, PRIMARY if expiry_payoff >= 0 else NEGATIVE),
            (
                "Net expiry P&L" if include_premium else "Current premium",
                expiry_pnl if include_premium else float(context["signed_option_value"]),
                ACCENT if (expiry_pnl if include_premium else float(context["signed_option_value"])) >= 0 else NEGATIVE,
            ),
        ]
        _render_metric_grid(sandbox_metrics, columns=3)

        st.latex(r"\text{Call payoff at expiry} = \max(S_T - K, 0)")
        st.latex(r"\text{Put payoff at expiry} = \max(K - S_T, 0)")
        st.markdown(
            f"""
            <div class="learning-note">
                For the selected <strong>{escape(str(context['position_type']))} {escape(str(context['option_type']))}</strong>,
                the position payoff is the option payoff multiplied by +1 for a long position or -1 for a short position.
                {"This view currently subtracts today's model premium to show an expiry P&L." if include_premium else "Toggle the premium checkbox to convert payoff into a simple P&L view."}
            </div>
            """,
            unsafe_allow_html=True,
        )

    left_column, right_column = st.columns((1.05, 0.95), gap="large")
    with left_column:
        st.markdown(
            _panel_header(
                kicker="Variable Guide",
                title="Where The Inputs Come From",
                subtitle="These are the variables a junior trader or quant sees in Black-Scholes and in listed contracts.",
            ),
            unsafe_allow_html=True,
        )
        for item in OPTION_INPUT_GUIDE:
            with st.expander(f"{item['symbol']} — {item['label']}", expanded=item["symbol"] == "S"):
                st.markdown(f"**Plain English:** {item['plain_english']}")
                st.markdown(f"**Where it comes from:** {item['where_from']}")
                st.markdown(f"**Why it enters the maths:** {item['math_role']}")
                st.markdown(f"**Desk note:** {item['desk_note']}")

    with right_column:
        st.markdown(
            _panel_header(
                kicker="Payoff Language",
                title="How Traders Read The Contract",
                subtitle="These labels appear constantly on option chains, risk screens, and trader chat.",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _learning_card(
                "Moneyness Today",
                (
                    f"With spot {context['spot']:.2f} and strike {context['strike']:.2f}, the contract is currently "
                    f"{context['regime']}. Moneyness is spot divided by strike, which here is {context['moneyness']:.4f}x."
                ),
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _learning_card(
                "Premium Today vs Payoff Later",
                (
                    f"Today's theoretical premium is {context['option_value']:.4f}. The expiry payoff depends on where spot "
                    f"finishes at expiration, so premium today and payoff later are related but not the same object."
                ),
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _learning_card(
                "Long vs Short",
                "A long option pays premium and owns the right. A short option receives premium and takes the obligation if assigned or exercised against.",
            ),
            unsafe_allow_html=True,
        )


def _render_black_scholes_lab(context: dict[str, object]) -> None:
    """Educational page for the formula, assumptions, and local sensitivities."""
    st.markdown(
        _build_banner(
            kicker="Learning Mode / Black-Scholes Lab",
            title="Connect The Payoff To The Pricing Formula",
            subtitle=(
                "Black-Scholes is a European option pricing model. This page explains where the variables enter, "
                "what d1 and d2 are doing, and how local sensitivities arise from the formula."
            ),
            badges=[
                ("FORMULA", "cyan"),
                ("D1 / D2", "amber"),
                ("NO-ARBITRAGE", "green"),
            ],
            command_line=(
                f"MODEL S={context['spot']:.2f} K={context['strike']:.2f} "
                f"SIGMA={context['volatility'] * 100:.2f}% R={context['rate'] * 100:.2f}% T={context['maturity']:.2f}Y"
            ),
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        _panel_header(
            kicker="Formula",
            title="Classic European Call And Put Values",
            subtitle="These are the long-option values in the textbook Black-Scholes model.",
        ),
        unsafe_allow_html=True,
    )
    st.latex(r"d_1 = \frac{\ln(S/K) + (r + \tfrac{1}{2}\sigma^2)T}{\sigma\sqrt{T}}")
    st.latex(r"d_2 = d_1 - \sigma\sqrt{T}")
    st.latex(r"C = S N(d_1) - K e^{-rT} N(d_2)")
    st.latex(r"P = K e^{-rT} N(-d_2) - S N(-d_1)")

    if context["d1"] is not None:
        _render_metric_grid(
            [
                ("ln(S / K)", float(context["log_moneyness"]), NEUTRAL),
                ("(r + 0.5 sigma^2)T", float(context["carry_term"]), AMBER),
                ("sigma * sqrt(T)", float(context["sigma_sqrt_t"]), PRIMARY),
                ("d1", float(context["d1"]), ACCENT),
                ("d2", float(context["d2"]), ACCENT),
            ],
            columns=5,
        )
        st.markdown(
            """
            <div class="learning-note">
                A useful intuition is that <strong>d1</strong> and <strong>d2</strong> behave like standardized moneyness terms:
                they compare where spot sits relative to strike after adjusting for time, carry, and uncertainty.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(
            "d1 and d2 are only meaningful in the standard closed-form regime. At zero time or zero volatility, "
            "the app switches to stable limiting cases instead."
        )

    formula_tab, sensitivity_tab, assumptions_tab = st.tabs(
        ["Formula Anatomy", "Sensitivity Sandbox", "Assumptions & Limits"]
    )

    with formula_tab:
        st.markdown(
            _panel_header(
                kicker="Derivation Intuition",
                title="Where The Formula Comes From",
                subtitle="This is a high-level derivation roadmap rather than a full PDE proof.",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            1. Start from the option payoff at expiry.
            2. Model the underlying with continuous-time stochastic price dynamics.
            3. Form a Delta-hedged portfolio so the instantaneous random term is cancelled.
            4. Apply no-arbitrage: a locally riskless portfolio must earn the risk-free rate.
            5. Solve the resulting pricing equation with the expiry payoff as the boundary condition.
            """
        )
        st.markdown(
            _learning_card(
                "Why The Variables Look Like They Do",
                (
                    "Log-moneyness ln(S / K) measures where spot sits relative to strike. "
                    "sigma * sqrt(T) scales uncertainty over time. The discounted strike term K * exp(-rT) appears because "
                    "future cash amounts are valued in present terms."
                ),
            ),
            unsafe_allow_html=True,
        )

    with sensitivity_tab:
        st.markdown(
            _panel_header(
                kicker="Sandbox",
                title="Move One Driver At A Time",
                subtitle="This is the cleanest way to see why each Greek exists.",
            ),
            unsafe_allow_html=True,
        )
        sweep_variable = st.selectbox(
            "Choose one model input to sweep",
            options=["Spot", "Volatility", "Time to maturity", "Risk-free rate"],
            index=0,
        )
        x_values, y_values, x_label, explanation = _parameter_sweep(context, sweep_variable)
        st.plotly_chart(
            _build_sensitivity_figure(x_values, y_values, x_label, "Long option value"),
            width="stretch",
        )
        st.markdown(
            f'<div class="learning-note">{escape(explanation)}</div>',
            unsafe_allow_html=True,
        )

        actual_change, greek_change, shocked_value, bump_label = _local_bump_demo(context, sweep_variable)
        _render_metric_grid(
            [
                ("Current value", float(context["option_value"]), ACCENT),
                ("Shocked value", shocked_value, PRIMARY if shocked_value >= float(context["option_value"]) else NEGATIVE),
                ("Actual change", actual_change, PRIMARY if actual_change >= 0 else NEGATIVE),
                ("Greek estimate", greek_change, AMBER if greek_change >= 0 else NEGATIVE),
            ],
            columns=4,
        )
        st.caption(
            f"Local approximation used in the sandbox: {bump_label}. The Greek estimate is a small-move approximation, not an exact repricing."
        )

    with assumptions_tab:
        st.markdown(
            _panel_header(
                kicker="Assumptions",
                title="Why The Model Is Useful And Why It Can Still Be Wrong",
                subtitle="A junior trader should know both the elegance of the model and its limits in live markets.",
            ),
            unsafe_allow_html=True,
        )
        for assumption in BLACK_SCHOLES_ASSUMPTIONS:
            st.markdown(f"- {assumption}")
        st.warning(
            "This app prices European options. If early exercise matters, or if volatility is not well described by a constant sigma, "
            "you need a richer model or numerical method."
        )


def _render_exercise_styles(context: dict[str, object]) -> None:
    """Learning page for exercise styles, assignment, and why the app prices only European options."""
    st.markdown(
        _build_banner(
            kicker="Learning Mode / Exercise Styles",
            title="European vs American Options",
            subtitle=(
                "The exercise rule changes both the trader's operational risk and the pricing method. "
                "This app prices European options, so understanding the difference matters."
            ),
            badges=[
                ("EUROPEAN", "amber"),
                ("AMERICAN", "cyan"),
                ("ASSIGNMENT", "red"),
            ],
            command_line=f"STYLE {context['option_type'].upper()} / {context['position_type'].upper()} POSITION",
        ),
        unsafe_allow_html=True,
    )

    st.warning(
        "The calculator in this project uses the classic European Black-Scholes setup. American exercise adds optionality, "
        "so the pricing problem usually moves beyond the closed form."
    )

    st.markdown(
        _panel_header(
            kicker="Comparison",
            title="Exercise Styles Side By Side",
            subtitle="These are the practical differences a junior trader should be able to explain.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_exercise_style_table(), unsafe_allow_html=False)
    st.caption(
        "Mathematical inference: an American option cannot be worth less than the otherwise identical European option because it includes all of the European exercise opportunities plus more."
    )

    style_column, side_column = st.columns(2)
    with style_column:
        style_choice = st.radio(
            "Choose an exercise style to reason about",
            options=["European", "American"],
            horizontal=True,
        )
    with side_column:
        side_choice = st.radio(
            "Choose your side of the contract",
            options=["Long option", "Short option"],
            horizontal=True,
        )

    st.markdown(
        _learning_card(
            "Operational Reading",
            _exercise_message(style_choice, side_choice),
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        _panel_header(
            kicker="Junior Trader Checklist",
            title="What You Should Check Before Trading",
            subtitle="This is the operational layer that sits on top of the math.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        - Check exercise style and settlement style before putting on a short option position.
        - Confirm whether the product is physically settled or cash settled.
        - Know the contract multiplier and any special deliverable adjustments.
        - Watch ex-dividend dates and carry conditions if early exercise is possible.
        - Remember that assignment risk is an operational risk, not just a pricing detail.
        """
    )


def _render_junior_trader_notes(context: dict[str, object]) -> None:
    """Learning page for desk intuition, Greek interpretation, and quick checks."""
    st.markdown(
        _build_banner(
            kicker="Learning Mode / Junior Trader Notes",
            title="Desk Intuition Beyond The Formula",
            subtitle=(
                "This page collects the mental models and fast checks that help a beginner connect option maths to trader language."
            ),
            badges=[
                ("GREEKS", "cyan"),
                ("VOLATILITY", "amber"),
                ("QUIZ", "green"),
            ],
            command_line=f"NOTES {context['option_type'].upper()} / {context['regime']} / SIGMA={context['volatility'] * 100:.2f}%",
        ),
        unsafe_allow_html=True,
    )

    left_column, right_column = st.columns((1.15, 0.85), gap="large")

    with left_column:
        st.markdown(
            _panel_header(
                kicker="Mental Models",
                title="What A Junior Trader Should Be Able To Explain",
                subtitle="These are practical explanations you should be comfortable saying out loud.",
            ),
            unsafe_allow_html=True,
        )
        for note in JUNIOR_TRADER_NOTES:
            with st.expander(note["title"], expanded=False):
                st.write(note["body"])

        st.markdown(
            _panel_header(
                kicker="Greek Glossary",
                title="How Traders Talk About Sensitivities",
                subtitle="The formulas are useful, but so is the desk language behind them.",
            ),
            unsafe_allow_html=True,
        )
        for greek in GREEK_GUIDE:
            with st.expander(greek["name"], expanded=greek["name"] == "Delta"):
                st.markdown(f"**Math label:** `{greek['math']}`")
                st.markdown(f"**Plain English:** {greek['plain_english']}")
                st.markdown(f"**Desk use:** {greek['desk_use']}")
                st.markdown(f"**Watch out for:** {greek['watch']}")

    with right_column:
        st.markdown(
            _panel_header(
                kicker="Quick Checks",
                title="Interactive Self-Test",
                subtitle="Answer a few short questions and reveal the explanation immediately.",
            ),
            unsafe_allow_html=True,
        )
        _render_learning_checks()
        st.markdown(
            _learning_card(
                "Live-Market Reminder",
                "Theoretical option value is only one layer. On a real desk you also care about bid/ask spread, contract multiplier, liquidity, settlement, dividends, and implied-volatility skew.",
            ),
            unsafe_allow_html=True,
        )


def _render_sources_page(context: dict[str, object]) -> None:
    """Source-backed reference page used by the learning sections."""
    st.markdown(
        _build_banner(
            kicker="Learning Mode / Sources",
            title="Reference Material Behind The Learning Sections",
            subtitle=(
                "The educational notes in this app combine source-backed option education with light synthesis that connects the model to junior-trader intuition."
            ),
            badges=[
                ("OIC", "green"),
                ("CME", "cyan"),
                ("REFERENCE PAGE", "neutral"),
            ],
            command_line=f"SOURCES CURRENT SCENARIO: {context['option_type'].upper()} / {context['pricing_mode']}",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="learning-note">
            Source-backed items below cover payoffs, pricing, Greeks, and exercise styles. Some pages in the app also include synthesis,
            such as explaining where traders usually obtain model inputs and how these quantities are interpreted on a desk.
        </div>
        """,
        unsafe_allow_html=True,
    )

    for source in SOURCE_LIBRARY:
        st.markdown(
            _source_card(
                title=source["title"],
                url=source["url"],
                publisher=source["publisher"],
                why=source["why"],
            ),
            unsafe_allow_html=True,
        )


def _render_metric_grid(metric_specs: list[tuple[str, float, str]], columns: int = 3) -> None:
    """Render metric cards in a fixed-width grid."""
    for start in range(0, len(metric_specs), columns):
        row_columns = st.columns(columns)
        for column, (label, value, accent_color) in zip(row_columns, metric_specs[start : start + columns]):
            column.markdown(
                _metric_card(label=label, value=value, accent_color=accent_color),
                unsafe_allow_html=True,
            )


def _render_notes_panel(context: dict[str, object]) -> None:
    """Render compact setup diagnostics and reading notes for the current scenario."""
    rows = [
        ("POSITION", f"{str(context['position_type']).upper()} {str(context['option_type']).upper()}"),
        ("REGIME", str(context["regime"])),
        ("MODEL MARK", _format_metric(float(context["option_value"]))),
        ("BREAK-EVEN", f"{float(context['break_even']):,.4f}"),
        ("MONEYNESS", f"{float(context['moneyness']):.4f}x"),
        ("PV STRIKE", f"{float(context['discounted_strike']):,.4f}"),
        (
            "GRID WINDOW",
            f"{float(np.asarray(context['price_grid'])[0]):,.2f} -> {float(np.asarray(context['price_grid'])[-1]):,.2f}",
        ),
        ("ENGINE", str(context["pricing_mode"])),
    ]

    st.markdown('<div class="notes-subtitle">Setup Snapshot</div>', unsafe_allow_html=True)
    for key, value in rows:
        left, right = st.columns((0.95, 1.05), gap="small")
        left.markdown(
            f'<div class="notes-key">{escape(key)}</div>',
            unsafe_allow_html=True,
        )
        right.markdown(
            f'<div class="notes-value">{escape(value)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="notes-divider"></div>', unsafe_allow_html=True)
    notes = [
        "Theta is annualised in this app.",
        "Vega and rho are quoted per 1.00 change in volatility and rates.",
        "Short positions invert the long Greeks and value curve.",
        "Move to the learning sections for formula and contract explanations.",
    ]
    st.markdown('<div class="notes-subtitle">Read Notes</div>', unsafe_allow_html=True)
    for note in notes:
        st.markdown(
            f'<div class="notes-note"><span class="notes-prompt">&gt;</span>{escape(note)}</div>',
            unsafe_allow_html=True,
        )


def _render_learning_checks() -> None:
    """Small self-test for beginners using radios and immediate feedback."""
    for index, check in enumerate(LEARNING_CHECKS):
        st.markdown(
            f'<div class="quiz-question">{index + 1}. {escape(check["question"])}</div>',
            unsafe_allow_html=True,
        )
        answer = st.radio(
            label=f"Question {index + 1}",
            options=check["options"],
            index=None,
            key=f"learning_check_{index}",
            label_visibility="collapsed",
        )
        if answer is None:
            continue
        if answer == check["answer"]:
            st.success(check["explanation"])
        else:
            st.error(f"Not quite. {check['explanation']}")


def _build_payoff_figure(
    price_grid: np.ndarray,
    payoff_curve: np.ndarray,
    value_curve: np.ndarray,
    spot: float,
    strike: float,
    position_type: str,
) -> go.Figure:
    """Build the main pricing view: terminal payoff versus current model value."""
    payoff_color = PRIMARY if position_type == "long" else NEGATIVE
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=price_grid,
            y=value_curve,
            mode="lines",
            name="Model value",
            line={"color": ACCENT, "width": 2.4},
            hovertemplate="Underlying=%{x:.2f}<br>Model value=%{y:.4f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=price_grid,
            y=payoff_curve,
            mode="lines",
            name="Expiry payoff",
            line={"color": payoff_color, "width": 3},
            fill="tozeroy",
            fillcolor=_rgba(payoff_color, 0.16),
            hovertemplate="Underlying=%{x:.2f}<br>Expiry payoff=%{y:.4f}<extra></extra>",
        )
    )
    figure.add_hline(y=0.0, line_dash="dot", line_color=NEUTRAL, line_width=1)
    figure.add_vline(x=strike, line_dash="dash", line_color=AMBER, line_width=1.1)
    figure.add_vline(x=spot, line_dash="dot", line_color=ACCENT, line_width=1.1)
    figure.add_annotation(
        x=strike,
        y=1.0,
        yref="paper",
        text="STRIKE",
        showarrow=False,
        font={"size": 10, "color": AMBER, "family": FONT_STACK},
        bgcolor=_rgba(PANEL_BG, 0.85),
        bordercolor=_rgba(AMBER, 0.45),
        borderpad=4,
    )
    figure.add_annotation(
        x=spot,
        y=1.08,
        yref="paper",
        text="SPOT",
        showarrow=False,
        font={"size": 10, "color": ACCENT, "family": FONT_STACK},
        bgcolor=_rgba(PANEL_BG, 0.85),
        bordercolor=_rgba(ACCENT, 0.45),
        borderpad=4,
    )
    _apply_chart_theme(figure)
    figure.update_layout(
        margin={"l": 18, "r": 18, "t": 18, "b": 18},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
            "bgcolor": "rgba(0,0,0,0)",
        },
    )
    figure.update_xaxes(title="Underlying price", gridcolor=GRID, zeroline=False)
    figure.update_yaxes(title="Position value", gridcolor=GRID, zeroline=False)
    return figure


def _build_greeks_figure(
    price_grid: np.ndarray,
    greek_curves: dict[str, np.ndarray],
    spot: float,
) -> go.Figure:
    """Render the five analytical Greeks on a shared underlying-price axis."""
    greek_specs = [
        ("delta", "Delta", PRIMARY, 1, 1),
        ("gamma", "Gamma", ACCENT, 1, 2),
        ("vega", "Vega", AMBER, 2, 1),
        ("theta", "Theta", NEGATIVE, 2, 2),
        ("rho", "Rho", NEUTRAL, 3, 1),
    ]

    figure = make_subplots(
        rows=3,
        cols=2,
        specs=[[{}, {}], [{}, {}], [{"colspan": 2}, None]],
        subplot_titles=[label.upper() for _, label, _, _, _ in greek_specs],
        vertical_spacing=0.11,
        horizontal_spacing=0.08,
    )

    for greek_name, label, color, row, col in greek_specs:
        figure.add_trace(
            go.Scatter(
                x=price_grid,
                y=greek_curves[greek_name],
                mode="lines",
                name=label,
                line={"color": color, "width": 2.35},
                showlegend=False,
                hovertemplate=f"Underlying=%{{x:.2f}}<br>{label}=%{{y:.4f}}<extra></extra>",
            ),
            row=row,
            col=col,
        )
        figure.add_hline(y=0.0, line_dash="dot", line_color=GRID, line_width=1, row=row, col=col)
        figure.add_vline(x=spot, line_dash="dot", line_color=ACCENT, line_width=1, row=row, col=col)
        figure.update_yaxes(title=label, gridcolor=GRID, zeroline=False, row=row, col=col)
        figure.update_xaxes(title="Underlying price", gridcolor=GRID, zeroline=False, row=row, col=col)

    _apply_chart_theme(figure)
    figure.update_layout(
        margin={"l": 18, "r": 18, "t": 22, "b": 18},
        height=860,
    )
    figure.update_annotations(font={"size": 11, "color": MUTED, "family": FONT_STACK})
    return figure


def _build_sensitivity_figure(
    x_values: np.ndarray,
    y_values: np.ndarray,
    x_label: str,
    y_label: str,
) -> go.Figure:
    """Single-factor sensitivity plot used by the learning sandbox."""
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines",
            line={"color": ACCENT, "width": 2.5},
            hovertemplate=f"{x_label}=%{{x:.4f}}<br>{y_label}=%{{y:.4f}}<extra></extra>",
            name=y_label,
        )
    )
    _apply_chart_theme(figure)
    figure.update_layout(margin={"l": 18, "r": 18, "t": 18, "b": 18}, showlegend=False)
    figure.update_xaxes(title=x_label, gridcolor=GRID, zeroline=False)
    figure.update_yaxes(title=y_label, gridcolor=GRID, zeroline=False)
    return figure


def _apply_chart_theme(figure: go.Figure) -> None:
    """Apply one consistent terminal-style theme across all Plotly figures."""
    figure.update_layout(
        template=None,
        paper_bgcolor=PANEL_BG,
        plot_bgcolor=PANEL_ALT,
        font={"family": FONT_STACK, "color": TEXT, "size": 12},
        hovermode="x unified",
        hoverlabel={
            "bgcolor": PANEL_BG,
            "bordercolor": PANEL_BORDER,
            "font": {"family": FONT_STACK, "color": TEXT},
        },
    )
    figure.update_xaxes(
        showline=True,
        linewidth=1,
        linecolor=PANEL_BORDER,
        mirror=False,
        tickfont={"color": MUTED},
        title_font={"color": MUTED},
    )
    figure.update_yaxes(
        showline=True,
        linewidth=1,
        linecolor=PANEL_BORDER,
        mirror=False,
        tickfont={"color": MUTED},
        title_font={"color": MUTED},
    )


def _parameter_sweep(
    context: dict[str, object], variable: str
) -> tuple[np.ndarray, np.ndarray, str, str]:
    """Create a one-factor price curve for the learning sandbox."""
    strike = float(context["strike"])
    spot = float(context["spot"])
    rate = float(context["rate"])
    volatility = float(context["volatility"])
    maturity = float(context["maturity"])
    option_type = str(context["option_type"])

    if variable == "Spot":
        x_values = np.asarray(context["price_grid"])
        y_values = np.asarray(
            black_scholes_price(x_values, strike, rate, volatility, maturity, option_type)
        )
        return (
            x_values,
            y_values,
            "Spot price",
            "Sweeping spot shows why Delta and Gamma exist: the price response is directional, but not perfectly linear.",
        )

    if variable == "Volatility":
        lower = max(0.01, volatility * 0.25)
        upper = max(0.60, volatility * 2.0)
        x_values = np.linspace(lower, upper, 220)
        y_values = np.asarray(
            [
                black_scholes_price(spot, strike, rate, sigma, maturity, option_type)
                for sigma in x_values
            ]
        )
        return (
            x_values * 100.0,
            y_values,
            "Volatility (%)",
            "This curve isolates Vega: higher uncertainty tends to make both calls and puts more valuable.",
        )

    if variable == "Time to maturity":
        lower = 1.0 / 252.0
        upper = max(2.0, maturity * 1.8, 0.25)
        x_values = np.linspace(lower, upper, 220)
        y_values = np.asarray(
            [
                black_scholes_price(spot, strike, rate, volatility, time_value, option_type)
                for time_value in x_values
            ]
        )
        return (
            x_values,
            y_values,
            "Time to maturity (years)",
            "This sweep shows how optionality changes with time. Theta describes the local rate of change as time passes.",
        )

    lower = rate - 0.05
    upper = rate + 0.05
    x_values = np.linspace(lower, upper, 220)
    y_values = np.asarray(
        [
            black_scholes_price(spot, strike, rate_value, volatility, maturity, option_type)
            for rate_value in x_values
        ]
    )
    return (
        x_values * 100.0,
        y_values,
        "Risk-free rate (%)",
        "This is the Rho channel: changing rates mainly works through the discounted strike and carry term.",
    )


def _local_bump_demo(
    context: dict[str, object], variable: str
) -> tuple[float, float, float, str]:
    """Compare exact repricing with a local Greek approximation."""
    spot = float(context["spot"])
    strike = float(context["strike"])
    rate = float(context["rate"])
    volatility = float(context["volatility"])
    maturity = float(context["maturity"])
    option_type = str(context["option_type"])
    option_value = float(context["option_value"])
    greeks = context["greek_snapshot"]

    if variable == "Spot":
        bump = max(0.5, strike * 0.01)
        shocked_value = float(
            black_scholes_price(spot + bump, strike, rate, volatility, maturity, option_type)
        )
        exact_change = shocked_value - option_value
        greek_change = float(greeks["delta"]) * bump + 0.5 * float(greeks["gamma"]) * bump**2
        return exact_change, greek_change, shocked_value, f"Spot bumped by +{bump:.2f}"

    if variable == "Volatility":
        bump = 0.01
        shocked_value = float(
            black_scholes_price(spot, strike, rate, volatility + bump, maturity, option_type)
        )
        exact_change = shocked_value - option_value
        greek_change = float(greeks["vega"]) * bump
        return exact_change, greek_change, shocked_value, "Volatility bumped by +1.00 vol point"

    if variable == "Time to maturity":
        bump = min(0.05, max(maturity * 0.1, 1.0 / 252.0))
        shocked_maturity = max(maturity - bump, 0.0)
        shocked_value = float(
            black_scholes_price(spot, strike, rate, volatility, shocked_maturity, option_type)
        )
        exact_change = shocked_value - option_value
        greek_change = float(greeks["theta"]) * bump
        return exact_change, greek_change, shocked_value, f"Calendar time advanced by {bump:.4f} years"

    bump = 0.0025
    shocked_value = float(
        black_scholes_price(spot, strike, rate + bump, volatility, maturity, option_type)
    )
    exact_change = shocked_value - option_value
    greek_change = float(greeks["rho"]) * bump
    return exact_change, greek_change, shocked_value, "Rate bumped by +25 bps"


def _build_banner(
    kicker: str,
    title: str,
    subtitle: str,
    badges: list[tuple[str, str]],
    command_line: str,
) -> str:
    """Top-of-page banner shared by explorer and learning sections."""
    badge_markup = "".join(
        f'<span class="status-pill status-{tone}">{escape(text)}</span>' for text, tone in badges
    )
    return f"""
    <div class="hero-panel">
        <div class="hero-kicker">{escape(kicker.upper())}</div>
        <h1>{escape(title)}</h1>
        <p>{escape(subtitle)}</p>
        <div class="status-row">{badge_markup}</div>
        <div class="command-line">{escape(command_line)}</div>
    </div>
    """


def _metric_card(label: str, value: float, accent_color: str) -> str:
    """Single KPI card used across explorer and learning pages."""
    display_color = NEGATIVE if value < 0 else accent_color
    return f"""
    <div class="metric-card">
        <div class="metric-label">{escape(label.upper())}</div>
        <div class="metric-value" style="color: {display_color};">{escape(_format_metric(value))}</div>
    </div>
    """


def _panel_header(kicker: str, title: str, subtitle: str) -> str:
    """Reusable section header for the terminal layout."""
    return f"""
    <div class="panel-header">
        <div class="panel-kicker">{escape(kicker.upper())}</div>
        <h3>{escape(title)}</h3>
        <p>{escape(subtitle)}</p>
    </div>
    """


def _learning_card(title: str, body: str) -> str:
    """Simple explanatory card used by the educational sections."""
    return f"""
    <div class="learning-card">
        <h4>{escape(title)}</h4>
        <p>{escape(body)}</p>
    </div>
    """


def _source_card(title: str, url: str, publisher: str, why: str) -> str:
    """Source card with publisher and reason for inclusion."""
    return f"""
    <div class="source-card">
        <div class="source-publisher">{escape(publisher)}</div>
        <h4><a href="{escape(url)}" target="_blank">{escape(title)}</a></h4>
        <p>{escape(why)}</p>
    </div>
    """


def _position_plain_english(context: dict[str, object]) -> str:
    """Describe the current selection in contract language rather than formula language."""
    strike = float(context["strike"])
    maturity = float(context["maturity"])
    option_type = str(context["option_type"])
    position_type = str(context["position_type"])

    if position_type == "long" and option_type == "call":
        return (
            f"This position buys the right, but not the obligation, to buy the underlying at {strike:.2f} "
            f"in {maturity:.2f} years. You pay premium today for upside convexity if spot finishes above strike."
        )
    if position_type == "short" and option_type == "call":
        return (
            f"This position sells the call and receives premium today, but takes the obligation if assigned. "
            f"If spot finishes well above {strike:.2f}, losses can keep increasing."
        )
    if position_type == "long" and option_type == "put":
        return (
            f"This position buys the right, but not the obligation, to sell the underlying at {strike:.2f} "
            f"in {maturity:.2f} years. It benefits from downside moves and can act like protection."
        )
    return (
        f"This position sells the put and receives premium today, but takes the obligation if assigned. "
        f"If spot finishes well below {strike:.2f}, losses grow as the underlying falls."
    )


def _exercise_style_table() -> str:
    """Markdown table comparing European and American exercise styles."""
    header = "| Topic | European | American |\n| --- | --- | --- |\n"
    rows = "".join(
        f"| {row['topic']} | {row['european']} | {row['american']} |\n"
        for row in EXERCISE_STYLE_COMPARISON
    )
    return header + rows


def _exercise_message(style_choice: str, side_choice: str) -> str:
    """Interpret exercise/assignment in plain English for the selected combination."""
    if style_choice == "European" and side_choice == "Long option":
        return "You control exercise, but only at expiry. There is no early-exercise choice before maturity."
    if style_choice == "European" and side_choice == "Short option":
        return "You do not face early assignment before expiry, but you still carry expiry assignment risk."
    if style_choice == "American" and side_choice == "Long option":
        return "You own the right and may choose whether to exercise before expiry. That extra flexibility is why American options are at least as valuable as otherwise identical European options."
    return "You are short an American-style option, so early assignment is possible. That is an operational and risk-management issue, not just a pricing nuance."


def _classify_moneyness(spot: float, strike: float, option_type: str) -> str:
    """Simple label for ITM, ATM, or OTM."""
    distance = abs(spot - strike) / strike
    if distance <= 0.02:
        return "ATM"
    if option_type == "call":
        return "ITM" if spot > strike else "OTM"
    return "ITM" if spot < strike else "OTM"


def _pricing_mode(volatility: float, maturity: float) -> str:
    """Surface when the app is using a limiting case instead of the standard closed form."""
    if maturity <= EPSILON:
        return "EXPIRY LIMIT"
    if volatility <= EPSILON:
        return "DETERMINISTIC LIMIT"
    return "CLOSED FORM"


def _intrinsic_value(spot: float, strike: float, option_type: str) -> float:
    """Immediate exercise value at the current spot."""
    if option_type == "call":
        return max(spot - strike, 0.0)
    return max(strike - spot, 0.0)


def _break_even_price(strike: float, premium: float, option_type: str) -> float:
    """Approximate expiry break-even using the current model premium."""
    if option_type == "call":
        return strike + premium
    return max(strike - premium, 0.0)


def _format_metric(value: float) -> str:
    """Consistent number formatting for cards."""
    return f"{value:,.4f}" if abs(value) >= 0.01 else f"{value:,.6f}"


def _rgba(hex_color: str, alpha: float) -> str:
    """Convert a hex colour to an rgba string for Plotly fills."""
    hex_value = hex_color.lstrip("#")
    red = int(hex_value[0:2], 16)
    green = int(hex_value[2:4], 16)
    blue = int(hex_value[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {alpha})"


def _inject_styles() -> None:
    """Centralised CSS for the terminal-like learning UI."""
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap');

            html, body, [class*="css"], [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] * {{
                font-family: {FONT_STACK};
            }}

            .stApp {{
                color: {TEXT};
                background:
                    radial-gradient(circle at 12% 6%, rgba(77, 213, 255, 0.14), transparent 26%),
                    radial-gradient(circle at 88% 2%, rgba(83, 243, 166, 0.12), transparent 22%),
                    linear-gradient(180deg, #07100f 0%, {APP_BG} 100%);
            }}

            .stApp::before {{
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                background: repeating-linear-gradient(
                    180deg,
                    transparent 0,
                    transparent 4px,
                    rgba(255, 255, 255, 0.018) 5px
                );
                opacity: 0.32;
            }}

            [data-testid="stHeader"],
            [data-testid="stToolbar"],
            [data-testid="stDecoration"],
            [data-testid="stStatusWidget"],
            #MainMenu,
            .stDeployButton {{
                display: none !important;
            }}

            div[data-testid="stAppViewContainer"] > .main {{
                padding-top: 0;
            }}

            .block-container {{
                max-width: 1280px;
                padding-top: 0.8rem;
                padding-bottom: 2.2rem;
            }}

            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, #091311 0%, #060a09 100%);
                border-right: 1px solid {PANEL_BORDER};
            }}

            [data-testid="stSidebar"] * {{
                color: {TEXT} !important;
            }}

            [data-testid="stSidebar"] input {{
                background: {PANEL_ALT} !important;
                border: 1px solid {PANEL_BORDER} !important;
                color: {TEXT} !important;
                border-radius: 10px !important;
            }}

            [data-testid="stSidebar"] [data-baseweb="radio"] {{
                background: {PANEL_ALT};
                border: 1px solid {PANEL_BORDER};
                border-radius: 12px;
                padding: 0.35rem 0.45rem;
            }}

            [data-testid="stSidebar"] [data-baseweb="slider"] > div > div {{
                background: {PRIMARY};
            }}

            [data-testid="stPlotlyChart"] {{
                background: linear-gradient(180deg, rgba(10, 21, 19, 0.98) 0%, rgba(8, 17, 15, 0.98) 100%);
                border: 1px solid {PANEL_BORDER};
                border-radius: 18px;
                padding: 0.5rem 0.45rem 0.2rem 0.45rem;
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.32);
            }}

            div[data-testid="stExpander"] {{
                background: linear-gradient(180deg, rgba(13, 27, 24, 0.95) 0%, rgba(10, 21, 19, 0.95) 100%);
                border: 1px solid {PANEL_BORDER};
                border-radius: 14px;
            }}

            div[data-testid="stAlert"] {{
                background: linear-gradient(180deg, rgba(13, 27, 24, 0.95) 0%, rgba(10, 21, 19, 0.95) 100%);
                border: 1px solid {PANEL_BORDER};
                color: {TEXT};
            }}

            .sidebar-shell {{
                padding: 0.1rem 0 1rem 0;
            }}

            .sidebar-kicker {{
                color: {PRIMARY};
                text-transform: uppercase;
                letter-spacing: 0.14em;
                font-size: 0.74rem;
                font-weight: 600;
            }}

            .sidebar-shell h2 {{
                margin: 0.2rem 0 0.55rem 0;
                font-size: 1.25rem;
                color: {TEXT};
            }}

            .sidebar-shell p {{
                margin: 0;
                color: {MUTED};
                line-height: 1.6;
                font-size: 0.9rem;
            }}

            .sidebar-footnote {{
                margin-top: 1rem;
                padding: 0.8rem 0.9rem;
                background: linear-gradient(180deg, rgba(13, 27, 24, 0.95) 0%, rgba(10, 21, 19, 0.95) 100%);
                border: 1px solid {PANEL_BORDER};
                border-radius: 14px;
                color: {MUTED};
                font-size: 0.78rem;
                line-height: 1.65;
            }}

            .hero-panel {{
                padding: 1rem 1.2rem 1.15rem 1.2rem;
                margin-bottom: 1rem;
                background: linear-gradient(180deg, rgba(10, 21, 19, 0.96) 0%, rgba(8, 16, 15, 0.96) 100%);
                border: 1px solid {PANEL_BORDER};
                border-radius: 18px;
                box-shadow: 0 24px 48px rgba(0, 0, 0, 0.28);
            }}

            .hero-kicker {{
                text-transform: uppercase;
                letter-spacing: 0.16em;
                color: {ACCENT};
                font-size: 0.75rem;
                font-weight: 600;
            }}

            .hero-panel h1 {{
                margin: 0.6rem 0 0 0;
                color: {TEXT};
                font-size: 2.35rem;
                letter-spacing: -0.035em;
                line-height: 1.05;
            }}

            .hero-panel p {{
                margin: 0.9rem 0 0 0;
                color: {MUTED};
                line-height: 1.7;
                max-width: 980px;
                font-size: 0.95rem;
            }}

            .status-row {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
                margin-top: 1rem;
            }}

            .status-pill {{
                display: inline-flex;
                align-items: center;
                padding: 0.32rem 0.58rem;
                border-radius: 999px;
                border: 1px solid {PANEL_BORDER};
                font-size: 0.74rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                background: {PANEL_ALT};
            }}

            .status-green {{
                color: {PRIMARY};
                border-color: rgba(83, 243, 166, 0.32);
            }}

            .status-cyan {{
                color: {ACCENT};
                border-color: rgba(77, 213, 255, 0.32);
            }}

            .status-amber {{
                color: {AMBER};
                border-color: rgba(247, 185, 85, 0.32);
            }}

            .status-red {{
                color: {NEGATIVE};
                border-color: rgba(255, 107, 107, 0.34);
            }}

            .status-neutral {{
                color: {NEUTRAL};
                border-color: {PANEL_BORDER};
            }}

            .command-line {{
                margin-top: 1rem;
                padding: 0.8rem 0.95rem;
                background: rgba(7, 12, 11, 0.92);
                border: 1px solid {PANEL_BORDER};
                border-radius: 14px;
                color: {PRIMARY};
                font-size: 0.84rem;
                letter-spacing: 0.03em;
                overflow-x: auto;
            }}

            .page-orientation {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.7rem;
                margin: 0.2rem 0 0.95rem 0;
            }}

            .page-orientation span {{
                padding: 0.45rem 0.65rem;
                border-radius: 999px;
                background: rgba(13, 27, 24, 0.82);
                border: 1px solid {PANEL_BORDER};
                color: {MUTED};
                font-size: 0.74rem;
                line-height: 1.4;
            }}

            .page-orientation strong {{
                color: {TEXT};
                font-weight: 600;
            }}

            .metric-card {{
                margin: 0.3rem 0 0.8rem 0;
                padding: 0.95rem 1rem;
                background: linear-gradient(180deg, rgba(13, 27, 24, 0.96) 0%, rgba(10, 21, 19, 0.96) 100%);
                border: 1px solid {PANEL_BORDER};
                border-radius: 16px;
                min-height: 112px;
                box-shadow: 0 16px 30px rgba(0, 0, 0, 0.22);
            }}

            .metric-label {{
                color: {MUTED};
                font-size: 0.72rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
            }}

            .metric-value {{
                margin-top: 0.7rem;
                font-size: 1.55rem;
                line-height: 1.1;
                word-break: break-word;
            }}

            .panel-header {{
                margin: 0.65rem 0 0.55rem 0;
            }}

            .panel-kicker {{
                color: {PRIMARY};
                text-transform: uppercase;
                letter-spacing: 0.14em;
                font-size: 0.72rem;
                font-weight: 600;
            }}

            .panel-header h3 {{
                margin: 0.45rem 0 0 0;
                color: {TEXT};
                font-size: 1.15rem;
            }}

            .panel-header p {{
                margin: 0.45rem 0 0 0;
                color: {MUTED};
                line-height: 1.6;
                font-size: 0.84rem;
                max-width: 880px;
            }}

            .learning-card,
            .source-card {{
                background: linear-gradient(180deg, rgba(10, 21, 19, 0.96) 0%, rgba(8, 16, 15, 0.96) 100%);
                border: 1px solid {PANEL_BORDER};
                border-radius: 16px;
                padding: 0.95rem 1rem;
                margin-bottom: 0.85rem;
                box-shadow: 0 18px 34px rgba(0, 0, 0, 0.2);
            }}

            .learning-card h4,
            .source-card h4 {{
                margin: 0 0 0.55rem 0;
                color: {TEXT};
                font-size: 0.98rem;
            }}

            .learning-card p,
            .source-card p {{
                margin: 0;
                color: {MUTED};
                line-height: 1.7;
                font-size: 0.84rem;
            }}

            .source-publisher {{
                color: {PRIMARY};
                text-transform: uppercase;
                letter-spacing: 0.12em;
                font-size: 0.68rem;
                margin-bottom: 0.45rem;
            }}

            .source-card a {{
                color: {ACCENT};
                text-decoration: none;
            }}

            .learning-note {{
                margin: 0.8rem 0 1rem 0;
                padding: 0.85rem 0.95rem;
                background: rgba(13, 27, 24, 0.88);
                border: 1px solid {PANEL_BORDER};
                border-radius: 14px;
                color: {MUTED};
                line-height: 1.7;
                font-size: 0.82rem;
            }}

            .notes-key {{
                color: {MUTED};
                font-size: 0.76rem;
                letter-spacing: 0.12em;
                padding: 0.42rem 0;
                border-bottom: 1px solid rgba(23, 53, 48, 0.45);
            }}

            .notes-value {{
                color: {TEXT};
                text-align: right;
                font-size: 0.84rem;
                padding: 0.42rem 0;
                border-bottom: 1px solid rgba(23, 53, 48, 0.45);
            }}

            .notes-divider {{
                height: 1px;
                background: {PANEL_BORDER};
                margin: 0.85rem 0;
            }}

            .notes-subtitle {{
                color: {PRIMARY};
                text-transform: uppercase;
                letter-spacing: 0.14em;
                font-size: 0.7rem;
                margin-bottom: 0.45rem;
            }}

            .notes-note {{
                display: flex;
                gap: 0.55rem;
                color: {MUTED};
                font-size: 0.8rem;
                line-height: 1.65;
                padding: 0.18rem 0;
            }}

            .notes-prompt {{
                color: {PRIMARY};
            }}

            .quiz-question {{
                color: {TEXT};
                font-size: 0.86rem;
                line-height: 1.6;
                margin: 0.7rem 0 0.35rem 0;
            }}

            code {{
                color: {PRIMARY};
                background: rgba(13, 27, 24, 0.92);
                border: 1px solid {PANEL_BORDER};
                border-radius: 6px;
                padding: 0.15rem 0.32rem;
            }}

            a {{
                color: {ACCENT};
            }}

            @media (max-width: 900px) {{
                .hero-panel h1 {{
                    font-size: 1.8rem;
                }}

                .metric-value {{
                    font-size: 1.25rem;
                }}

                .notes-value {{
                    text-align: left;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
