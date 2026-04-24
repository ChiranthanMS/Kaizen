"""
Fallback OCR service that tries multiple OCR providers
"""
import os
import logging
from typing import Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class FallbackOCRService:
    """OCR service with multiple provider fallbacks"""
    
    def __init__(self):
        self.ocr_space_available = bool(os.getenv("OCR_SPACE_API_KEY"))
        self.google_vision_available = bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        
    def is_available(self) -> bool:
        """Check if at least one OCR service is available"""
        return self.ocr_space_available or self.google_vision_available
    
    async def extract_text_from_file(self, file_content: bytes, filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text using fallback strategy: OCR.Space first, then Google Vision
        
        Args:
            file_content (bytes): The file content as bytes
            filename (str): Original filename
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, extracted_text, error_message)
        """
        errors = []
        
        # Try OCR.Space first (faster and cheaper)
        if self.ocr_space_available:
            try:
                from services.ocr_space_service import ocr_space_service
                logger.info(f"Trying OCR.Space for {filename}")
                
                success, text, error = await ocr_space_service.extract_text_from_file(
                    file_content, filename, max_retries=2  # Reduced retries for faster fallback
                )
                
                if success and text:
                    logger.info(f"OCR.Space successful for {filename}")
                    return True, text, None
                else:
                    errors.append(f"OCR.Space: {error}")
                    logger.warning(f"OCR.Space failed for {filename}: {error}")
                    
            except Exception as e:
                error_msg = f"OCR.Space exception: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"OCR.Space exception for {filename}: {e}")
        
        # Fallback to Google Vision API
        if self.google_vision_available:
            try:
                from services.google_vision_service import google_vision_service
                logger.info(f"Falling back to Google Vision for {filename}")
                
                success, text, error = await google_vision_service.extract_text_from_file(
                    file_content, filename
                )
                
                if success and text:
                    logger.info(f"Google Vision successful for {filename}")
                    return True, text, None
                else:
                    errors.append(f"Google Vision: {error}")
                    logger.warning(f"Google Vision failed for {filename}: {error}")
                    
            except Exception as e:
                error_msg = f"Google Vision exception: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"Google Vision exception for {filename}: {e}")
        
        # All OCR services failed
        combined_error = " | ".join(errors) if errors else "No OCR services available"
        logger.error(f"All OCR services failed for {filename}: {combined_error}")
        
        return False, None, combined_error

# Global fallback service instance
fallback_ocr_service = FallbackOCRService()