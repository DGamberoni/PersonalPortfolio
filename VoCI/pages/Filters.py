import streamlit as st
import pandas as pd
from pandas.api.types import is_categorical_dtype, is_datetime64_any_dtype, is_numeric_dtype, is_object_dtype
import os
from io import BytesIO

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Trattamento delle colonne con pochi valori unici come categoriche o che terminano con '_id'
            if is_categorical_dtype(df[column]) or df[column].nunique() < 30 or column.endswith('_id') or column.endswith('Id') or column.endswith('ID'):
                unique_values = df[column].unique()
                
                select_all = right.checkbox("Select all", key=f"{column}_all")
                if select_all:
                    df = df[df[column].isin(unique_values)]
                else:
                    options = unique_values.tolist()
                    user_cat_input = right.multiselect(
                        f"Values for {column}",
                        default=None,
                        options=options,
                    )
                    if user_cat_input:
                        df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    _min,
                    _max,
                    (_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                min_date = df[column].min()
                max_date = df[column].max()
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]

            else:
                user_text_inputs = right.text_area(
                    f"Substrings or regex (AND/OR logic) in {column} (use AND/OR to separate)",
                ).split('\n')
                if user_text_inputs:
                    combined_query = " ".join(user_text_inputs)
                    and_parts = combined_query.split("AND")
                    and_conditions = []
                    for part in and_parts:
                        or_conditions = part.split("OR")
                        or_queries = [f"({column}.str.contains(r'\\b{cond.strip()}\\b', case=False, regex=True, na=False))" for cond in or_conditions]
                        and_conditions.append(" | ".join(or_queries))
                    final_query = " & ".join(f"({cond})" for cond in and_conditions)
                    df = df.query(final_query)

    return df

def download_file():
    output = BytesIO()
    if 'file_in' in st.session_state:
        input_name = os.path.splitext(st.session_state['file_in'].name)[0]
    elif 'query_name' in st.session_state:
        input_name = st.session_state['query_name']
    output_name = f"{input_name}_Filtered.xlsx"
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state["df_current"].to_excel(writer, index=False)
    output.seek(0)

    st.download_button(
        label = "Download",
        data = output,
        file_name = output_name,
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def main():

    st.title("🔍Filter Data")
    
    st.session_state["df_current_filtered"] = filter_dataframe(st.session_state["df_current"])

    st.dataframe(st.session_state["df_current_filtered"].head(1000))
    dimensions = st.session_state["df_current_filtered"].shape
    st.markdown(f"Dimensions of the dataframe: {dimensions[0]} rows, {dimensions[1]} columns")
    download_file()

    if st.button("Apply filters"):
        st.session_state["df_current"] = st.session_state["df_current_filtered"]

    st.markdown('---')
    st.page_link("1_Homepage.py", label="Add Data", icon="📥")
    st.page_link("pages/3_Sentiment.py", label="Compute Sentiment", icon="😊")
    st.page_link("pages/4_Graphtopic.py", label="Find Topics", icon="🕸️")

if __name__ == "__main__":
    main()