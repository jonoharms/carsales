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
    color_by = st.sidebar.selectbox('Color By', df.columns, index=12)
    x_col = st.sidebar.selectbox('X Value', ['kms', 'age', 'year'], index=0)
    x_col = x_col if x_col is not None else 'kms'

    y_col = st.sidebar.selectbox(
        'Y Value', ['ex_gov_price', 'drive_away_price'], index=0
    )
    y_col = y_col if y_col is not None else 'ex_gov_price'

    size = st.sidebar.selectbox('Size', [None, 'kms', 'age'], index=0)
    st.sidebar.markdown("""---""")
    trendline = st.sidebar.selectbox('Trendline Type', ['ols', 'lowess', None])
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

    if st.sidebar.checkbox('plotly', value=False):
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_by,
            hover_name='title',
            hover_data=tooltip,
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
    else:
        achart = (
            alt.Chart(df)
            .mark_point()
            .encode(
                x=x_col + ':Q',
                y=y_col + ':Q',
                color=color_by,
                tooltip=tooltip,
                href='link:N',
                size=size,
            )
        )

        st.altair_chart(achart, use_container_width=True)

    with st.expander('Show Dataframe'):
        st.write(df)


if __name__ == '__main__':
    main()
