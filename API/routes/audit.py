"""
Audit routes/endpoints
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional
import logging

from API.models.schemas import AuditRequest, AuditResponse, ErrorResponse
from API.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])

audit_service = AuditService()


@router.post(
    "",
    response_model=AuditResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform SEO Audit",
    description="Perform a comprehensive SEO audit on a website. Returns audit statistics and detailed issues.",
    responses={
        200: {
            "description": "Audit completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "audit_stats": {
                            "site_overview": {
                                "base_url": "https://example.com",
                                "total_crawled_pages": 65,
                                "average_seo_score": 27.23
                            }
                        },
                        "audit_issues": {},
                        "execution_time": 45.23
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
async def perform_audit(request: AuditRequest) -> AuditResponse:
    """
    Perform SEO audit on a website.
    
    - **url**: Website URL to audit (required)
    - **max_pages**: Maximum number of pages to crawl (optional, if not provided crawls all pages)
    
    **Note**: The crawler does NOT respect robots.txt by default (respect_robots=False) to ensure comprehensive audits.
    This means it will crawl all pages it discovers, even if they are disallowed in robots.txt.
    The robots.txt file is still fetched and analyzed for information, but its restrictions are not enforced.
    
    Returns:
    - **audit_stats**: Statistics and overview of the audit
    - **audit_issues**: Detailed issues found during the audit
    - **execution_time**: Time taken to complete the audit in seconds
    """
    try:
        logger.info(f"🔍 Starting audit for URL: {request.url}, max_pages: {request.max_pages}")
        
        # Perform audit (respect_robots=False by default for comprehensive audits)
        result = await audit_service.perform_audit(
            base_url=request.url,
            max_pages=request.max_pages,
            respect_robots=False  # Default to False for comprehensive SEO audits
        )
        
        logger.info(f"✅ Audit completed successfully for {request.url}")
        
        return AuditResponse(**result)
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Error performing audit: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing audit: {str(e)}"
        )

