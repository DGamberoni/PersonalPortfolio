import streamlit as st
import pandas as pd
import numpy as np
from scipy.special import softmax
import os
from io import BytesIO
from stqdm import stqdm
import matplotlib.pyplot as plt
import plotly.express as px
stqdm.pandas()

# Preprocess text (username and link placeholders)
def preprocess(text):
    new_text = []
    for t in str(text).split(" "):
        t = '@user' if t.startswith('@') and len(t) > 1 else t
        t = 'http' if t.startswith('http') else t
        new_text.append(t)
    return " ".join(new_text)

tokenizer = st.session_state['tokenizer']
config = st.session_state['config']
model = st.session_state['model']

def get_sentiment_label(message):

    preprocessed_text = preprocess(message)
    encoded_input = tokenizer(preprocessed_text, return_tensors='pt', truncation=True, max_length=512)
    output = model(**encoded_input)
    scores = output[0][0].detach().numpy()
    scores = softmax(scores)
    ranking = np.argsort(scores)[::-1]
    top_label = config.id2label[ranking[0]]
    return top_label


def run():
    if 'df_current' in st.session_state:
        df_current = st.session_state['df_current']
        message_column = "Message_VoCI"
        st.session_state['message_column'] = message_column
        if message_column is not None and 'df_out_sentiment' not in st.session_state:
            if st.button("Compute sentiment"):

                df_current['Sentiment_VoCI'] = df_current[message_column].progress_apply(get_sentiment_label)
                st.session_state['df_current'] = df_current
                st.session_state['df_out_sentiment'] = df_current.copy()

def create_pie_chart():
    if 'df_out_sentiment' in st.session_state:
        st.markdown("### Sentiment Distribution")
        color_discrete_map = {
        'negative': '#B24C42',
        'positive': '#7E9C52',
        'neutral': '#F5F5F5'
            }
        fig = px.pie(
        st.session_state['df_out_sentiment'], 
        names='Sentiment_VoCI', 
        color='Sentiment_VoCI',  # Column for which colors will be set
        color_discrete_map=color_discrete_map
        )
        fig.update_layout(
        legend=dict(font=dict(size=16)))
        fig.update_traces(textinfo='value+percent',
                        textfont_size=16,  # Increase the font size for the labels
                        insidetextorientation='horizontal'
                            )
        
        # Display the pie chart in Streamlit
        st.plotly_chart(fig)


def download_file():
    if 'df_out_sentiment' in st.session_state:
        
        df_out_sentiment = st.session_state['df_out_sentiment']
        st.markdown("### Enriched File")
        st.dataframe(df_out_sentiment.head(1000))
        dimensions = df_out_sentiment.shape
        st.markdown(f"Dimensions of the dataframe: {dimensions[0]} rows, {dimensions[1]} columns")
        output = BytesIO()
        if 'file_in' in st.session_state:
            input_name = os.path.splitext(st.session_state['file_in'].name)[0]
        elif 'query_name' in st.session_state:
            input_name = st.session_state['query_name']
        output_name = f"{input_name}_Sentiment.xlsx"
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_out_sentiment.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            label = "Download",
            data = output,
            file_name = output_name,
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def main():
    st.set_page_config(page_title="VoCI · Sentiment", page_icon="😊")
    st.title("😊Sentiment")

    run()
    create_pie_chart()
    download_file()

    st.markdown('---')
    st.page_link("1_Homepage.py", label="Add Data", icon="📥")
    st.page_link("pages/2_Filters.py", label="Filter Data", icon="🔍")
    st.page_link("pages/4_Graphtopic.py", label="Find Topics", icon="🕸️")

if __name__ == "__main__":
    main()