from decimal import Decimal
import pandas as pd
import plotly.express as px

PALETTE = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4", "#EC4899", "#84CC16"]


def _is_number(v) -> bool:
    return isinstance(v, (int, float, Decimal)) and not isinstance(v, bool)


def _pretty(name: str) -> str:
    return name.replace("_", " ").title()


def rows_to_dataframe(rows: list[dict]) -> pd.DataFrame:
    """Converts SQL rows to a DataFrame, turning Decimal columns into floats."""
    df = pd.DataFrame(rows)
    for col in df.columns:
        values = [v for v in df[col] if v is not None]
        if values and any(isinstance(v, Decimal) for v in values) and all(_is_number(v) for v in values):
            df[col] = df[col].map(lambda v: float(v) if v is not None else None)
    return df


def build_chart(chart_type: str, rows: list[dict]):
    """Returns a Plotly figure, or None if the data can't be charted."""
    if not rows or len(rows) < 2:
        return None

    df = rows_to_dataframe(rows)
    numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    labels = [c for c in df.columns if c not in numeric]

    if labels and numeric:
        x, y = labels[0], numeric[-1]
    elif len(numeric) >= 2:
        x, y = numeric[0], numeric[-1]
    else:
        return None

    if chart_type == "pie" and ((df[y] < 0).any() or len(df) > 12):
        chart_type = "bar"          # pies only make sense for a few positive slices
    if chart_type == "line":
        df = df.sort_values(x)

    names = {x: _pretty(x), y: _pretty(y)}

    if chart_type == "line":
        fig = px.line(df, x=x, y=y, markers=True, labels=names, color_discrete_sequence=PALETTE)
        fig.update_traces(line=dict(width=3), marker=dict(size=8))
    elif chart_type == "pie":
        fig = px.pie(df, names=x, values=y, hole=0.45, color_discrete_sequence=PALETTE)
        fig.update_traces(textinfo="percent+label", textposition="inside")
    else:
        fig = px.bar(df, x=x, y=y, labels=names, color_discrete_sequence=PALETTE)
        fig.update_traces(marker_line_width=0)

    fig.update_layout(
        template="plotly_white",
        title=dict(text=f"{_pretty(y)} by {_pretty(x)}", x=0.02),
        font=dict(size=13),
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=(chart_type == "pie"),
    )
    if chart_type != "pie":
        fig.update_layout(hovermode="x unified")
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="#E5E7EB", zeroline=False)
    return fig