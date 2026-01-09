"""
Design & Artwork Intelligence - Preflight Service
Stateless file validation for print-ready artwork
"""
from typing import Dict, Any, Optional
from decimal import Decimal
import mimetypes


class PreflightService:
    """
    Preflight Service - Validates design files before production
    NO DB writes, stateless, product-specific rules
    """
    
    @staticmethod
    def validate(
        file_url: str,
        product_id: int,
        file_size: Optional[int] = None,
        file_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate design file for print readiness
        
        Args:
            file_url: URL or path to design file
            product_id: Product ID for product-specific rules
            file_size: File size in bytes (optional)
            file_format: File format (PDF, PNG, etc.) (optional)
        
        Returns:
            Dict with validation results:
            {
                "status": "pass|warning|fail",
                "checks": {
                    "dpi": "pass|warning|fail",
                    "color_mode": "pass|warning|fail",
                    "bleed": "pass|warning|fail",
                    ...
                },
                "suggestions": ["Increase DPI to 300", ...]
            }
        """
        from ..models import Product
        
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return {
                "status": "fail",
                "checks": {},
                "suggestions": ["Product not found"],
                "error": "Product not found"
            }
        
        checks = {}
        suggestions = []
        
        # DPI Check (would need actual file analysis in production)
        dpi_status = PreflightService._check_dpi(file_url, product)
        checks["dpi"] = dpi_status["status"]
        if dpi_status.get("suggestion"):
            suggestions.append(dpi_status["suggestion"])
        
        # Color Mode Check
        color_status = PreflightService._check_color_mode(file_url, product)
        checks["color_mode"] = color_status["status"]
        if color_status.get("suggestion"):
            suggestions.append(color_status["suggestion"])
        
        # Bleed Check
        bleed_status = PreflightService._check_bleed(file_url, product)
        checks["bleed"] = bleed_status["status"]
        if bleed_status.get("suggestion"):
            suggestions.append(bleed_status["suggestion"])
        
        # File Format Check
        format_status = PreflightService._check_file_format(file_format, product)
        checks["file_format"] = format_status["status"]
        if format_status.get("suggestion"):
            suggestions.append(format_status["suggestion"])
        
        # File Size Check
        if file_size:
            size_status = PreflightService._check_file_size(file_size, product)
            checks["file_size"] = size_status["status"]
            if size_status.get("suggestion"):
                suggestions.append(size_status["suggestion"])
        
        # Determine overall status
        if any(status == "fail" for status in checks.values()):
            overall_status = "fail"
        elif any(status == "warning" for status in checks.values()):
            overall_status = "warning"
        else:
            overall_status = "pass"
        
        return {
            "status": overall_status,
            "checks": checks,
            "suggestions": suggestions
        }
    
    @staticmethod
    def _check_dpi(file_url: str, product: 'Product') -> Dict[str, Any]:
        """Check DPI/resolution"""
        # In production, would analyze actual image/PDF
        # For now, return default pass
        return {
            "status": "pass",
            "suggestion": None
        }
    
    @staticmethod
    def _check_color_mode(file_url: str, product: 'Product') -> Dict[str, Any]:
        """Check color mode (CMYK vs RGB)"""
        # In production, would analyze actual file
        # For print, CMYK is preferred
        return {
            "status": "warning",
            "suggestion": "Convert RGB to CMYK for accurate print colors"
        }
    
    @staticmethod
    def _check_bleed(file_url: str, product: 'Product') -> Dict[str, Any]:
        """Check bleed requirements"""
        # Would check if design has proper bleed margins
        return {
            "status": "pass",
            "suggestion": None
        }
    
    @staticmethod
    def _check_file_format(file_format: Optional[str], product: 'Product') -> Dict[str, Any]:
        """Check file format compatibility"""
        if not file_format:
            return {
                "status": "warning",
                "suggestion": "File format not specified"
            }
        
        allowed_formats = ['PDF', 'PNG', 'JPG', 'EPS', 'AI']
        if file_format.upper() not in allowed_formats:
            return {
                "status": "fail",
                "suggestion": f"File format {file_format} not supported. Use: {', '.join(allowed_formats)}"
            }
        
        return {
            "status": "pass",
            "suggestion": None
        }
    
    @staticmethod
    def _check_file_size(file_size: int, product: 'Product') -> Dict[str, Any]:
        """Check file size limits"""
        max_size_mb = 50  # 50MB default
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return {
                "status": "warning",
                "suggestion": f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds recommended limit ({max_size_mb}MB)"
            }
        
        return {
            "status": "pass",
            "suggestion": None
        }

