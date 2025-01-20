import os
import requests
import tempfile
import pymupdf4llm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from langchain.docstore.document import Document

from utils import Utils

class ArticleScrapper:
    def __init__(self, logger):
        self.logger = logger
        self.driver = None
        self.logger.info(f"ArticleScrapper instance initialized.")
    
    def get_driver(self):
        try:        
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            # Setup the webdriver
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), 
                options=chrome_options
            )
            self.logger.info("CHROME DRIVER IS READY.")
            self.driver = driver
        except Exception as e:
            self.logger.error(f"Error in downloading and installing chrome webdriver.", exc_info=True)
            return None
        
    def close_driver(self):
        if self.driver:
            self.driver.quit()
            self.logger.info("Chrome driver closed successfully.")

    def extract_content_selenium(self, url):
        """
        Extract web page content using Selenium with Chrome
        
        Args:
            url (str): URL to extract content from
        
        Returns:
            Document: Extracted web content
        """
        try:                
            # Navigate to the page
            self.driver.get(url)
            
            # Wait for potential dynamic content to load
            self.driver.implicitly_wait(10)
            
            # Get page source
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Remove script, style, and other non-content tags
            for script in soup(["script", "style", "head", "title", "meta", "nav"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            cleaned_text = ' '.join(lines)
            
            self.logger.info(f"Selenium Extracted text: {cleaned_text[:50]}...")
            # Close the driver
            self.close_driver()
            
            # Return as LangChain Document
            return Document(
                page_content=cleaned_text,
                metadata={
                    'source': url,
                    'title': soup.title.string if soup.title else 'No Title'
                }
            )
        
        except Exception as e:
            self.logger.error(f"Selenium extraction error: {e}", exc_info=True)
            return None
        
    def extract_content_requests(self, url):
        """
        Extract web page content using requests and BeautifulSoup
        
        Args:
            url (str): URL to extract content from
        
        Returns:
            Document: Extracted web content
        """
        try:
            # Setup headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            # Send request
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script, style, and other non-content tags
            for script in soup(["script", "style", "head", "title", "meta", "nav"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            cleaned_text = ' '.join(lines)

            self.logger.info(f"BeautifulSoup Extracted text: {cleaned_text[:50]}...")
            # Return as LangChain Document
            return Document(
                page_content=cleaned_text,
                metadata={
                    'source': url,
                    'title': soup.title.string if soup.title else 'No Title'
                }
            )
        
        except Exception as e:
            self.logger.error(f"BeautifulSoup extraction error: {e}", exc_info=True)
            return None
    
    def extract_web_content(self, url):
        """
        Multiple strategy web content extraction
        
        Args:
            url (str): URL to extract content from
        
        Returns:
            Document: Extracted web content
        """
        # Try Selenium first (better for JS-heavy sites)
        document = self.extract_content_selenium(url)
        
        # Fallback to requests method
        if not document or not document.page_content.strip():
            document = self.extract_content_requests(url)
        
        return document

    def scrape_pdf(self, uploaded_file):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name
            # Extract text from PDF
            text=pymupdf4llm.to_markdown(tmp_path)
            article_urls=Utils(self.logger).extract_urls(text)
            self.logger.info(f"Extracted URLs: {article_urls}")
            return article_urls
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {str(e)}", exc_info=True)
            return None
        finally:
            # Clean up the temporary file - this ensures deletion even if an error occurs
            os.unlink(tmp_path)
    