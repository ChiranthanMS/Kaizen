import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import calendar

logger = logging.getLogger(__name__)

class RegexBillParser:
    """Regex-based fallback parser for bill data extraction"""
    
    def __init__(self):
        # Compile regex patterns for better performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all regex patterns"""
        
        # Amount patterns (various formats)
        self.amount_patterns = [
            re.compile(r'(?:total|amount|sum|bill|pay|due)[\s:]*(?:rs\.?|₹|inr)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            re.compile(r'(?:₹|rs\.?|inr)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            re.compile(r'(\d+(?:,\d{3})*(?:\.\d{2})?)(?:\s*(?:₹|rs\.?|inr))', re.IGNORECASE),
            re.compile(r'total[\s:]*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            re.compile(r'amount[\s:]*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
        ]
        
        # Date patterns (various formats)
        self.date_patterns = [
            re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', re.IGNORECASE),  # DD/MM/YYYY or DD-MM-YYYY
            re.compile(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', re.IGNORECASE),  # YYYY/MM/DD or YYYY-MM-DD
            re.compile(r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})', re.IGNORECASE),  # DD MMM YYYY
            re.compile(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2}),?\s+(\d{4})', re.IGNORECASE),  # MMM DD, YYYY
            re.compile(r'date[\s:]*(\d{1,2})[/-](\d{1,2})[/-](\d{4})', re.IGNORECASE),
        ]
        
        # Tax patterns
        self.tax_patterns = [
            re.compile(r'(?:tax|gst|vat|cgst|sgst|igst)[\s:]*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            re.compile(r'(?:₹|rs\.?|inr)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)(?:\s*(?:tax|gst|vat))', re.IGNORECASE),
        ]
        
        # Subtotal patterns
        self.subtotal_patterns = [
            re.compile(r'(?:subtotal|sub-total|sub total)[\s:]*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            re.compile(r'(?:before tax|pre-tax)[\s:]*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
        ]
        
        # Discount patterns
        self.discount_patterns = [
            re.compile(r'(?:discount|off|save)[\s:]*(?:₹|rs\.?|inr)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            re.compile(r'(?:₹|rs\.?|inr)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)(?:\s*(?:discount|off))', re.IGNORECASE),
        ]
        
        # Invoice number patterns
        self.invoice_patterns = [
            re.compile(r'(?:invoice|bill|receipt)[\s#:]*([a-z0-9\-/]+)', re.IGNORECASE),
            re.compile(r'(?:inv|rcpt|bill)[\s#:]*([a-z0-9\-/]+)', re.IGNORECASE),
            re.compile(r'#([a-z0-9\-/]+)', re.IGNORECASE),
        ]
        
        # Payment method patterns
        self.payment_patterns = [
            re.compile(r'(?:paid by|payment|method)[\s:]*([a-z\s]+)', re.IGNORECASE),
            re.compile(r'(cash|card|credit|debit|upi|net banking|netbanking|cheque|check)', re.IGNORECASE),
        ]
        
        # Vendor/merchant patterns
        self.vendor_patterns = [
            re.compile(r'^([A-Z][A-Z\s&.,\'-]+)(?:\n|$)', re.MULTILINE),  # First line in caps
            re.compile(r'(?:restaurant|hotel|cafe|store|shop|mart|ltd|pvt|inc)[\s:]*([a-z\s&.,\'-]+)', re.IGNORECASE),
        ]
        
        # Category detection patterns
        self.category_patterns = {
            'food': re.compile(r'(?:restaurant|cafe|food|meal|dining|kitchen|pizza|burger|coffee|tea|lunch|dinner|breakfast)', re.IGNORECASE),
            'travel': re.compile(r'(?:taxi|cab|uber|ola|bus|train|flight|hotel|accommodation|fuel|petrol|diesel|parking)', re.IGNORECASE),
            'rent': re.compile(r'(?:rent|rental|lease|office|room|hall|conference|meeting)', re.IGNORECASE),
        }
        
        # Travel location patterns
        self.travel_patterns = [
            re.compile(r'(?:from|origin)[\s:]*([a-z\s,]+?)(?:to|destination)', re.IGNORECASE),
            re.compile(r'(?:to|destination)[\s:]*([a-z\s,]+)', re.IGNORECASE),
        ]

    def parse_bill_data(self, raw_text: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse bill data using regex patterns
        Returns structured bill data dictionary
        """
        logger.info(f"Starting regex parsing for {filename or 'unknown file'}")
        
        # Clean the text
        text = self._clean_text(raw_text)
        
        # Extract data using patterns
        result = {
            "category": self._extract_category(text),
            "date": self._extract_date(text),
            "amount": self._extract_amount(text),
            "vendor": self._extract_vendor(text),
            "subtotal": self._extract_subtotal(text),
            "tax": self._extract_tax(text),
            "discount": self._extract_discount(text),
            "currency": self._extract_currency(text),
            "payment_method": self._extract_payment_method(text),
            "invoice_number": self._extract_invoice_number(text),
            "description": self._generate_description(text),
            "travel_from": self._extract_travel_from(text),
            "travel_to": self._extract_travel_to(text),
            "confidence_score": self._calculate_confidence(text, result if 'result' in locals() else {})
        }
        
        # Calculate confidence based on extracted data
        result["confidence_score"] = self._calculate_confidence(text, result)
        
        logger.info(f"Regex parsing completed with confidence: {result['confidence_score']}")
        return result

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better pattern matching"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Fix common OCR errors
        text = text.replace('|', 'I')  # Common OCR mistake
        text = text.replace('0', 'O')  # In some contexts
        
        return text

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract main amount from text"""
        amounts = []
        
        for pattern in self.amount_patterns:
            matches = pattern.findall(text)
            for match in matches:
                try:
                    # Clean and convert to float
                    amount_str = match.replace(',', '').strip()
                    amount = float(amount_str)
                    if 0 < amount < 1000000:  # Reasonable range
                        amounts.append(amount)
                except (ValueError, AttributeError):
                    continue
        
        # Return the highest amount found (likely the total)
        return max(amounts) if amounts else None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date and convert to YYYY-MM-DD format"""
        for pattern in self.date_patterns:
            match = pattern.search(text)
            if match:
                try:
                    groups = match.groups()
                    
                    if len(groups) == 3:
                        if groups[0].isdigit() and len(groups[0]) == 4:  # YYYY-MM-DD format
                            year, month, day = groups
                        elif groups[2].isdigit() and len(groups[2]) == 4:  # DD-MM-YYYY format
                            day, month, year = groups
                        else:  # Month name format
                            if groups[0].isalpha():  # MMM DD YYYY
                                month_name, day, year = groups
                                month = str(list(calendar.month_abbr).index(groups[0][:3].title()))
                            else:  # DD MMM YYYY
                                day, month_name, year = groups
                                month = str(list(calendar.month_abbr).index(groups[1][:3].title()))
                        
                        # Validate and format
                        year = int(year)
                        month = int(month)
                        day = int(day)
                        
                        if 1 <= month <= 12 and 1 <= day <= 31 and 2000 <= year <= 2030:
                            return f"{year:04d}-{month:02d}-{day:02d}"
                            
                except (ValueError, IndexError, AttributeError):
                    continue
        
        return None

    def _extract_tax(self, text: str) -> Optional[float]:
        """Extract tax amount"""
        for pattern in self.tax_patterns:
            match = pattern.search(text)
            if match:
                try:
                    tax_str = match.group(1).replace(',', '').strip()
                    tax = float(tax_str)
                    if 0 <= tax < 100000:  # Reasonable range
                        return tax
                except (ValueError, AttributeError):
                    continue
        return None

    def _extract_subtotal(self, text: str) -> Optional[float]:
        """Extract subtotal amount"""
        for pattern in self.subtotal_patterns:
            match = pattern.search(text)
            if match:
                try:
                    subtotal_str = match.group(1).replace(',', '').strip()
                    subtotal = float(subtotal_str)
                    if 0 < subtotal < 1000000:  # Reasonable range
                        return subtotal
                except (ValueError, AttributeError):
                    continue
        return None

    def _extract_discount(self, text: str) -> Optional[float]:
        """Extract discount amount"""
        for pattern in self.discount_patterns:
            match = pattern.search(text)
            if match:
                try:
                    discount_str = match.group(1).replace(',', '').strip()
                    discount = float(discount_str)
                    if 0 <= discount < 100000:  # Reasonable range
                        return discount
                except (ValueError, AttributeError):
                    continue
        return None

    def _extract_currency(self, text: str) -> str:
        """Extract currency from text"""
        if re.search(r'₹|inr|rupee', text, re.IGNORECASE):
            return "INR"
        elif re.search(r'\$|usd|dollar', text, re.IGNORECASE):
            return "USD"
        elif re.search(r'€|eur|euro', text, re.IGNORECASE):
            return "EUR"
        elif re.search(r'£|gbp|pound', text, re.IGNORECASE):
            return "GBP"
        else:
            return "INR"  # Default

    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice/receipt number"""
        for pattern in self.invoice_patterns:
            match = pattern.search(text)
            if match:
                invoice_num = match.group(1).strip()
                if len(invoice_num) > 2 and len(invoice_num) < 50:  # Reasonable length
                    return invoice_num
        return None

    def _extract_payment_method(self, text: str) -> str:
        """Extract payment method"""
        for pattern in self.payment_patterns:
            match = pattern.search(text)
            if match:
                method = match.group(1).lower().strip()
                if 'cash' in method:
                    return "cash"
                elif any(word in method for word in ['card', 'credit', 'debit']):
                    return "card"
                elif 'upi' in method:
                    return "upi"
                elif any(word in method for word in ['net', 'banking']):
                    return "netbanking"
                elif any(word in method for word in ['cheque', 'check']):
                    return "cheque"
        
        return "other"

    def _extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor/merchant name"""
        lines = text.split('\n')
        
        # Try first few lines for vendor name
        for i, line in enumerate(lines[:3]):
            line = line.strip()
            if len(line) > 3 and len(line) < 100:
                # Check if it looks like a business name
                if re.search(r'[A-Z][a-z]', line) and not re.search(r'\d{4}', line):
                    return line
        
        # Try regex patterns
        for pattern in self.vendor_patterns:
            match = pattern.search(text)
            if match:
                vendor = match.group(1).strip()
                if len(vendor) > 3 and len(vendor) < 100:
                    return vendor
        
        return None

    def _extract_category(self, text: str) -> str:
        """Extract bill category based on keywords"""
        for category, pattern in self.category_patterns.items():
            if pattern.search(text):
                return category
        
        return "miscellaneous"

    def _extract_travel_from(self, text: str) -> Optional[str]:
        """Extract travel origin"""
        for pattern in self.travel_patterns:
            match = pattern.search(text)
            if match and 'from' in pattern.pattern.lower():
                location = match.group(1).strip()
                if len(location) > 2 and len(location) < 50:
                    return location
        return None

    def _extract_travel_to(self, text: str) -> Optional[str]:
        """Extract travel destination"""
        for pattern in self.travel_patterns:
            match = pattern.search(text)
            if match and 'to' in pattern.pattern.lower():
                location = match.group(1).strip()
                if len(location) > 2 and len(location) < 50:
                    return location
        return None

    def _generate_description(self, text: str) -> str:
        """Generate a description from the text"""
        lines = text.split('\n')
        
        # Find lines that might contain description
        description_parts = []
        for line in lines:
            line = line.strip()
            if (len(line) > 10 and len(line) < 200 and 
                not re.search(r'^\d+[/-]\d+[/-]\d+', line) and  # Not a date
                not re.search(r'₹|\d+\.\d{2}', line) and  # Not an amount
                not re.search(r'total|amount|tax|gst', line, re.IGNORECASE)):  # Not financial terms
                description_parts.append(line)
        
        if description_parts:
            return ' | '.join(description_parts[:2])  # Take first 2 relevant lines
        else:
            return "Bill processed via regex parser"

    def _calculate_confidence(self, text: str, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted data quality"""
        confidence = 0.0
        
        # Base confidence for regex parsing
        confidence += 0.3
        
        # Add confidence based on extracted fields
        if extracted_data.get('amount'):
            confidence += 0.2
        if extracted_data.get('date'):
            confidence += 0.15
        if extracted_data.get('vendor'):
            confidence += 0.1
        if extracted_data.get('category') != 'miscellaneous':
            confidence += 0.1
        if extracted_data.get('tax'):
            confidence += 0.05
        if extracted_data.get('invoice_number'):
            confidence += 0.05
        if extracted_data.get('payment_method') != 'other':
            confidence += 0.05
        
        # Reduce confidence if text is very short or unclear
        if len(text) < 50:
            confidence -= 0.1
        
        # Ensure confidence is within valid range
        return max(0.0, min(1.0, confidence))

# Global service instance
regex_bill_parser = RegexBillParser()