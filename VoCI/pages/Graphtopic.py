import streamlit as st
import pandas as pd
import os
from io import BytesIO
from graphtopic import st_GraphTopic
import streamlit.components.v1 as components

def run():
    if 'df_current' in st.session_state:
        message_column = "Message_VoCI"
        st.session_state['message_column'] = message_column
        if message_column is not None and 'gt' not in st.session_state:
            if st.button("Find topics"):
                st.session_state['gt'] = st_GraphTopic(st.session_state['df_current'], message_column)
                st.session_state['gt'].get_communities()
                st.session_state['df_out'] = st.session_state['gt'].df
                st.session_state['df_current'] = st.session_state['df_out'].copy()

def download_file():
    if 'df_out' in st.session_state:
        df_out = st.session_state['df_out']
        st.markdown("### Enriched File")
        st.dataframe(df_out.head(1000))
        dimensions = df_out.shape
        st.markdown(f"Dimensions of the dataframe: {dimensions[0]} rows, {dimensions[1]} columns")
        output = BytesIO()
        if 'file_in' in st.session_state:
            input_name = os.path.splitext(st.session_state['file_in'].name)[0]
        elif 'query_name' in st.session_state:
            input_name = st.session_state['query_name']
        output_name = f"{input_name}_GT.xlsx"
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_out.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            label = "Download",
            data = output,
            file_name = output_name,
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def show_graph(n_communities = 5):

    html_content = st.session_state['gt'].view(n_communities) 
    html_content = html_content.replace('position: relative;', 'position: Fixed; top:0;')

    st.session_state['html_content'] = html_content
    graph_borders = """
                            <style>
                                iframe {
                                    border: 6px double #00AFF1 !important; /* Custom purple double border */
                                    border-radius: 10px !important; /* Rounded corners */
                                    box-shadow: 0px 10px 100px rgba(0, 0, 0, 0.1) !important; /* Shadow for 3D effect */
                                    margin: 0 !important; /* Reset margin */
                                    padding: 0 !important; /* Reset padding */
                                    box-sizing: border-box !important; /* Include padding and border in the element's total width and height */
                                    overflow: hidden !important; /* Hide anything outside the bounds of the iframe */
                                }
                            </style>
                        """
    st.markdown(graph_borders, unsafe_allow_html=True)
    source_code = st.session_state.html_content    
    components.html(source_code, height=600)

def sum_up():
    if 'df_out' in st.session_state:
        st.markdown('---')
        st.markdown("### Generate Summaries")
        api_key = st.text_input("Insert your Gemini API key",
                                type = 'password',
                                value = 'AIzaSyCH_VRsDIvCkNEjxto9IQrVmBJMhJ7W-0M')
        n_communities = st.slider("How many topics do you want to sum up?", min_value=1, max_value=10, value=5, step=1, key="slider2")
        st.session_state['n_communities'] = n_communities
        with_duplicates = st.radio('How do you want to rank them?',
                                   ['Cardinality_With_Duplicates', 'Cardinality_Without_Duplicates'],
                                   captions=['e.g. when the number of reposts matter',
                                             'e.g. when you need more variety in each community'])
        with_duplicates = with_duplicates == 'Cardinality_With_Duplicates'

        if st.button("Generate summaries"):
            if api_key:
                gt = st.session_state['gt']
                st.session_state['df_summaries'] = gt.sum_up(api_key = api_key,
                                                             n_communities = n_communities,
                                                             with_duplicates = with_duplicates)            
                
            else:
                st.error("Error: Insert your Gemini API key.")
    
    if 'df_summaries' in st.session_state:
        df_summaries = st.session_state.df_summaries

        for _, row in df_summaries.iterrows():
            st.markdown(f"#### {row['Rank']}. {row['Title']}")
            st.markdown(f"**Summary:** {row['Summary']}")
        
        show_graph(n_communities)

def recap_output():
    if 'df_out' in st.session_state:
        df_out = st.session_state['df_out']
        n_tot = len(df_out)
        n_communities_big = len(df_out['Community'][df_out['Cardinality_With_Duplicates'] > 1].unique())
        max_cardinality_duplicates = df_out['Cardinality_With_Duplicates'].max()
        max_cardinality_no_duplicates = df_out['Cardinality_Without_Duplicates'].max()
        output_md = f"""
        ### Recap
        - Total number of entries: {n_tot}
        - Number of topics: {n_communities_big}
        - Maximum cardinality (with duplicates): {max_cardinality_duplicates}
        - Maximum cardinality (without duplicates): {max_cardinality_no_duplicates}
        """
        st.markdown(output_md)
    
def download_summaries():
    if 'df_summaries' in st.session_state:
        df_summaries = st.session_state['df_summaries']
        output = BytesIO()
        if 'file_in' in st.session_state:
            input_name = os.path.splitext(st.session_state['file_in'].name)[0]
        elif 'query_name' in st.session_state:
            input_name = st.session_state['query_name']
        output_name = f"{input_name}_GT_summaries.xlsx"
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_summaries.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            label = "Download summaries",
            data = output,
            file_name = output_name,
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def main():
    st.set_page_config(page_title="VoCI · Topics", page_icon="🕸️")
    st.title("🕸️Topics")
    run()
    recap_output()
    download_file()
    sum_up()
    download_summaries()
    st.markdown('---')
    st.page_link("1_Homepage.py", label="Add Data", icon="📥")
    st.page_link("pages/2_Filters.py", label="Filter Data", icon="🔍")
    st.page_link("pages/3_Sentiment.py", label="Compute Sentiment", icon="😊")
         

if __name__ == '__main__':
    main()