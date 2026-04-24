import logging
import time
from typing import Dict, Any, Optional, Tuple
from services.ocr_space_service import ocr_space_service
from services.gemini_service import gemini_service
from services.regex_bill_parser import regex_bill_parser

logger = logging.getLogger(__name__)

class EnhancedBillProcessor:
    """
    Enhanced bill processing service that combines:
    1. OCR.Space for text extraction (primary)
    2. Gemini 2.0 Flash for intelligent parsing (primary)
    3. Regex parser as fallback
    """
    
    def __init__(self):
        self.ocr_service = ocr_space_service
        self.ai_parser = gemini_service
        self.fallback_parser = regex_bill_parser
    
    async def process_bill(self, file_content: bytes, filename: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Process a bill file through the complete pipeline
        
        Args:
            file_content: The file content as bytes
            filename: Original filename
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (success, bill_data, error_message)
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting enhanced bill processing for {filename}")
            
            # Step 1: Extract text using OCR.Space
            ocr_success, raw_text, ocr_error = await self.ocr_service.extract_text_from_file(
                file_content, filename
            )
            
            if not ocr_success or not raw_text:
                logger.error(f"OCR extraction failed for {filename}: {ocr_error}")
                return False, None, f"OCR extraction failed: {ocr_error}"
            
            if len(raw_text.strip()) < 10:
                logger.warning(f"Insufficient text extracted from {filename}")
                return False, None, "Insufficient text extracted from the image"
            
            logger.info(f"OCR successful for {filename}. Extracted {len(raw_text)} characters")
            
            # Step 2: Try Gemini 2.0 Flash for intelligent parsing
            bill_data = None
            parsing_method = "unknown"
            confidence_score = 0.0
            
            if self.ai_parser.is_available():
                try:
                    logger.info(f"Attempting Gemini 2.0 Flash parsing for {filename}")
                    gemini_data, gemini_error = await self.ai_parser.analyze_bill_async(raw_text, filename)
                    
                    if gemini_data and gemini_error is None:
                        bill_data = gemini_data
                        parsing_method = "gemini_2_flash"
                        confidence_score = gemini_data.get('confidence_score', 0.8)
                        logger.info(f"Gemini parsing successful for {filename} with confidence {confidence_score}")
                    else:
                        logger.warning(f"Gemini parsing failed for {filename}: {gemini_error}")
                        
                except Exception as e:
                    logger.error(f"Gemini parsing error for {filename}: {e}")
            else:
                logger.warning("Gemini API not available, skipping AI parsing")
            
            # Step 3: Fallback to regex parser if Gemini failed or confidence is low
            if (bill_data is None or 
                confidence_score < 0.6 or 
                not bill_data.get('amount') or 
                not bill_data.get('vendor')):
                
                logger.info(f"Using regex fallback parser for {filename}")
                try:
                    regex_data = self.fallback_parser.parse_bill_data(raw_text, filename)
                    
                    if bill_data is None:
                        # Use regex data as primary
                        bill_data = regex_data
                        parsing_method = "regex_fallback"
                        confidence_score = regex_data.get('confidence_score', 0.5)
                    else:
                        # Merge regex data to fill missing fields
                        bill_data = self._merge_bill_data(bill_data, regex_data)
                        parsing_method = "gemini_regex_hybrid"
                        confidence_score = max(confidence_score, regex_data.get('confidence_score', 0.5))
                    
                    logger.info(f"Regex parsing completed for {filename} with method {parsing_method}")
                    
                except Exception as e:
                    logger.error(f"Regex parsing error for {filename}: {e}")
                    if bill_data is None:
                        return False, None, f"All parsing methods failed: {e}"
            
            # Step 4: Validate and enhance the final data
            if bill_data is None:
                return False, None, "No parsing method succeeded"
            
            # Add processing metadata
            processing_time = time.time() - start_time
            bill_data.update({
                'raw_text': raw_text,
                'processing_time': processing_time,
                'parsing_method': parsing_method,
                'confidence_score': confidence_score,
                'filename': filename
            })
            
            # Validate required fields
            validation_result = self._validate_bill_data(bill_data)
            if not validation_result['valid']:
                logger.warning(f"Bill data validation failed for {filename}: {validation_result['errors']}")
                # Don't fail completely, but lower confidence
                bill_data['confidence_score'] = max(0.3, bill_data['confidence_score'] - 0.2)
                bill_data['validation_warnings'] = validation_result['errors']
            
            logger.info(f"Enhanced bill processing completed for {filename} in {processing_time:.2f}s")
            return True, bill_data, None
            
        except Exception as e:
            logger.error(f"Unexpected error in enhanced bill processing for {filename}: {e}")
            return False, None, f"Processing error: {str(e)}"
    
    def _merge_bill_data(self, primary_data: Dict[str, Any], fallback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge bill data from primary and fallback parsers
        Primary data takes precedence, fallback fills missing fields
        """
        merged = primary_data.copy()
        
        # Fields to merge if missing or None in primary
        merge_fields = [
            'amount', 'date', 'vendor', 'category', 'subtotal', 'tax', 
            'discount', 'currency', 'payment_method', 'invoice_number',
            'description', 'travel_from', 'travel_to'
        ]
        
        for field in merge_fields:
            if not merged.get(field) and fallback_data.get(field):
                merged[field] = fallback_data[field]
                logger.debug(f"Merged {field} from fallback parser: {fallback_data[field]}")
        
        return merged
    
    def _validate_bill_data(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted bill data
        
        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        errors = []
        
        # Check required fields
        if not bill_data.get('amount'):
            errors.append("Missing amount")
        elif not isinstance(bill_data['amount'], (int, float)) or bill_data['amount'] <= 0:
            errors.append("Invalid amount value")
        
        if not bill_data.get('vendor'):
            errors.append("Missing vendor name")
        
        if not bill_data.get('date'):
            errors.append("Missing date")
        elif bill_data.get('date'):
            # Validate date format
            import re
            if not re.match(r'\d{4}-\d{2}-\d{2}', str(bill_data['date'])):
                errors.append("Invalid date format (should be YYYY-MM-DD)")
        
        # Validate category
        valid_categories = ['food', 'travel', 'rent', 'miscellaneous']
        if bill_data.get('category') not in valid_categories:
            errors.append(f"Invalid category: {bill_data.get('category')}")
        
        # Validate currency
        valid_currencies = ['INR', 'USD', 'EUR', 'GBP', 'other']
        if bill_data.get('currency') not in valid_currencies:
            errors.append(f"Invalid currency: {bill_data.get('currency')}")
        
        # Validate payment method
        valid_payment_methods = ['cash', 'card', 'upi', 'netbanking', 'cheque', 'other']
        if bill_data.get('payment_method') not in valid_payment_methods:
            errors.append(f"Invalid payment method: {bill_data.get('payment_method')}")
        
        # Validate confidence score
        confidence = bill_data.get('confidence_score', 0)
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            errors.append("Invalid confidence score")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        return {
            'ocr_space': {
                'available': self.ocr_service.is_available(),
                'service': 'OCR.Space API'
            },
            'gemini': {
                'available': self.ai_parser.is_available(),
                'service': 'Gemini 2.0 Flash'
            },
            'regex_fallback': {
                'available': True,
                'service': 'Regex Pattern Parser'
            },
            'processing_pipeline': 'OCR.Space → Gemini 2.0 Flash → Regex Fallback'
        }

# Global service instance
enhanced_bill_processor = EnhancedBillProcessor()