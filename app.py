from __future__ import annotations

from html import escape

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from greeks import analytical_greeks
from payoff import option_payoff
from pricing import black_scholes_price
from utils import create_price_grid, position_sign

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


def main() -> None:
    st.set_page_config(
        page_title="Options Payoff & Greeks Visualiser",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_styles()

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-shell">
                <div class="sidebar-kicker">Research Terminal</div>
                <h2>Model Deck</h2>
                <p>Configure a single European option and inspect both its expiry shape and analytical risk profile.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
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
                Greeks are annualised. Vega and rho are quoted per 1.00 change in volatility and rates.
            </div>
            """,
            unsafe_allow_html=True,
        )

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
    signed_option_value = position_multiplier * option_value
    signed_value_curve = position_multiplier * value_curve

    regime = _classify_moneyness(spot, strike, option_type)
    pricing_mode = _pricing_mode(volatility, maturity)
    moneyness = spot / strike
    break_even = _break_even_price(strike, option_value, option_type)
    discounted_strike = strike * np.exp(-rate * maturity)

    st.markdown(
        _build_hero(
            option_type=option_type,
            position_type=position_type,
            regime=regime,
            pricing_mode=pricing_mode,
            spot=spot,
            strike=strike,
            volatility=volatility,
            maturity=maturity,
            rate=rate,
        ),
        unsafe_allow_html=True,
    )

    top_metrics = [
        ("Position value", signed_option_value, ACCENT),
        ("Delta", signed_snapshot["delta"], PRIMARY),
        ("Gamma", signed_snapshot["gamma"], ACCENT),
    ]
    bottom_metrics = [
        ("Vega", signed_snapshot["vega"], AMBER),
        ("Theta", signed_snapshot["theta"], NEGATIVE),
        ("Rho", signed_snapshot["rho"], NEUTRAL),
    ]

    for columns, metric_group in (
        (st.columns(3), top_metrics),
        (st.columns(3), bottom_metrics),
    ):
        for column, (label, value, accent_color) in zip(columns, metric_group):
            column.markdown(
                _metric_card(label=label, value=value, accent_color=accent_color),
                unsafe_allow_html=True,
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
                price_grid=price_grid,
                payoff_curve=payoff_curve,
                value_curve=signed_value_curve,
                spot=spot,
                strike=strike,
                position_type=position_type,
            ),
            use_container_width=True,
        )

    with right_column:
        st.markdown(
            _panel_header(
                kicker="Desk Notes",
                title="Research Summary",
                subtitle="Compact diagnostics for screenshots and fast interpretation.",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _build_notes_panel(
                option_type=option_type,
                position_type=position_type,
                regime=regime,
                pricing_mode=pricing_mode,
                mark=option_value,
                break_even=break_even,
                moneyness=moneyness,
                discounted_strike=discounted_strike,
                price_low=float(price_grid[0]),
                price_high=float(price_grid[-1]),
            ),
            unsafe_allow_html=True,
        )

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
            price_grid=price_grid,
            greek_curves=signed_greek_curves,
            spot=spot,
        ),
        use_container_width=True,
    )


def _build_payoff_figure(
    price_grid: np.ndarray,
    payoff_curve: np.ndarray,
    value_curve: np.ndarray,
    spot: float,
    strike: float,
    position_type: str,
) -> go.Figure:
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


def _apply_chart_theme(figure: go.Figure) -> None:
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


def _build_hero(
    option_type: str,
    position_type: str,
    regime: str,
    pricing_mode: str,
    spot: float,
    strike: float,
    volatility: float,
    maturity: float,
    rate: float,
) -> str:
    badges = [
        ("BLACK-SCHOLES", "cyan"),
        ("EUROPEAN", "neutral"),
        (f"{position_type.upper()} {option_type.upper()}", "green" if position_type == "long" else "red"),
        (regime, "amber"),
        (pricing_mode, "neutral"),
    ]
    badge_markup = "".join(
        f'<span class="status-pill status-{tone}">{escape(text)}</span>' for text, tone in badges
    )
    return f"""
    <div class="hero-panel">
        <div class="hero-kicker">Terminal Research / Quant Option Study</div>
        <h1>Options Payoff &amp; Greeks Visualiser</h1>
        <p>
            Compact desk-style analysis for payoff inspection, theoretical valuation, and analytical Greeks.
            Built to read like a research terminal rather than a generic dashboard.
        </p>
        <div class="status-row">{badge_markup}</div>
        <div class="command-line">
            RUN/BS SPOT={spot:.2f} STRIKE={strike:.2f} SIGMA={volatility * 100:.2f}% RATE={rate * 100:.2f}% T={maturity:.2f}Y
        </div>
    </div>
    """


def _metric_card(label: str, value: float, accent_color: str) -> str:
    display_color = NEGATIVE if value < 0 else accent_color
    return f"""
    <div class="metric-card">
        <div class="metric-label">{escape(label.upper())}</div>
        <div class="metric-value" style="color: {display_color};">{escape(_format_metric(value))}</div>
    </div>
    """


def _panel_header(kicker: str, title: str, subtitle: str) -> str:
    return f"""
    <div class="panel-header">
        <div class="panel-kicker">{escape(kicker.upper())}</div>
        <h3>{escape(title)}</h3>
        <p>{escape(subtitle)}</p>
    </div>
    """


def _build_notes_panel(
    option_type: str,
    position_type: str,
    regime: str,
    pricing_mode: str,
    mark: float,
    break_even: float,
    moneyness: float,
    discounted_strike: float,
    price_low: float,
    price_high: float,
) -> str:
    rows = [
        ("POSITION", f"{position_type.upper()} {option_type.upper()}"),
        ("REGIME", regime),
        ("MODEL MARK", _format_metric(mark)),
        ("BREAK-EVEN", f"{break_even:,.4f}"),
        ("MONEYNESS", f"{moneyness:.4f}x"),
        ("PV STRIKE", f"{discounted_strike:,.4f}"),
        ("GRID WINDOW", f"{price_low:,.2f} -> {price_high:,.2f}"),
        ("ENGINE", pricing_mode),
    ]
    row_markup = "".join(
        f"""
        <div class="console-row">
            <span class="console-key">{escape(key)}</span>
            <span class="console-value">{escape(value)}</span>
        </div>
        """
        for key, value in rows
    )
    notes = [
        "Theta is annualised.",
        "Vega and rho are quoted per 1.00 change.",
        "Short positions invert the long Greeks and value curve.",
        "Stable limiting cases are used when sigma or maturity approach zero.",
    ]
    note_markup = "".join(
        f'<div class="console-note"><span class="console-prompt">&gt;</span>{escape(note)}</div>'
        for note in notes
    )
    return f"""
    <div class="console-panel">
        {row_markup}
        <div class="console-divider"></div>
        {note_markup}
    </div>
    """


def _classify_moneyness(spot: float, strike: float, option_type: str) -> str:
    distance = abs(spot - strike) / strike
    if distance <= 0.02:
        return "ATM"
    if option_type == "call":
        return "ITM" if spot > strike else "OTM"
    return "ITM" if spot < strike else "OTM"


def _pricing_mode(volatility: float, maturity: float) -> str:
    if maturity <= 1e-10:
        return "EXPIRY LIMIT"
    if volatility <= 1e-10:
        return "DETERMINISTIC LIMIT"
    return "CLOSED FORM"


def _break_even_price(strike: float, premium: float, option_type: str) -> float:
    if option_type == "call":
        return strike + premium
    return max(strike - premium, 0.0)


def _inject_styles() -> None:
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

            .block-container {{
                max-width: 1280px;
                padding-top: 1.6rem;
                padding-bottom: 2.2rem;
            }}

            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, #091311 0%, #060a09 100%);
                border-right: 1px solid {PANEL_BORDER};
            }}

            [data-testid="stSidebar"] * {{
                color: {TEXT} !important;
            }}

            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] .stMarkdown,
            [data-testid="stSidebar"] .stCaption {{
                letter-spacing: 0.02em;
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

            .sidebar-shell {{
                padding: 0.1rem 0 1rem 0;
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

            .sidebar-kicker {{
                color: {PRIMARY};
                text-transform: uppercase;
                letter-spacing: 0.14em;
                font-size: 0.74rem;
                font-weight: 600;
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
                max-width: 940px;
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
                font-size: 1.6rem;
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
                max-width: 820px;
            }}

            .console-panel {{
                background: linear-gradient(180deg, rgba(10, 21, 19, 0.96) 0%, rgba(8, 16, 15, 0.96) 100%);
                border: 1px solid {PANEL_BORDER};
                border-radius: 18px;
                padding: 0.9rem 1rem;
                box-shadow: 0 18px 34px rgba(0, 0, 0, 0.24);
            }}

            .console-row {{
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                padding: 0.52rem 0;
                border-bottom: 1px solid rgba(23, 53, 48, 0.45);
            }}

            .console-key {{
                color: {MUTED};
                font-size: 0.76rem;
                letter-spacing: 0.12em;
            }}

            .console-value {{
                color: {TEXT};
                text-align: right;
                font-size: 0.84rem;
            }}

            .console-divider {{
                height: 1px;
                background: {PANEL_BORDER};
                margin: 0.85rem 0;
            }}

            .console-note {{
                display: flex;
                gap: 0.55rem;
                color: {MUTED};
                font-size: 0.8rem;
                line-height: 1.65;
                padding: 0.18rem 0;
            }}

            .console-prompt {{
                color: {PRIMARY};
            }}

            code {{
                color: {PRIMARY};
                background: rgba(13, 27, 24, 0.92);
                border: 1px solid {PANEL_BORDER};
                border-radius: 6px;
                padding: 0.15rem 0.32rem;
            }}

            @media (max-width: 900px) {{
                .hero-panel h1 {{
                    font-size: 1.8rem;
                }}

                .metric-value {{
                    font-size: 1.3rem;
                }}

                .console-row {{
                    flex-direction: column;
                    align-items: flex-start;
                }}

                .console-value {{
                    text-align: left;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _format_metric(value: float) -> str:
    return f"{value:,.4f}" if abs(value) >= 0.01 else f"{value:,.6f}"


def _rgba(hex_color: str, alpha: float) -> str:
    hex_value = hex_color.lstrip("#")
    red = int(hex_value[0:2], 16)
    green = int(hex_value[2:4], 16)
    blue = int(hex_value[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {alpha})"


if __name__ == "__main__":
    main()
