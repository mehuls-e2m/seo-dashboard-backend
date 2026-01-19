"""
Pagespeed routes/endpoints
"""
from fastapi import APIRouter, HTTPException, status
import logging

from API.models.schemas import PagespeedRequest, PagespeedResponse, ErrorResponse
from API.services.pagespeed_service import PagespeedService
from API.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pagespeed", tags=["pagespeed"])

pagespeed_service = PagespeedService(
    gemini_api_key=settings.gemini_api_key,
    pagespeed_api_key=settings.pagespeed_api_key
)


@router.post(
    "",
    response_model=PagespeedResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Pagespeed for Important Pages",
    description="Extracts 5 most important links from homepage using Gemini, then analyzes pagespeed metrics for those pages in parallel. Returns average metrics.",
    responses={
        200: {
            "description": "Pagespeed analysis completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "homepage_url": "https://example.com",
                        "total_pages_analyzed": 5,
                        "pages_analyzed": [
                            "https://example.com",
                            "https://example.com/about",
                            "https://example.com/products"
                        ],
                        "average_page_size_bytes": 245678,
                        "average_dom_elements": 342,
                        "average_scripts_count": 12.5,
                        "average_stylesheets_count": 3.2,
                        "average_images_count": 15.8,
                        "average_text_content_length": 4567
                    }
                }
            }
        },
        400: {
            "description": "Invalid request parameters",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def analyze_pagespeed(request: PagespeedRequest):
    """
    Analyze pagespeed for important pages extracted from homepage.
    
    - Uses Gemini to extract 5 most important links from homepage
    - Analyzes pagespeed metrics for those pages in parallel
    - Returns average metrics across all analyzed pages
    """
    try:
        logger.info(f"🚀 Starting pagespeed analysis for: {request.homepage_url}")
        
        result = await pagespeed_service.analyze_important_pages(request.homepage_url)
        
        logger.info(f"✅ Pagespeed analysis completed successfully")
        
        return PagespeedResponse(
            homepage_url=request.homepage_url,
            **result
        )
        
    except Exception as e:
        logger.error(f"❌ Error in pagespeed analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing pagespeed: {str(e)}"
        )

