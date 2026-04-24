from fastapi import APIRouter
import os
import logging
from datetime import datetime
from services.ocr_space_service import ocr_space_service
from services.fallback_ocr_service import fallback_ocr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["OCR Health Monitoring"])

@router.get("/ocr-status")
async def get_ocr_status():
    """Get detailed status of all OCR services"""
    try:
        ocr_space_available = ocr_space_service.is_available()
        google_vision_available = bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "ocr_space": {
                    "available": ocr_space_available,
                    "api_key_configured": bool(os.getenv("OCR_SPACE_API_KEY")),
                    "status": "ready" if ocr_space_available else "not configured"
                },
                "google_vision": {
                    "available": google_vision_available,
                    "credentials_configured": google_vision_available,
                    "status": "ready" if google_vision_available else "not configured"
                }
            },
            "fallback": {
                "enabled": True,
                "available": fallback_ocr_service.is_available(),
                "strategy": "OCR.Space → Google Vision"
            },
            "overall_status": "healthy" if fallback_ocr_service.is_available() else "unhealthy",
            "features": {
                "retry_logic": True,
                "exponential_backoff": True,
                "multiple_engines": True,
                "improved_parsing": True,
                "bill_no_exclusion": True
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting OCR status: {str(e)}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "error",
            "error": str(e)
        }