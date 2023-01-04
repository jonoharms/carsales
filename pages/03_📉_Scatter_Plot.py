import glob
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_extras.dataframe_explorer import dataframe_explorer
from sklearn.linear_model import LinearRegression
import datetime
import altair as alt


def main():
    st.set_page_config(page_title='Scatter Plot', layout='wide')
    st.write('# Carsales Analyser')
    st.write('⌘/^ click to open carsales page in new tab')
    data = Path.cwd().joinpath('data').resolve()
    files = glob.glob(str(data) + '/*.csv')
    dataframes = [pd.read_csv(file, index_col=0) for file in files]
    df = (
        pd.concat(dataframes, axis=0)
        .drop_duplicates(subset=['id'])
        .reset_index(drop=True)
    )
    df['model'] = df['model'].astype(str)
    df['age'] = datetime.date.today().year - df['year']
    df = dataframe_explorer(df)
    y_col = st.sidebar.selectbox(
        'Y Value', ['ex_gov_price', 'drive_away_price'], index=0
    )
    y_col = y_col if y_col is not None else 'ex_gov_price'
    color_by = st.sidebar.selectbox('Color By', df.columns, index=12)
    # x_col = st.sidebar.selectbox('X Value', ['kms', 'age', 'year'], index=0)
    # x_col = x_col if x_col is not None else 'kms'

    # size_by = st.sidebar.selectbox('Size By', ['kms', 'age'], index=0)
    st.sidebar.markdown("""---""")
    trendline_type = st.sidebar.selectbox(
        'Trendline Type',
        ['linear', 'quad', 'poly', 'log', 'exp', 'pow', 'loess', None],
    )
    trendline_order = 3
    if trendline_type == 'poly':
        trendline_order = st.sidebar.select_slider('Order', range(3, 10))

    trendline_scope = st.sidebar.selectbox(
        'Trendline Scope', ['overall', 'trace']
    )
    only_trends = st.sidebar.checkbox('Only Show Trendlines', value=False)
    tooltip = [
        'make',
        'model',
        'badge',
        'ex_gov_price',
        'drive_away_price',
        'kms',
        'year',
        'state',
        'id',
    ]
    brush = alt.selection_interval()  # selection of type "interval"

    base_chart = (
        alt.Chart(df)
        .mark_point()
        .encode(
            # x=x_col + ':Q',
            y=y_col + ':Q',
            # color=alt.condition(brush, color_by, alt.value('lightgray')),
            tooltip=tooltip,
            href='link:N',
            # size=size_by,
        )
        # .add_selection(brush)
    )
    x_cols = ['kms:Q', 'age:Q']
    points_charts = list(base_chart.encode(x=col) for col in x_cols)

    trend_charts = None
    if trendline_type:
        groupby = [color_by] if trendline_scope == 'trace' else []

        if trendline_type == 'loess':
            trend_charts = list(
                chart.transform_loess(
                    col,
                    y_col,
                    groupby=groupby,
                ).mark_line()
                for col, chart in zip(x_cols, points_charts)
            )
        else:
            trend_charts = list(
                chart.transform_regression(
                    col,
                    y_col,
                    method=trendline_type,
                    groupby=groupby,
                    order=trendline_order,
                ).mark_line()
                for col, chart in zip(x_cols, points_charts)
            )

    # if trend_charts and only_trends:
    #     chart = alt.hconcat(*trend_charts)
    # elif trend_charts:

    # else:

    charts = [
        chart.encode(
            color=alt.condition(brush, color_by, alt.value('lightgray'))
        ).add_selection(brush)
        for chart in points_charts
    ]
    # charts = [
    #     alt.layer(point, trend) for point, trend in zip(charts, trend_charts)
    # ]

    chart = alt.hconcat(*charts)
    trend_chart = alt.hconcat(*trend_charts)

    st.altair_chart(chart, use_container_width=True)
    st.altair_chart(trend_chart, use_container_width=True)

    with st.expander('Show Dataframe'):
        st.write(df)


if __name__ == '__main__':
    main()
