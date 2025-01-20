import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime, date

from llm import LLM
from scrapper import ArticleScrapper
from utils import DataPreprocessor, Utils

import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s       - %(message)s [%(filename)s:%(lineno)d]',  # Custom log format
    datefmt='%Y-%m-%d %H:%M:%S'  # Custom date format
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main():
    # Set page title and configuration
    st.set_page_config(page_title="News Automation", layout="wide")
    # Get the current year
    current_year = datetime.now().year
    # Footer with dynamic year
    footer = f"""
        <style>
            .footer {{
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background-color: #f1f1f1;
                color: #333333;
                text-align: center;
                padding: 10px 0;
                font-size: 12px;
                border-top: 1px solid #e0e0e0;
            }}
        </style>
        <div class="footer">
            © {current_year} Abhishek. All rights reserved.
        </div>
    """
    st.markdown(footer, unsafe_allow_html=True)

    processed_articles = []
    output_json_file = os.path.join(os.path.dirname(__file__), '..', 'output', 'output.json')
    try:
        # Load the existing file
        with open(output_json_file, 'r', encoding='utf-8') as file:
            processed_articles = json.load(file)
            #st.success("Output JSON File loaded successfully.", icon="🟢")
    except FileNotFoundError:
        logger.error("Output JSON File not found.")
        st.error("Output JSON File not found.", icon="🔴")
        return
    
    # Define the text you want to adjust
    my_text = """
            This is a News Article Automation project. The main objective of this project is to automate the process of extracting the news articles from the urls provided and extract the features from them using llms like OpenAI and Gemini. The project is divided into the following steps:
            1. This project scrapped the data from the urls provided
            2. Extract the Features from the scrapped data using llms like openai/gemini
            3. Clean the raw data-set
            4. Do the required preprocessing
            5. Provide the final data

            Using this project you can extract the data from urls and using llms along with your prompt you will get your desired output.

            NOTE: Updated the API keys as per your selected llm. Currently configured for OPENAI and GEMINI only
        """
    
    # Initialize session state for collapse control
    if 'is_expanded' not in st.session_state:
        st.session_state.is_expanded = True

    # Create a collapse button
    with st.expander("**PROJECT HIGHLIGHTS**", expanded=st.session_state.is_expanded):
        st.markdown(my_text)

    # # Button to toggle the collapse state
    # if st.button("Toggle"):
    #     st.session_state.is_expanded = not st.session_state.is_expanded
    
    # Add title
    st.title("News Article Automation")
    
    # Input Source Selectbox
    input_src_options = ["File Upload", "Article URL"]
    selected_src_option = st.selectbox("Select News Input Source:", input_src_options, index=None)

    if selected_src_option:
        st.session_state.is_expanded = False

    # LLM model Selectbox
    llm_options = ["OpenAI", "Gemini"]
    selected_llm_option = st.selectbox("Select LLM Model:", llm_options, index=None)

    if not selected_llm_option:
        return
    else:
        llm_model         = st.text_input("LLM Model:", placeholder="gpt/gemini-flash")
        llm_model_api_key = st.text_input("LLM Model API Key:", placeholder="api-key")

        # st.write(f"Selected LLM Model: {selected_llm_option}")
        
    if selected_src_option == "File Upload":    
        fetch_article_btn = None
        # File upload section
        uploaded_file = st.file_uploader("Please attach the PDF/CSV/EXCEL or Outlook email file here", 
                                       type=['pdf', 'csv', 'excel','eml'],
                                       help="Upload your news document")
        st.warning("Note: CSV/Excel file should have the following columns: 'article_url', 'received_date'", icon="⚠️")
        # Submit button - now directly under the file upload
        fetch_article_btn = st.button("Fetch Article URLs", use_container_width=True)
        # Handle form submission
        articles = []
        # Initialize session state
        if "article_table_visible" not in st.session_state:
            st.session_state.article_table_visible = False  # Tracks if the table and button2 are visible
        if "extracted_articles" not in st.session_state:
            st.session_state.extracted_articles = pd.DataFrame({"article_urls": [], "received_date": []})  # Stores table data

        if fetch_article_btn:
            st.session_state.is_expanded = False#not st.session_state.is_expanded
            if uploaded_file is None:
                st.error("Please upload a file first!")
            else:
                # Add loading spinner while processing
                with st.spinner('Processing your file...'):
                    article_scrapper  = ArticleScrapper(logger)
                    if uploaded_file.type == 'application/pdf':                                           
                        articles = article_scrapper.scrape_pdf(uploaded_file)
                    elif uploaded_file.type == 'application/vnd.ms-outlook':
                        pass
                    elif uploaded_file.type == 'text/csv':
                        pass
                    elif uploaded_file.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                        pass
                if len(articles) > 0:
                    st.session_state.article_table_visible = True  # Set the table visibility flag to True
                    # Initialize with default data for the first time
                    data = {
                        'article_url': articles,
                        'received_date': [datetime.today()] * len(articles)
                    }
                    st.session_state.extracted_articles = pd.DataFrame(data)
                    st.session_state.extracted_articles.index = st.session_state.extracted_articles.index + 1

        # Display the Article table and button2 if the visibility flag is True
        if st.session_state.article_table_visible:
            # Add a main header for Editable table
            st.title("Extracted Articles")
            # Add a subheader
            st.subheader("Select the date you received this newsletter")
            st.session_state.extracted_articles = st.data_editor(
                st.session_state.extracted_articles, column_config={
                "article_url": st.column_config.TextColumn(
                    "article_url",
                    disabled=False
                ),
                "received_date": st.column_config.DateColumn(
                    "received_date",
                    min_value=datetime(2000, 1, 1),
                    max_value=datetime(2050, 12, 31),
                    format="DD/MM/YYYY",
                )
            },
            hide_index=False,
            num_rows="dynamic"
            )

            # Button2
            if st.button("Extract Features", use_container_width=True, key="extract_table_features_btn"):
                # Add loading spinner while processing
                with st.spinner('Scraping Articles and Extracting features from them...'):
                    # Initialize the LLM processor and Data Preprocessor
                    llm_processor     = LLM(logger, selected_llm_option, llm_model, llm_model_api_key)
                    data_preprocessor = DataPreprocessor(logger)
                    
                    # Example: Process the table data
                    for _, row in st.session_state.extracted_articles.iterrows():
                        logger.info(row)
                        # Initialize the ArticleScrapper
                        article_scrapper  = ArticleScrapper(logger)
                        article_scrapper.get_driver()
                        article_details   = Utils(logger).get_features(article_scrapper, llm_processor, data_preprocessor, row.received_date, row.article_url)
                        processed_articles.append(article_details)
                        st.success(f"Features extracted and processed successfully for Article:     {row.article_url}")
                        logger.info(f"Features extracted and processed successfully for Article:    {row.article_url}")
                        # Display file details
                        st.write("Article Details:")
                        st.json(article_details)
                        
    if selected_src_option == "Article URL":
        article_url = st.text_input("Enter your Article URL:", placeholder="https://www.example.com")
        if article_url:
            st.write(f"Article URL: {article_url}")
                
        # Date selection section
        st.subheader("Select the date you received this news letter")

        today = date.today()

        selected_date = st.date_input("Article Received Date", None)

        if selected_date:
            # Submit button - Scrape data from the URL and extract features using GenAI
            btn_extract_features = st.button("Extract Features", use_container_width=True, key="extract_article_features_btn")
            if btn_extract_features:
                if article_url:
                    # Add loading spinner while processing
                    with st.spinner('Extracting features from the article...'):
                        # Initialize the ArticleScrapper, LLM processor and Data Preprocessor
                        article_scrapper  = ArticleScrapper(logger)
                        llm_processor     = LLM(logger, selected_llm_option, llm_model, llm_model_api_key)
                        data_preprocessor = DataPreprocessor(logger)
                        article_details   = Utils(logger).get_features(article_scrapper, llm_processor, data_preprocessor, selected_date, article_url)
                        processed_articles.append(article_details)
                        st.success(f"Features extracted and processed successfully for Article: {article_url}")
                        logger.info(f"Features extracted and processed successfully for Article: {article_url}")
                        
                        # Display file details
                        st.write("Article Details:")
                        st.json(article_details)
    # Save the final ouput in JSON file
    try:
        with open(output_json_file, 'w', encoding='utf-8') as file:
            json.dump(processed_articles, file, indent=4)
        # st.success("Output JSON File saved successfully.", icon="🟢")
    except FileNotFoundError:
        logger.error("Output JSON File not found.")
        st.error("Output JSON File not found.", icon="🔴")
        return
if __name__ == "__main__":
    main()
