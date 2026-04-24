import os
import io
import requests
from PIL import Image
from typing import Optional, Tuple
import tempfile
import logging

logger = logging.getLogger(__name__)

class SimpleOCRService:
    def __init__(self):
        # OCR.space API key from environment
        self.ocr_space_api_key = os.getenv("OCR_SPACE_API_KEY")
        
    async def extract_text_from_file(self, file_content: bytes, filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text from uploaded file (image only for now)
        Returns: (success, extracted_text, error_message)
        """
        try:
            file_extension = filename.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                return False, None, "PDF processing requires additional dependencies. Please use image files for now."
            elif file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif']:
                return await self._extract_from_image(file_content, filename)
            else:
                return False, None, f"Unsupported file type: {file_extension}"
                
        except Exception as e:
            logger.error(f"Error in OCR processing: {str(e)}")
            return False, None, f"OCR processing failed: {str(e)}"
    
    async def _extract_from_image(self, image_content: bytes, filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Extract text from image using OCR.space API or fallback methods"""
        
        # Try OCR.space API first (cloud-based, no local installation needed)
        if self.ocr_space_api_key and self.ocr_space_api_key != "your_ocr_space_api_key_here":
            try:
                return await self._ocr_space_extract(image_content)
            except Exception as e:
                logger.warning(f"OCR.space failed, trying fallback: {str(e)}")
        
        # Fallback to EasyOCR (works without local Tesseract installation)
        try:
            return await self._easyocr_extract(image_content)
        except Exception as e:
            logger.warning(f"EasyOCR failed: {str(e)}")
        
        # Final fallback - return error with helpful message
        return False, None, "OCR processing failed. Please ensure the image contains clear, readable text. For better results, consider getting a free API key from https://ocr.space/ocrapi and adding it to your .env file as OCR_SPACE_API_KEY."
    
    async def _ocr_space_extract(self, image_content: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
        """Extract text using OCR.space API"""
        try:
            url = "https://api.ocr.space/parse/image"
            
            files = {
                'file': ('image.png', image_content, 'image/png')
            }
            
            data = {
                'apikey': self.ocr_space_api_key,
                'language': 'eng',
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2  # Use OCR Engine 2 for better accuracy
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('IsErroredOnProcessing', False):
                error_msg = result.get('ErrorMessage', ['Unknown error'])[0]
                return False, None, f"OCR.space error: {error_msg}"
            
            parsed_results = result.get('ParsedResults', [])
            if not parsed_results:
                return False, None, "No text found in image"
            
            extracted_text = parsed_results[0].get('ParsedText', '').strip()
            
            if extracted_text:
                return True, extracted_text, None
            else:
                return False, None, "No text could be extracted from the image"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"OCR.space API request failed: {str(e)}")
            raise Exception(f"OCR.space API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"OCR.space processing error: {str(e)}")
            raise Exception(f"OCR.space processing error: {str(e)}")
    
    async def _easyocr_extract(self, image_content: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
        """Extract text using EasyOCR (fallback method)"""
        try:
            import easyocr
            
            # Create EasyOCR reader
            reader = easyocr.Reader(['en'], gpu=False)  # Use CPU to avoid GPU dependencies
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save to temporary file for EasyOCR
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                image.save(temp_file.name, 'PNG')
                temp_path = temp_file.name
            
            try:
                # Extract text
                results = reader.readtext(temp_path)
                
                # Combine all detected text
                extracted_text = ' '.join([result[1] for result in results if result[2] > 0.5])  # Confidence > 0.5
                
                if extracted_text.strip():
                    return True, extracted_text.strip(), None
                else:
                    return False, None, "No text could be extracted from the image"
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except ImportError:
            raise Exception("EasyOCR not available. Please install with: pip install easyocr")
        except Exception as e:
            logger.error(f"EasyOCR processing error: {str(e)}")
            raise Exception(f"EasyOCR processing error: {str(e)}")

# Global OCR service instance
simple_ocr_service = SimpleOCRService()