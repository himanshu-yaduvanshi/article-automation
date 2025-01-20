import re
import string
import pandas as pd
from ast import literal_eval
from datetime import datetime
from babel.dates import parse_date

class DataPreprocessor:
    def __init__(self, logger):
        self.logger = logger
        self.logger.info(f"DataPreprocessor instance initialized.")
        
    def clean_and_parse_features(self, features):
        if not features or pd.isna(features):
            return {}
        elif isinstance(features, dict):
            return features
        try:
            # Replace smart quotes with regular quotes
            features = features.replace("artical_date", "article_date")
            features = features.replace("dimpfel_classifiation", "dimpfel_classification")
            features = features.replace("```json", "").replace("```", "")
            features = features.replace('"', '"').replace('"', '"')
            features = features.replace("'", "'").replace("'", "'")
            features = literal_eval(features)
            self.logger.info("Feature Preprocessing: Features are successfully cleaned and parsed.")
            return features
        except Exception as e:
            self.logger.error(f"Feature Preprocessing: Error cleaning and parsing features: {str(e)}", exc_info=True)
            return {}
            
    def clean_date_string(self, date_str):
        """
        Clean and normalize date string before parsing
        """
        if not isinstance(date_str, str):
            return None
            
        # Remove extra whitespace
        date_str = date_str.strip()
        
        # Handle empty strings
        if not date_str or date_str.lower() in ['', 'none', 'null']:
            return None
            
        # Handle date ranges - take the first date
        if ' to ' in date_str:
            date_str = date_str.split(' to ')[0]
            
        # Remove timezone information if present
        date_str = re.sub(r'\s*\([^)]*\)', '', date_str)
        
        # Remove ordinal indicators
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        
        # Normalize Spanish/Portuguese date format
        date_str = date_str.lower()
        date_str = date_str.replace('de ', '')
        date_str = date_str.replace(',', '')
        date_str = date_str.replace('lunes ', '')
        date_str = date_str.replace('martes ', '')
        date_str = date_str.replace('miércoles ', '')
        date_str = date_str.replace('jueves ', '')
        date_str = date_str.replace('viernes ', '')
        date_str = date_str.replace('sábado ', '')
        date_str = date_str.replace('domingo ', '')
        
        # Handle partial dates or special cases
        if re.match(r'^\d{4}$', date_str):  # Just year
            return f"01-01-{date_str}"
        if re.match(r'^(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}$', date_str, re.I):
            month, year = date_str.split()
            return f"01-{datetime.strptime(month, '%B').month:02d}-{year}"
            
        return date_str

    def standardize_date(self, date_str, source_locale='en'):
        """
        Convert dates from different languages to DD-MM-YYYY format
        """
        if not isinstance(date_str, str):
            return None
            
        # Clean the date string
        date_str = self.clean_date_string(date_str)
        if not date_str:
            return None
            
        # Special cases
        special_cases = {
            'last month': (datetime.now().replace(day=1) - pd.DateOffset(months=1)).strftime("%d-%m-%Y"),
            'last year': (datetime.now() - pd.DateOffset(years=1)).strftime("%d-%m-%Y"),
            '2020 to present': '01-01-2020',
            '2019 - last year': '01-01-2019'
        }
        
        if date_str.lower() in special_cases:
            return special_cases[date_str.lower()]
            
        try:
            # Month name translations
            month_translations = {
                'enero': 'january', 'febrero': 'february', 'marzo': 'march',
                'abril': 'april', 'mayo': 'may', 'junio': 'june',
                'julio': 'july', 'agosto': 'august', 'septiembre': 'september',
                'octubre': 'october', 'noviembre': 'november', 'diciembre': 'december',
                'janeiro': 'january', 'fevereiro': 'february', 'março': 'march',
                'abril': 'april', 'maio': 'may', 'junho': 'june',
                'julho': 'july', 'agosto': 'august', 'setembro': 'september',
                'outubro': 'october', 'novembro': 'november', 'dezembro': 'december'
            }
            
            # Replace month names with English versions
            for es_month, en_month in month_translations.items():
                date_str = date_str.lower().replace(es_month, en_month)
            
            # Try different date formats
            formats = [
                "%d-%m-%Y",                # 25-12-2023
                "%Y-%m-%d",                # 2023-12-25
                "%d/%m/%Y",                # 25/12/2023
                "%d.%m.%Y",                # 25.12.2023
                "%d %B %Y",                # 25 December 2023
                "%d %b %Y",                # 25 Dec 2023
                "%d %b, %Y",               # 25 Dec, 2023
                "%B %d %Y",                # December 25 2023
                "%b %d %Y",                # Dec 25 2023
                "%d-%b-%Y",                # 25-Dec-2023
                "%d %m %Y",                # 25 12 2023
                "%b-%d-%Y",                # Dec-25-2023
                "%Y%m%d",                  # 20231225
                "%d%m%Y",                  # 25122023
                "%d %B, %Y",               # 25 December, 2023
                "%B %d, %Y",               # December 25, 2023
                "%d-%B-%Y"                 # 25-December-2023
            ]
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime("%d-%m-%Y")
                except:
                    continue
                    
            # Try babel parsing as last resort
            try:
                date_obj = parse_date(date_str, locale=source_locale)
                return date_obj.strftime("%d-%m-%Y")
            except:
                pass
                    
            raise ValueError(f"Could not parse date: {date_str}")
            
        except Exception as e:
            self.logger.error(f"Error processing date '{date_str}': {str(e)}", exc_info=True)
            return date_str

class Utils:
    def __init__(self, logger):
        self.logger = logger
    
    def extract_urls(self, text):
        """
        Extracts clean URLs from text while filtering out common PDF artifacts and invalid URL parts.
        """
        # More comprehensive URL pattern
        url_pattern = r'https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        
        # Find all matches
        urls = re.findall(url_pattern, text)
        
        # Clean up URLs
        cleaned_urls = []
        for url in urls:
            # Remove common PDF artifacts and invalid URL endings
            url = re.sub(r'\).*$', '', url)  # Remove everything after closing parenthesis
            url = re.sub(r'\].*$', '', url)  # Remove everything after closing bracket
            url = re.sub(r'["\'\]].*$', '', url)  # Remove quotes and anything after
            url = url.split('external-destination=')[0]  # Remove PDF metadata
            
            # Basic URL validation
            if all(char in string.printable for char in url):  # Check for valid characters
                if not any(x in url for x in ['[', ']', ')', '(', '"', "'"]):  # No brackets or quotes
                    cleaned_urls.append(url.strip())
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(cleaned_urls))
    
    def get_features(self, article_scrapper, llm_processor, data_preprocessor, selected_date, article_url):
        # Extract the web content
        page_document     = article_scrapper.extract_web_content(article_url)
        features          = llm_processor.run_llm(page_document.page_content)
        # Here you would add your URL processing logic
        features                 = data_preprocessor.clean_and_parse_features(features)
        features['article_date'] = data_preprocessor.standardize_date(features.get('article_date'))
        features['date']         =  data_preprocessor.standardize_date(features.get('date'))

        article_details = {
            "article_received_month": selected_date.strftime("%B") + " " + str(selected_date.year),
            "article_url": article_url,
            "page_source": page_document.metadata.get('source'),
            "page_title" : page_document.metadata.get('title'),
            'page_content' : page_document.page_content,
        }
        article_details.update(features)
        return article_details



    # Function to expand the dictionary column into separate columns
    def expand_dict_column(self, df, dict_column):
        # Convert the dictionary column to actual dictionaries
        df[dict_column] = df[dict_column].apply(eval if isinstance(df[dict_column].iloc[0], str) else lambda x: x)
        # Expand the dictionary into separate columns
        expanded_df = pd.json_normalize(df[dict_column])#.dropna(axis=1, how='all')
        self.logger.info("\n")
        self.logger.info(expanded_df.columns)
        # expanded_df = pd.json_normalize(df[dict_column].tolist())
        # Drop the original dictionary column and concatenate with expanded columns
        result = pd.concat([df, expanded_df], axis=1)
        return result
    
    # def create_table(self, st, articles):
    #     # Add a main header
    #     st.title("Extracted Articles")

    #     # Add a subheader
    #     st.subheader("Select the date you received this news letter")
    #     # Create initial data
    #     data = {
    #         'Article': articles,
    #         'Received Date': [datetime.today()] * len(articles)  # Initialize with today's date
    #     }

    #     # Create DataFrame
    #     df = pd.DataFrame(data)
    #     # Reset index to start from 1
    #     df.index = df.index + 1

    #     # Use Streamlit's data editor
    #     edited_df = st.data_editor(
    #         df,
    #         column_config={
    #             "Article": st.column_config.TextColumn(
    #                 "Article",
    #                 disabled=False  # Make Link column read-only
    #             ),
    #             "Received Date": st.column_config.DateColumn(
    #                 "Received Date",
    #                 min_value=datetime(2000, 1, 1),
    #                 max_value=datetime(2050, 12, 31),
    #                 format="DD/MM/YYYY",
    #             )
    #         },
    #         hide_index=False,
    #         num_rows="fixed"
    #     )

    #     return edited_df
    def create_table(self, st, articles):
        # Add a main header
        st.title("Extracted Articles")

        # Add a subheader
        st.subheader("Select the date you received this newsletter")

        # Initialize session state if it doesn't exist
        if 'extracted_articles' not in st.session_state:
            # Create initial data
            data = {
                'Article': articles,
                'Received Date': [datetime.today()] * len(articles)
            }
            st.session_state.table_data = pd.DataFrame(data)
            st.session_state.table_data.index = st.session_state.table_data.index + 1

        # Use Streamlit's data editor
        st.session_state.table_data = st.data_editor(
            st.session_state.table_data,
            column_config={
                "Article": st.column_config.TextColumn(
                    "Article",
                    disabled=False
                ),
                "Received Date": st.column_config.DateColumn(
                    "Received Date",
                    min_value=datetime(2000, 1, 1),
                    max_value=datetime(2050, 12, 31),
                    format="DD/MM/YYYY",
                )
            },
            hide_index=False,
            num_rows="fixed",
            key="editor_data"
        )
        return st.session_state.table_data