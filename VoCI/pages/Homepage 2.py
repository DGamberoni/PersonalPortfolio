import streamlit as st
import pandas as pd
from transformers import AutoTokenizer, AutoConfig
from sentence_transformers import SentenceTransformer
from optimum.onnxruntime import ORTModelForSequenceClassification
from io import BytesIO
from pandas.api.types import is_categorical_dtype, is_datetime64_any_dtype, is_numeric_dtype, is_object_dtype
import os
from bcr_api.bwproject import BWProject
from bcr_api.bwresources import BWQueries
import requests
import datetime

def configure_page():
    st.set_page_config(page_title="VoCI", page_icon="🧬")

    _, col2, _ = st.columns([1,1,1])
    with col2:
        st.image('voci_logo.png', width=200)
   
def import_models():
    with st.spinner("Loading app..."):
        model_path = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
        if 'tokenizer' not in st.session_state:
            st.session_state['tokenizer'] = AutoTokenizer.from_pretrained(model_path)
            st.session_state['config'] = AutoConfig.from_pretrained(model_path)
            st.session_state['model'] = ORTModelForSequenceClassification.from_pretrained(model_path, export=True)
            st.session_state['embedd_model'] = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device = "cpu")

def query_brandwatch():

    with st.form("my_form"):

        if "username" in st.session_state and "password" in st.session_state:
            username = st.text_input("Username", value = st.session_state["username"])
            password = st.text_input("Password", type="password", value = st.session_state["password"])
        else:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

        submitted = st.form_submit_button("Submit")
        if submitted and 'token' not in st.session_state:
            try:
                st.session_state["username"] = username
                st.session_state["password"] = password
                
                url = 'https://api.brandwatch.com/oauth/token'
                params = {
                    'username': username,
                    'grant_type': 'api-password',
                    'client_id': 'brandwatch-api-client'
                }
                data = {
                    'password': password
                }
                response = requests.post(url, params=params, data=data).json()
                token = response['access_token']
                st.success("Success: Connected to Brandwatch")
                st.session_state['token'] = token
            except:
                st.error("Error: Invalid credentials")

    if 'token' in st.session_state:

        if 'projects' not in st.session_state:
            url = 'https://api.brandwatch.com/projects/summary'
            headers = {
                'Authorization': f'Bearer {st.session_state["token"]}'
            }
            projects = requests.get(url, headers=headers)
            st.session_state['projects'] = projects

        else:
            projects = st.session_state['projects']   
         
        projects_names = [item['name'] for item in projects.json()['results']]
        projects_ids = [item['id'] for item in projects.json()['results']]
        projects_df = pd.DataFrame({'Project Name': projects_names, 'Project ID': projects_ids})

        project_name = st.selectbox("Select a project", options = projects_names, index = None)
        if project_name is not None:
            project_id = projects_df[projects_df['Project Name'] == project_name]['Project ID'].values[0]
            st.session_state['project_id'] = project_id
    
    if 'project_id' in st.session_state:
        
        if 'queries' not in st.session_state:
            url = f"https://api.brandwatch.com/projects/{project_id}/queries?type=monitor"
            headers = {
                'Authorization': f'Bearer {st.session_state["token"]}'
            }
            queries = requests.get(url, headers=headers)
            st.session_state['queries'] = queries
        
        else:
            queries = st.session_state['queries']

        queries_names = [item['name'] for item in queries.json()['results']]
        query_name = st.selectbox("Select a query", options = queries_names, index = None)
        st.session_state['query_name'] = query_name

    if 'query_name' in st.session_state:

        today = datetime.datetime.now()
        current_year = today.year
        date_range = st.date_input(
            "Select a date range",
            value=(datetime.date(current_year, 1, 1), datetime.datetime.now()),
            min_value=datetime.date(2000, 1, 1),
            format="DD/MM/YYYY",
        )

        if st.button("Load data"):
            startDate = date_range[0].strftime("%Y-%m-%d")
            endDate = date_range[1].strftime("%Y-%m-%d")

            with st.spinner("Retrieving mentions..."):
                project = BWProject(username=username, project=project_name, password=password, token_path=None)
                queries = BWQueries(project)
                df_in = pd.DataFrame(queries.get_mentions(query_name, startDate = startDate, endDate = endDate))
                df_in = df_in[df_in['fullText'].notna()]
                df_in.dropna(axis = 1, how = 'all', inplace = True)
                columns = df_in.columns.tolist()
                columns.remove('fullText')
                columns_order = ['fullText'] + columns
                df_in = df_in[columns_order]
                st.session_state['df_in'] = df_in

def upload_file():
    file_in = st.file_uploader("Choose a file")
    if file_in is not None:
        if 'file_in' not in st.session_state or file_in != st.session_state['file_in']:
            st.session_state['file_in'] = file_in
            try:
                df_in = pd.read_excel(file_in)
                st.session_state['df_in'] = df_in
            except:
                try:
                    df_in = pd.read_csv(file_in)
                    st.session_state['df_in'] = df_in
                except:
                    st.error(f"Error: Insert an Excel or CSV file_in.")


def download_file():
    output = BytesIO()
    if 'file_in' in st.session_state:
        input_name = os.path.splitext(st.session_state['file_in'].name)[0]
    elif 'query_name' in st.session_state:
        input_name = st.session_state['query_name']
    output_name = f"{input_name}_Enriched.xlsx"
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
    configure_page()
    import_models()
    
    if "df_current" not in st.session_state:
        st.session_state["df_current"] = pd.DataFrame()

    source_selection = st.radio("Choose your data source",
                                ["✨Brandwatch", "💻Local File"],
                                index=None)
    
    if source_selection == "✨Brandwatch":
        query_brandwatch()
    elif source_selection == "💻Local File":
        upload_file()

    if "df_in" in st.session_state:
        message_column_options = st.session_state["df_in"].select_dtypes(include=['object']).columns
        message_column = st.selectbox("Select message column", message_column_options, index=None)
        
        if message_column:
            st.session_state["df_in"].rename(columns={message_column: "Message_VoCI"}, inplace=True)
            st.session_state["df_current"] = pd.concat([st.session_state["df_current"], st.session_state["df_in"]])

            del st.session_state["df_in"]
            
            st.markdown('---')
            st.markdown("### Your Data")
            
            st.dataframe(st.session_state["df_current"].head(1000))
            dimensions = st.session_state["df_current"].shape
            st.markdown(f"Dimensions of the dataframe: {dimensions[0]} rows, {dimensions[1]} columns")
            download_file()

            st.page_link('1_Homepage.py', label='Add Data', icon='📥')
                
            st.markdown('---')
            st.markdown("### Analytics")
            st.page_link("pages/2_Filters.py", label="Filter Data", icon="🔍")
            st.page_link("pages/3_Sentiment.py", label="Compute Sentiment", icon="😊")
            st.page_link("pages/4_Graphtopic.py", label="Find Topics", icon="🕸️")

if __name__ == '__main__':
    main()
