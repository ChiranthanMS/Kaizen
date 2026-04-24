import os
import requests
import logging
import time
import asyncio
from typing import Tuple, Optional
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
load_dotenv(backend_dir / ".env")
load_dotenv(project_root / ".env", override=True)

logger = logging.getLogger(__name__)

class OCRSpaceError(Exception):
    """Custom exception for OCR.Space API errors"""
    pass

def extract_text_ocr_space(image_path: str, max_retries: int = 3) -> str:
    """
    Extract text from an image using OCR.Space API with retry logic.
    
    Args:
        image_path (str): Path to the image file
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        str: Extracted text from the image
        
    Raises:
        OCRSpaceError: If OCR extraction fails after all retries
    """
    api_key = os.getenv("OCR_SPACE_API_KEY")
    if not api_key:
        raise OCRSpaceError("OCR_SPACE_API_KEY not found in environment variables")
    
    if not os.path.exists(image_path):
        raise OCRSpaceError(f"Image file not found: {image_path}")
    
    # Try different timeout values and engines
    retry_configs = [
        {'timeout': 30, 'engine': 2},  # First try: 30s timeout, Engine 2
        {'timeout': 45, 'engine': 1},  # Second try: 45s timeout, Engine 1
        {'timeout': 60, 'engine': 2},  # Third try: 60s timeout, Engine 2
    ]
    
    last_error = None
    
    for attempt in range(max_retries):
        config = retry_configs[min(attempt, len(retry_configs) - 1)]
        
        try:
            logger.info(f"OCR attempt {attempt + 1}/{max_retries} for {image_path} (timeout: {config['timeout']}s, engine: {config['engine']})")
            
            # OCR.Space API endpoint
            url = "https://api.ocr.space/parse/image"
            
            # Prepare the request
            with open(image_path, 'rb') as image_file:
                files = {
                    'file': image_file
                }
                
                data = {
                    'apikey': api_key,
                    'language': 'eng',
                    'isOverlayRequired': False,
                    'detectOrientation': True,
                    'isTable': True,
                    'scale': True,
                    'OCREngine': config['engine'],
                }
                
                # Make the API request with configurable timeout
                response = requests.post(url, files=files, data=data, timeout=config['timeout'])
                
                # Check HTTP status
                if response.status_code != 200:
                    raise OCRSpaceError(f"OCR.Space API returned status {response.status_code}: {response.text}")
                
                # Parse JSON response
                result = response.json()
                
                # Check if OCR was successful
                if not result.get('IsErroredOnProcessing', True):
                    # Extract text from parsed results
                    parsed_results = result.get('ParsedResults', [])
                    if parsed_results and len(parsed_results) > 0:
                        extracted_text = parsed_results[0].get('ParsedText', '').strip()
                        
                        if extracted_text:
                            logger.info(f"OCR successful on attempt {attempt + 1}. Extracted {len(extracted_text)} characters")
                            return extracted_text
                        else:
                            raise OCRSpaceError("No text detected in the image")
                    else:
                        raise OCRSpaceError("No parsed results returned from OCR.Space API")
                else:
                    # Handle OCR processing errors
                    error_message = result.get('ErrorMessage', 'Unknown OCR processing error')
                    error_details = result.get('ErrorDetails', '')
                    full_error = f"{error_message}. {error_details}".strip()
                    raise OCRSpaceError(f"OCR processing failed: {full_error}")
                    
        except requests.exceptions.Timeout as e:
            last_error = f"Timeout after {config['timeout']}s: {str(e)}"
            logger.warning(f"OCR attempt {attempt + 1} timed out: {last_error}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            continue
            
        except requests.exceptions.RequestException as e:
            last_error = f"Network error: {str(e)}"
            logger.warning(f"OCR attempt {attempt + 1} failed: {last_error}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            continue
            
        except Exception as e:
            if isinstance(e, OCRSpaceError):
                last_error = str(e)
                logger.warning(f"OCR attempt {attempt + 1} failed: {last_error}")
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                continue
            else:
                logger.error(f"Unexpected error during OCR: {e}")
                raise OCRSpaceError(f"Unexpected error: {str(e)}")
    
    # All retries failed
    logger.error(f"All {max_retries} OCR attempts failed. Last error: {last_error}")
    raise OCRSpaceError(f"OCR failed after {max_retries} attempts. Last error: {last_error}")

class OCRSpaceService:
    """Service class for OCR.Space API operations"""
    
    def __init__(self):
        self.api_key = os.getenv("OCR_SPACE_API_KEY")
        
    def is_available(self) -> bool:
        """Check if OCR.Space API is available (API key is configured)"""
        return bool(self.api_key)
    
    async def extract_text_from_file(self, file_content: bytes, filename: str, max_retries: int = 3) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text from file content using OCR.Space API with retry logic.
        
        Args:
            file_content (bytes): The file content as bytes
            filename (str): Original filename
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, extracted_text, error_message)
        """
        import tempfile
        import os
        
        if not self.is_available():
            return False, None, "OCR.Space API key not configured"
        
        # Create temporary file
        temp_file_path = None
        try:
            # Create temporary file with appropriate extension
            file_extension = os.path.splitext(filename)[1].lower()
            if not file_extension:
                file_extension = '.jpg'  # Default extension
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Extract text using OCR.Space with retry logic
            extracted_text = await asyncio.get_event_loop().run_in_executor(
                None, extract_text_ocr_space, temp_file_path, max_retries
            )
            return True, extracted_text, None
            
        except OCRSpaceError as e:
            logger.error(f"OCR.Space error for {filename}: {e}")
            return False, None, str(e)
        except Exception as e:
            logger.error(f"Unexpected error during OCR for {filename}: {e}")
            return False, None, f"Unexpected error: {str(e)}"
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Could not delete temporary file {temp_file_path}: {e}")

# Global service instance
ocr_space_service = OCRSpaceService()