import re
import logging
from datetime import datetime, date
from typing import Optional, Tuple, List, Dict, Any
from models.bill_models import FinancialData, ExpenseCategory
import json

logger = logging.getLogger(__name__)

class BillProcessingService:
    def __init__(self):
        # Common patterns for financial data extraction
        # Note: Each regex must have exactly one capturing group that captures the numeric amount
        self.amount_patterns = [
            # Labeled totals with optional currency symbols and comma/decimal variants
            r'(?:grand\s*total|total\s*amount|total\s*due|amount\s*paid|amount|total)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
            # Currency symbol before amount, optionally followed by label
            r'(?:₹|rs\.?|\$|€|£)\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)\s*(?:total|amount|grand\s*total)?',
            # Amount followed by currency code
            r'([0-9][\d,]*(?:[\.,]\d{1,2})?)\s*(?:usd|inr|eur|gbp|aed|sar|cad|aud|sgd|myr|zar|rs\.?|dollars?)\b',
        ]
        
        self.tax_patterns = [
            r'(?:tax|igst|cgst|sgst)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
            r'(?:vat|sales\s+tax|service\s+tax)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
        ]
        
        self.subtotal_patterns = [
            r'(?:sub\s*total\w*|subtotal|net\s*amount|before\s*tax)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
        ]
        
        self.discount_patterns = [
            r'(?:discount|savings|off|reduction)\s*[:\-]?\s*(?:₹|rs\.?|\$|€|£)?\s*([0-9][\d,]*(?:[\.,]\d{1,2})?)',
        ]
        
        self.date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{2,4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4})',
            r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{2,4})',
        ]
        
        # Category keywords mapping
        self.category_keywords = {
            ExpenseCategory.FOOD: [
                'restaurant', 'cafe', 'food', 'dining', 'meal', 'breakfast', 'lunch', 'dinner',
                'pizza', 'burger', 'coffee', 'bar', 'pub', 'kitchen', 'bistro', 'grill',
                'bakery', 'deli', 'catering', 'fast food', 'takeaway', 'delivery'
            ],
            ExpenseCategory.TRANSPORT: [
                'taxi', 'uber', 'lyft', 'bus', 'train', 'flight', 'airline', 'airport',
                'metro', 'subway', 'transport', 'travel', 'cab', 'railway', 'airways',
                'parking', 'toll', 'gas station', 'fuel', 'petrol', 'diesel'
            ],
            ExpenseCategory.LODGING: [
                'hotel', 'motel', 'inn', 'resort', 'lodge', 'accommodation', 'stay',
                'booking', 'reservation', 'room', 'suite', 'hostel', 'b&b', 'airbnb'
            ],
            ExpenseCategory.FUEL: [
                'gas', 'petrol', 'diesel', 'fuel', 'shell', 'bp', 'exxon', 'chevron',
                'mobil', 'station', 'pump', 'gallon', 'liter', 'litre'
            ],
            ExpenseCategory.ENTERTAINMENT: [
                'cinema', 'movie', 'theater', 'concert', 'show', 'entertainment',
                'ticket', 'event', 'club', 'bar', 'recreation', 'amusement'
            ],
            ExpenseCategory.OFFICE_SUPPLIES: [
                'office', 'supplies', 'stationery', 'paper', 'pen', 'printer',
                'computer', 'software', 'equipment', 'desk', 'chair', 'staples'
            ],
            ExpenseCategory.COMMUNICATION: [
                'phone', 'mobile', 'internet', 'wifi', 'data', 'telecom',
                'verizon', 'att', 'sprint', 'tmobile', 'communication'
            ],
            ExpenseCategory.MEDICAL: [
                'hospital', 'clinic', 'doctor', 'medical', 'pharmacy', 'medicine',
                'health', 'dental', 'vision', 'prescription', 'treatment'
            ]
        }
        
        # Common vendor name patterns
        self.vendor_patterns = [
            r'(?:merchant|vendor|store)[:\s]*([^\n\r]+)',
            r'(?:^|\n)([A-Z][A-Z\s&]+(?:LLC|INC|CORP|LTD)?)',
            r'thank\s+you\s+for\s+visiting\s+([^\n\r]+)',
            r'welcome\s+to\s+([^\n\r]+)',
        ]

    async def process_bill_text(self, raw_text: str, filename: str = None) -> Tuple[FinancialData, float, List[str]]:
        """
        Process raw OCR text and extract structured financial data
        Returns: (financial_data, confidence_score, warnings)
        """
        start_time = datetime.now()
        warnings: List[str] = []
        
        try:
            # Use rules-based parsing (Gemini AI parsing removed)
            cleaned_text = self._clean_text(raw_text)
            
            # Extract financial components
            amount = self._extract_amount(cleaned_text)
            tax = self._extract_tax(cleaned_text)
            subtotal = self._extract_subtotal(cleaned_text)
            discount = self._extract_discount(cleaned_text)
            date_extracted = self._extract_date(cleaned_text)
            vendor = self._extract_vendor(cleaned_text, filename)
            category = self._classify_category(cleaned_text, vendor)
            currency = self._extract_currency(cleaned_text)
            remarks = self._extract_remarks(cleaned_text)
            # Try to extract basic line items via rules (used if AI not available)
            rule_line_items = self._extract_line_items(raw_text or cleaned_text)
            
            # Validate and adjust amounts
            amount, subtotal, tax, discount, validation_warnings = self._validate_amounts(
                amount, subtotal, tax, discount
            )
            warnings.extend(validation_warnings)
            
            # Use rule-based line items extraction
            line_items = rule_line_items
            
            # Reconcile/round using line items if present and ensure 2-decimal precision
            amount, subtotal, tax, discount, reconcile_warnings = self._reconcile_with_line_items(
                amount, subtotal, tax, discount, line_items
            )
            warnings.extend(reconcile_warnings)

            amount, subtotal, tax, discount = self._normalize_money_fields(amount, subtotal, tax, discount)

            # Calculate confidence score
            confidence_score = self._calculate_confidence(amount, tax, subtotal, date_extracted, vendor, category)
            
            financial_data = FinancialData(
                date=date_extracted,
                vendor=vendor,
                category=category,
                amount=amount,
                subtotal=subtotal,
                tax=tax,
                discount=discount,
                currency=currency,
                remarks=remarks,
                line_items=line_items
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Bill processed in {processing_time:.2f}s with confidence {confidence_score:.2f}")
            return financial_data, confidence_score, warnings
        
        except Exception as e:
            logger.error(f"Error processing bill text: {str(e)}")
            raise Exception(f"Bill processing failed: {str(e)}")
    
    def _extract_line_items(self, raw_text: str) -> List[Dict[str, Any]]:
        """Heuristic extraction of line items from OCR text when AI is not available.
        Looks for rows with optional quantity, name, unit price, and line total.
        """
        try:
            if not raw_text:
                return []
            lines = [ln.strip() for ln in raw_text.replace('\r', '\n').split('\n') if ln.strip()]
            items: List[Dict[str, Any]] = []
            # Regex for formats like: 2 x Burger 5.00 10.00 or Burger 2 5.00 10.00
            row_re = re.compile(r"^(?:(\d+[xX*]\s*)?)([A-Za-z][A-Za-z0-9\-\s]{2,})(?:\s+(\d+(?:[\.,]\d+)?))?(?:\s+(\d+(?:[\.,]\d+)?))?(?:\s+(\d+(?:[\.,]\d+)?))?$")
            for ln in lines:
                m = row_re.match(ln)
                if not m:
                    continue
                qty_token, name, n1, n2, n3 = m.groups()
                qty = None
                if qty_token:
                    # e.g., '2x ' -> 2
                    try:
                        qty = float(re.findall(r"\d+", qty_token)[0])
                    except Exception:
                        qty = None
                # Collect numeric candidates at end
                nums = [x for x in (n1, n2, n3) if x]
                unit_price = None
                line_total = None
                # If two numbers, assume last is line_total, previous is unit price
                if len(nums) >= 2:
                    unit_price = self._to_float_amount(nums[-2])
                    line_total = self._to_float_amount(nums[-1])
                elif len(nums) == 1:
                    # Single number could be line total
                    line_total = self._to_float_amount(nums[0])
                # Filter unreasonable
                if name and (unit_price is not None or line_total is not None):
                    items.append({
                        "name": re.sub(r"\s{2,}", " ", name).strip(),
                        "qty": qty,
                        "unit_price": unit_price,
                        "line_total": line_total
                    })
            # Keep up to 50 items
            return items[:50]
        except Exception:
            return []
            
        except Exception as e:
            logger.error(f"Error processing bill text: {str(e)}")
            raise Exception(f"Bill processing failed: {str(e)}")

    def _clean_text(self, text: str) -> str:
        """Clean and normalize OCR text while preserving line breaks"""
        if not text:
            return ""
        
        # Normalize newlines to \n and trim trailing spaces per line
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        lines = [re.sub(r'[ \t]+', ' ', ln).strip() for ln in text.split('\n')]
        # Preserve first-pass structure: keep lines, but also keep a lowercased copy for pattern search
        text = '\n'.join([ln for ln in lines if ln])
        self._lower_cache = text.lower()
        
        # Remove common OCR artifacts, but keep single hyphens
        text = re.sub(r'[|]{2,}', '', text)  # Remove multiple pipes
        text = re.sub(r'-{3,}', '-', text)   # Collapse long dash sequences
        
        return text

    def _to_float_amount(self, s: str) -> Optional[float]:
        """Parse numeric strings with either US (1,234.56) or EU/IN (1.234,56 or 1,23,456.78) formats."""
        if s is None:
            return None
        try:
            s = s.strip()
            # If both comma and dot present, decide decimal by last separator
            if ',' in s and '.' in s:
                # If last separator is comma, treat comma as decimal and remove dots
                if s.rfind(',') > s.rfind('.'):
                    s = s.replace('.', '')
                    s = s.replace(',', '.')
                else:
                    # last is dot: treat dot as decimal and remove commas
                    s = s.replace(',', '')
            else:
                # Only one of them present
                if s.count(',') >= 1 and '.' not in s:
                    # Likely comma as decimal OR Indian grouping. If last comma is within last 3 chars, treat as decimal
                    last_comma = s.rfind(',')
                    if len(s) - last_comma <= 3:
                        s = s.replace(',', '.')
                    else:
                        s = s.replace(',', '')
                # If only dots present, assume dot decimal
            value = float(s)
            # sanity bounds
            if value < 0 or value > 1000000:
                return None
            return round(value + 1e-12, 2)
        except Exception:
            return None

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract total amount from text"""
        amounts = []
        
        # Use lowercased cache for better matching of labels, but keep original for vendor/name heuristics
        search_text = getattr(self, '_lower_cache', text)
        labelled_amounts = []
        other_amounts = []
        for idx, pattern in enumerate(self.amount_patterns):
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            for match in matches:
                try:
                    # match may be a tuple when multiple groups; take the first non-empty
                    if isinstance(match, tuple):
                        for m in match:
                            if m:
                                match = m
                                break
                    val = self._to_float_amount(str(match))
                    if val is not None and 0.01 <= val <= 100000:  # Reasonable range
                        if idx == 0 or idx == 1:  # prefer labelled/symbol patterns
                            labelled_amounts.append(val)
                        else:
                            other_amounts.append(val)
                except ValueError:
                    continue
        if labelled_amounts:
            amounts.extend(labelled_amounts)
        else:
            amounts.extend(other_amounts)
        
        # Return the highest amount found (likely to be total)
        return max(amounts) if amounts else None

    def _extract_tax(self, text: str) -> Optional[float]:
        """Extract tax amount from text"""
        for pattern in self.tax_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        for m in match:
                            if m:
                                match = m
                                break
                    tax = self._to_float_amount(str(match))
                    if tax is not None and 0 <= tax <= 10000:  # Reasonable tax range
                        return tax
                except ValueError:
                    continue
        return None

    def _extract_subtotal(self, text: str) -> Optional[float]:
        """Extract subtotal amount from text"""
        for pattern in self.subtotal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        for m in match:
                            if m:
                                match = m
                                break
                    subtotal = self._to_float_amount(str(match))
                    if subtotal is not None and 0.01 <= subtotal <= 100000:
                        return subtotal
                except ValueError:
                    continue
        return None

    def _extract_discount(self, text: str) -> Optional[float]:
        """Extract discount amount from text"""
        for pattern in self.discount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        for m in match:
                            if m:
                                match = m
                                break
                    discount = self._to_float_amount(str(match))
                    if discount is not None and 0 <= discount <= 10000:
                        return discount
                except ValueError:
                    continue
        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text and return as ISO string"""
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Try different date formats
                    date_formats = [
                        '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
                        '%m-%d-%Y', '%d-%m-%Y', '%Y-%m-%d',
                        '%m/%d/%y', '%d/%m/%y', '%y/%m/%d',
                        '%d %b %Y', '%b %d, %Y', '%B %d, %Y'
                    ]
                    
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(match, fmt).date()
                            # Validate date is reasonable (not too far in future/past)
                            if date(2000, 1, 1) <= parsed_date <= date(2030, 12, 31):
                                return parsed_date.isoformat()
                        except ValueError:
                            continue
                except Exception:
                    continue
        return None

    def _extract_vendor(self, text: str, filename: str = None) -> Optional[str]:
        """Extract vendor/store name from text"""
        # Try vendor patterns
        for pattern in self.vendor_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                vendor = match.strip()
                if len(vendor) > 2 and len(vendor) < 100:
                    return vendor.title()
        
        # Fallback: look for capitalized words at the beginning
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 3 and line.isupper():
                return line.title()
        
        # Extract from filename if available
        if filename:
            name = filename.split('.')[0].replace('_', ' ').replace('-', ' ')
            if len(name) > 2:
                return name.title()
        
        return None

    def _classify_category(self, text: str, vendor: str = None) -> Optional[str]:
        """Classify expense category based on text content"""
        text_to_analyze = text
        if vendor:
            text_to_analyze += f" {vendor.lower()}"
        
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences of each keyword
                score += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_to_analyze, re.IGNORECASE))
            
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get).value
        
        return ExpenseCategory.MISCELLANEOUS.value

    def _extract_currency(self, text: str) -> str:
        """Extract currency from text"""
        currency_patterns = [
            r'\b(usd|eur|gbp|cad|aud|inr|jpy)\b',
            r'\$',  # Dollar sign
            r'€',   # Euro sign
            r'£',   # Pound sign
            r'¥',   # Yen sign
            r'₹',   # Rupee sign
        ]
        
        currency_map = {
            '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₹': 'INR'
        }
        
        for pattern in currency_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                currency = matches[0].upper()
                return currency_map.get(currency, currency)
        
        return 'USD'  # Default currency

    def _extract_remarks(self, text: str) -> Optional[str]:
        """Extract relevant remarks from text"""
        remarks_patterns = [
            r'note[:\s]*([^\n\r]+)',
            r'memo[:\s]*([^\n\r]+)',
            r'description[:\s]*([^\n\r]+)',
            r'purpose[:\s]*([^\n\r]+)',
        ]
        
        for pattern in remarks_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                remark = matches[0].strip()
                if len(remark) > 3 and len(remark) < 200:
                    return remark.title()
        
        return None

    def _validate_amounts(self, amount: Optional[float], subtotal: Optional[float], 
                         tax: Optional[float], discount: Optional[float]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], List[str]]:
        """Validate and adjust extracted amounts"""
        warnings = []
        
        # If we have subtotal and tax, calculate total
        if subtotal and tax and not amount:
            calculated_total = subtotal + tax
            if discount:
                calculated_total -= discount
            amount = calculated_total
            warnings.append("Total amount calculated from subtotal and tax")
        
        # If we have total and tax, calculate subtotal
        elif amount and tax and not subtotal:
            calculated_subtotal = amount - tax
            if discount:
                calculated_subtotal += discount
            if calculated_subtotal > 0:
                subtotal = calculated_subtotal
                warnings.append("Subtotal calculated from total and tax")
        
        # Validate relationships
        if amount and subtotal and tax:
            expected_total = subtotal + tax
            if discount:
                expected_total -= discount
            
            if abs(amount - expected_total) > 0.02:  # Allow small rounding differences
                warnings.append(f"Amount calculation mismatch: {amount} vs calculated {expected_total}")
        
        # Ensure tax is reasonable (typically 0-30% of subtotal)
        if tax and subtotal and tax > subtotal * 0.3:
            warnings.append("Tax amount seems unusually high")
        
        return amount, subtotal, tax, discount, warnings

    def _calculate_confidence(self, amount: Optional[float], tax: Optional[float], 
                            subtotal: Optional[float], date_extracted: Optional[str], 
                            vendor: Optional[str], category: Optional[str]) -> float:
        """Calculate confidence score for extraction accuracy"""
        score = 0.0
        
        # Amount extraction (most important)
        if amount:
            score += 0.4
        
        # Date extraction
        if date_extracted:
            score += 0.2
        
        # Vendor extraction
        if vendor:
            score += 0.15
        
        # Category classification
        if category and category != "miscellaneous":
            score += 0.1
        
        # Tax extraction
        if tax:
            score += 0.1
        
        # Subtotal extraction
        if subtotal:
            score += 0.05
        
        return min(score, 1.0)

    def _normalize_money_fields(self, amount: Optional[float], subtotal: Optional[float],
                                tax: Optional[float], discount: Optional[float]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Round monetary fields to 2 decimals consistently."""
        def r2(v: Optional[float]) -> Optional[float]:
            if v is None:
                return None
            # small epsilon to avoid cases like 1.19999999
            return round(float(v) + 1e-12, 2)
        return r2(amount), r2(subtotal), r2(tax), r2(discount)

    def _reconcile_with_line_items(self, amount: Optional[float], subtotal: Optional[float],
                                   tax: Optional[float], discount: Optional[float],
                                   line_items: List[Dict[str, Any]]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], List[str]]:
        """Use line items to reconcile subtotal/amount when possible and issue warnings."""
        warnings: List[str] = []
        if not line_items:
            return amount, subtotal, tax, discount, warnings

        # Compute items subtotal from provided line items
        items_subtotal = 0.0
        any_item = False
        for it in line_items:
            try:
                name = it.get("name") if isinstance(it, dict) else None
                qty = it.get("qty") if isinstance(it, dict) else None
                unit_price = it.get("unit_price") if isinstance(it, dict) else None
                line_total = it.get("line_total") if isinstance(it, dict) else None

                # Prefer explicit line_total; else compute from qty * unit_price
                if isinstance(line_total, (int, float)):
                    items_subtotal += float(line_total)
                    any_item = True
                elif isinstance(qty, (int, float)) and isinstance(unit_price, (int, float)):
                    items_subtotal += float(qty) * float(unit_price)
                    any_item = True
            except Exception:
                continue

        if not any_item:
            return amount, subtotal, tax, discount, warnings

        items_subtotal = round(items_subtotal + 1e-12, 2)

        # If subtotal missing, adopt items subtotal
        if subtotal is None:
            subtotal = items_subtotal
            warnings.append("Subtotal inferred from sum of line items")
        else:
            # If subtotal present but differs significantly from items subtotal, warn
            if abs(float(subtotal) - items_subtotal) > 0.02:
                warnings.append(f"Subtotal mismatch with line items: parsed {subtotal} vs items {items_subtotal}")

        # If total amount missing, compute from components
        if amount is None and subtotal is not None:
            computed = float(subtotal) + (float(tax) if tax is not None else 0.0) - (float(discount) if discount is not None else 0.0)
            amount = round(computed + 1e-12, 2)
            warnings.append("Total amount computed from subtotal, tax, and discount")

        return amount, subtotal, tax, discount, warnings

# Global service instance
bill_processing_service = BillProcessingService()