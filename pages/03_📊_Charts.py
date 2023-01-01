import glob
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_extras.dataframe_explorer import dataframe_explorer
from sklearn.linear_model import LinearRegression
import datetime


def main():
    st.write('# Carsales Analyser')

    data = Path.cwd().joinpath('data').resolve()
    files = glob.glob(str(data) + '/*.csv')
    dataframes = [pd.read_csv(file, index_col=0) for file in files]
    df = (
        pd.concat(dataframes, axis=0)
        .drop_duplicates(subset=['id'])
        .reset_index(drop=True)
    )
    df['age'] = datetime.date.today().year - df['year']
    df = dataframe_explorer(df)
    color_by = st.sidebar.selectbox('Color By', df.columns, index=12)
    x_col = st.sidebar.selectbox('X Value', ['kms', 'age', 'year'], index=0)
    y_col = st.sidebar.selectbox(
        'Y Value', ['ex_gov_price', 'drive_away_price'], index=0
    )
    size = st.sidebar.selectbox('Size', [None, 'kms', 'age'], index=0)
    st.sidebar.markdown("""---""")
    trendline = st.sidebar.selectbox('Trendline Type', ['ols', 'lowess', None])
    trendline_scope = st.sidebar.selectbox(
        'Trendline Scope', ['overall', 'trace']
    )
    only_trends = st.sidebar.checkbox('Only Show Trendlines', value=False)

    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_by,
        hover_name='title',
        hover_data=[
            'make',
            'model',
            'badge',
            'ex_gov_price',
            'drive_away_price',
            'kms',
            'year',
            'state',
        ],
        trendline=trendline,
        trendline_scope=trendline_scope,
        size=size,
    )

    if x_col == 'year':
        fig.update_xaxes(autorange='reversed')

    if only_trends:
        fig.data = [t for t in fig.data if t.mode == 'lines']
        fig.update_traces(
            showlegend=True
        )   # trendlines have showlegend=False by default

    st.plotly_chart(fig, use_container_width=True)

    if trendline == 'ols':
        with st.expander('Show Trendline Results'):
            results = px.get_trendline_results(fig)

            for res in results.px_fit_results:
                st.write(res.summary())

    with st.expander('Show Dataframe'):
        st.write(df)


if __name__ == '__main__':
    main()
