import os
import io
import requests
from PIL import Image
import fitz  # PyMuPDF for PDF processing
from typing import Optional, Tuple
import tempfile
import logging

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        # OCR.space API key from environment
        self.ocr_space_api_key = os.getenv("OCR_SPACE_API_KEY")
        if self.ocr_space_api_key and self.ocr_space_api_key.strip() not in {"", "your_ocr_space_api_key_here"}:
            masked = self.ocr_space_api_key[:3] + "***" + self.ocr_space_api_key[-3:]
            logger.info(f"OCR.space API key detected: {masked} (masked)")
        else:
            logger.warning("OCR_SPACE_API_KEY missing or placeholder. OCR will fall back to EasyOCR and may be slower/less accurate.")
        
    async def extract_text_from_file(self, file_content: bytes, filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text from uploaded file (image or PDF)
        Returns: (success, extracted_text, error_message)
        """
        try:
            file_extension = filename.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                return await self._extract_from_pdf(file_content)
            elif file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif']:
                return await self._extract_from_image(file_content, filename)
            else:
                return False, None, f"Unsupported file type: {file_extension}"
                
        except Exception as e:
            logger.error(f"Error in OCR processing: {str(e)}")
            return False, None, f"OCR processing failed: {str(e)}"
    
    async def _extract_from_pdf(self, pdf_content: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
        """Extract text from PDF file"""
        try:
            # First try to extract text directly from PDF
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            extracted_text = ""
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text = page.get_text()
                extracted_text += text + "\n"
            
            pdf_document.close()
            
            # If we got meaningful text, return it
            if extracted_text.strip():
                return True, extracted_text.strip(), None
            
            # If no text found, convert PDF pages to images and use OCR
            return await self._extract_from_pdf_images(pdf_content)
            
        except Exception as e:
            logger.error(f"PDF processing error: {str(e)}")
            return False, None, f"PDF processing failed: {str(e)}"
    
    async def _extract_from_pdf_images(self, pdf_content: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
        """Convert PDF pages to images and extract text using OCR"""
        try:
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            all_text = ""
            
            for page_num in range(min(pdf_document.page_count, 10)):  # Limit to 10 pages
                page = pdf_document[page_num]
                # Convert page to image
                mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Extract text from image
                success, text, error = await self._extract_from_image(img_data, f"page_{page_num}.png")
                if success and text:
                    all_text += f"--- Page {page_num + 1} ---\n{text}\n\n"
            
            pdf_document.close()
            
            if all_text.strip():
                return True, all_text.strip(), None
            else:
                return False, None, "No text could be extracted from PDF"
                
        except Exception as e:
            logger.error(f"PDF to image OCR error: {str(e)}")
            return False, None, f"PDF OCR processing failed: {str(e)}"
    
    async def _extract_from_image(self, image_content: bytes, filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Extract text from image using OCR.space API or fallback methods"""
        
        # Try OCR.space API first (cloud-based, no local installation needed)
        if self.ocr_space_api_key:
            try:
                return await self._ocr_space_extract(image_content)
            except Exception as e:
                logger.warning(f"OCR.space failed, trying fallback: {str(e)}")
        
        # Fallback to EasyOCR (works without local Tesseract installation)
        try:
            return await self._easyocr_extract(image_content)
        except Exception as e:
            logger.warning(f"EasyOCR failed: {str(e)}")
        
        # Final fallback - return error
        return False, None, "OCR processing failed. Please ensure the image contains clear, readable text."
    
    async def _ocr_space_extract(self, image_content: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
        """Extract text using OCR.space API with retries and better defaults"""
        if not self.ocr_space_api_key or self.ocr_space_api_key.strip() in {"", "your_ocr_space_api_key_here"}:
            # Explicit message when API key is missing/placeholder
            raise Exception("OCR_SPACE_API_KEY not configured. Add it to your .env and restart the server.")
        
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
            'isTable': False,
            'isCreateSearchablePdf': False,
            'OCREngine': 2
        }
        
        # Retry on transient errors (429/5xx)
        backoffs = [0, 1.0, 2.0]
        last_err = None
        for delay in backoffs:
            if delay:
                import time as _t
                _t.sleep(delay)
            try:
                response = requests.post(url, files=files, data=data, timeout=60)
                status = response.status_code
                if status >= 500 or status == 429:
                    last_err = Exception(f"OCR.space transient error: HTTP {status}")
                    continue
                response.raise_for_status()
                result = response.json()

                if result.get('IsErroredOnProcessing', False):
                    # Prefer detailed messages if available
                    err_list = result.get('ErrorMessage') or result.get('ErrorDetails')
                    error_msg = (err_list[0] if isinstance(err_list, list) and err_list else err_list) or 'Unknown error'
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
                last_err = e
                logger.warning(f"OCR.space request attempt failed: {e}")
                continue
            except Exception as e:
                last_err = e
                logger.warning(f"OCR.space processing attempt failed: {e}")
                continue

        logger.error(f"OCR.space API failed after retries: {last_err}")
        raise Exception(f"OCR.space API request failed after retries: {last_err}")
    
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
ocr_service = OCRService()