import os
from openai import OpenAI
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class LLM:
    def __init__(self, logger, selected_llm="openai"):
        self.logger         = logger
        self.OPENAI_MODEL   = os.getenv("OPENAI_MODEL")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.GEMINI_MODEL   = os.getenv("GEMINI_MODEL")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.SELECTED_LLM   = selected_llm
        self.logger.info(f"{selected_llm} LLM instance initialized.")
    
    def run_llm(self, news_page_content):
        prompt = f"""

        You are a helpful AI news expert and you need to extract the following information from the news article:
        
        1. Article Date
        2. Country
        3. Region
        4. Project Title
        5. Sector
        6. China Key Leaders/Groups
        7. Country Key Leaders/Groups
        8. Date
        9. From
        10. Recipient
        11. Amount
        
        Article Content:
        {news_page_content}
        
        INSTRUCTION: 
            - Sector will only be classified any of these: 'Diplomatic', 'Information', 'Military', 'Economic', 'Financial Intelligence', 'Law Enforcement'
            - For blank values, please provide an empty string only and null is not allowed.
            - Please provide the final output as a plain JSON object provided below without any markdown or additional text and start with {{.
            - Do not wrap the json codes in JSON markers:
        EXPECTED OUTPUT:
        {{
            'article_date': '',
            'country': '',
            'region': '',
            'project_title': '',
            'sector': '',
            'china_key_leaders_groups': '',
            'country_key_leaders_groups': '',
            'date': '',
            'from': '',
            'recipient': '',
            'amount': ''
        }}
        """
        
        try:
            if self.SELECTED_LLM.lower()=="openai":            
                client   = OpenAI(api_key=self.OPENAI_API_KEY, timeout=20, max_retries=3)
                response = client.chat.completions.create(
                    model=self.OPENAI_MODEL,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                features = response.choices[0].message.content
            if self.SELECTED_LLM.lower()=="gemini":
                genai.configure(api_key=self.GEMINI_API_KEY)
                model    = genai.GenerativeModel(self.GEMINI_MODEL)
                response = model.generate_content(prompt)
                features = response.candidates[0].content.parts[0].text
            self.logger.info(f"{self.SELECTED_LLM.upper()} LLM Response: {features}")
        except Exception as e:
            self.logger.error(f"Error in extracting the information from the page_content", exc_info=True)
            features = {
                        'article_date': '',
                        'country': '',
                        'region': '',
                        'project_title': '',
                        'sector': '',
                        'china_key_leaders_groups': '',
                        'country_key_leaders_groups': '',
                        'date': '',
                        'from': '',
                        'recipient': '',
                        'amount': ''
                    }
        return features