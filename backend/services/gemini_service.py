import os
import json
import logging
from typing import Optional, Tuple, Dict, Any
import requests
import asyncio
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
load_dotenv(backend_dir / ".env")
load_dotenv(project_root / ".env", override=True)

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Updated to use Gemini 2.0 Flash model
GEMINI_ENDPOINT = os.getenv(
    "GEMINI_ENDPOINT",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
)

BILL_PROMPT = (
    "You are an advanced AI assistant for a corporate travel expense management system using Gemini 2.0 Flash.\n"
    "Your task is to analyze raw OCR text from expense bills and extract structured data with high precision.\n"
    "\n"
    "BILL CATEGORIES:\n"
    "- \"food\": Restaurants, cafes, catering, meals, food delivery\n"
    "- \"travel\": Transportation tickets, taxis, ride-sharing, fuel, parking, hotels, accommodation\n"
    "- \"rent\": Office rent, conference room rent, equipment rental\n"
    "- \"miscellaneous\": Office supplies, utilities, other business expenses\n"
    "\n"
    "EXTRACTION RULES:\n"
    "1. Analyze the OCR text carefully for bill/receipt patterns\n"
    "2. Extract dates in YYYY-MM-DD format (convert from any format found)\n"
    "3. Extract amounts as float numbers (remove currency symbols, commas)\n"
    "4. Identify vendor/merchant name from headers or business names\n"
    "5. Calculate subtotal, tax, and total amounts when available\n"
    "6. Detect payment methods from text patterns\n"
    "7. Extract invoice/receipt numbers when present\n"
    "8. For travel: extract origin and destination if mentioned\n"
    "\n"
    "REQUIRED JSON OUTPUT FORMAT:\n"
    "{\n"
    "  \"category\": \"food\" | \"travel\" | \"rent\" | \"miscellaneous\",\n"
    "  \"date\": \"YYYY-MM-DD\",\n"
    "  \"amount\": 0.00,\n"
    "  \"vendor\": \"string\",\n"
    "  \"subtotal\": 0.00,\n"
    "  \"tax\": 0.00,\n"
    "  \"discount\": 0.00,\n"
    "  \"currency\": \"INR\" | \"USD\" | \"EUR\" | \"GBP\" | \"other\",\n"
    "  \"payment_method\": \"cash\" | \"card\" | \"upi\" | \"netbanking\" | \"cheque\" | \"other\",\n"
    "  \"invoice_number\": \"string or null\",\n"
    "  \"description\": \"string\",\n"
    "  \"travel_from\": \"string or null\",\n"
    "  \"travel_to\": \"string or null\",\n"
    "  \"confidence_score\": 0.95\n"
    "}\n"
    "\n"
    "IMPORTANT:\n"
    "- Return ONLY valid JSON, no additional text\n"
    "- Use null for missing data, keep all JSON keys\n"
    "- Ensure amounts are numeric (float)\n"
    "- Set confidence_score based on text clarity (0.0-1.0)\n"
    "- If OCR text is unclear, set confidence_score lower\n"
)

class GeminiService:
    """Enhanced Gemini API service for bill analysis using Gemini 2.0 Flash"""

    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.endpoint = GEMINI_ENDPOINT

    def is_available(self) -> bool:
        """Check if Gemini API is available"""
        return bool(self.api_key and self.api_key.strip())

    async def analyze_bill_async(self, raw_text: str, filename: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Async version of bill analysis using Gemini 2.0 Flash
        Returns: (parsed_dict | None, error | None)
        """
        if not self.is_available():
            return None, "Gemini API key not configured"

        # Enhanced content with better context
        content_text = f"""
{BILL_PROMPT}

FILENAME: {filename or 'unknown'}

OCR TEXT TO ANALYZE:
{raw_text}

Please analyze the above OCR text and return the structured JSON data according to the format specified.
"""

        # Enhanced generation config for Gemini 2.0 Flash
        body = {
            "contents": [
                {"role": "user", "parts": [{"text": content_text}]}
            ],
            "generationConfig": {
                "temperature": 0.1,  # Lower temperature for more consistent results
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,  # Increased for more detailed responses
                "response_mime_type": "application/json",
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }

        try:
            # Run the request in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(
                    self.endpoint, 
                    params={"key": self.api_key}, 
                    json=body, 
                    timeout=60  # Increased timeout for better reliability
                )
            )
            
            response.raise_for_status()
            data = response.json()
            
            candidates = data.get("candidates", [])
            if not candidates:
                return None, "Gemini returned no candidates"
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            
            if not parts:
                return None, "Gemini returned no content parts"
            
            text = parts[0].get("text", "").strip()
            
            if not text:
                return None, "Gemini returned empty content"

            # Enhanced JSON parsing with better error handling
            parsed_data = await self._parse_gemini_response(text)
            if parsed_data is None:
                return None, "Failed to parse Gemini response as JSON"
            
            # Validate and normalize the parsed data
            normalized_data = self._normalize_bill_data(parsed_data)
            
            return normalized_data, None
            
        except requests.exceptions.Timeout:
            logger.error("Gemini API request timed out")
            return None, "Gemini API request timed out"
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API request failed: {e}")
            return None, f"Gemini request failed: {e}"
        except Exception as e:
            logger.error(f"Gemini parsing error: {e}")
            return None, f"Gemini parsing error: {e}"

    def analyze_bill(self, raw_text: str, filename: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Synchronous wrapper for bill analysis (for backward compatibility)
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.analyze_bill_async(raw_text, filename))
        except RuntimeError:
            # If no event loop is running, create a new one
            return asyncio.run(self.analyze_bill_async(raw_text, filename))

    async def _parse_gemini_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse Gemini response text to extract JSON"""
        try:
            # Clean the response text
            raw = text.strip()
            
            # Remove markdown code blocks if present
            if raw.startswith("```"):
                raw = raw.strip().strip("`")
                if raw.lower().startswith("json\n"):
                    raw = raw[5:]
            
            # Find JSON boundaries
            start = raw.find("{")
            end = raw.rfind("}")
            
            if start != -1 and end != -1 and end > start:
                json_text = raw[start:end + 1]
            else:
                json_text = raw
            
            # Parse JSON
            parsed = json.loads(json_text)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Raw text: {text}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return None

    def _normalize_bill_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate bill data"""
        def safe_float(value):
            """Safely convert value to float"""
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    # Remove currency symbols and commas
                    cleaned = value.replace(",", "").replace("₹", "").replace("$", "").replace("€", "").replace("£", "").strip()
                    return float(cleaned) if cleaned else None
                except (ValueError, AttributeError):
                    return None
            return None

        def safe_string(value):
            """Safely convert value to string"""
            if value is None:
                return None
            return str(value).strip() if str(value).strip() else None

        # Normalize the data
        normalized = {
            "category": safe_string(data.get("category", "miscellaneous")).lower() if data.get("category") else "miscellaneous",
            "date": safe_string(data.get("date")),
            "amount": safe_float(data.get("amount")),
            "vendor": safe_string(data.get("vendor")),
            "subtotal": safe_float(data.get("subtotal")),
            "tax": safe_float(data.get("tax")),
            "discount": safe_float(data.get("discount")),
            "currency": safe_string(data.get("currency", "INR")).upper() if data.get("currency") else "INR",
            "payment_method": safe_string(data.get("payment_method", "other")).lower() if data.get("payment_method") else "other",
            "invoice_number": safe_string(data.get("invoice_number")),
            "description": safe_string(data.get("description")),
            "travel_from": safe_string(data.get("travel_from")),
            "travel_to": safe_string(data.get("travel_to")),
            "confidence_score": safe_float(data.get("confidence_score", 0.8))
        }

        # Ensure confidence score is within valid range
        if normalized["confidence_score"] is not None:
            normalized["confidence_score"] = max(0.0, min(1.0, normalized["confidence_score"]))
        else:
            normalized["confidence_score"] = 0.8

        # Validate category
        valid_categories = ["food", "travel", "rent", "miscellaneous"]
        if normalized["category"] not in valid_categories:
            normalized["category"] = "miscellaneous"

        # Validate payment method
        valid_payment_methods = ["cash", "card", "upi", "netbanking", "cheque", "other"]
        if normalized["payment_method"] not in valid_payment_methods:
            normalized["payment_method"] = "other"

        return normalized

# Global service instance
gemini_service = GeminiService()