"""Service for managing prompt templates."""

from typing import Dict
from core.prompt_templates import get_prompt_template, list_prompt_templates
from utils.logger import get_logger
from exceptions.base_exceptions import ValidationException


class TemplateService:
    """Service for managing and accessing prompt templates."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._template_cache = {}
    
    def get_template(self, template_name: str) -> Dict:
        """
        Get a specific prompt template by name.
        
        Args:
            template_name: Name of the template to retrieve
            
        Returns:
            Template configuration dictionary
            
        Raises:
            ValidationException: If template is not found or invalid
        """
        if not template_name:
            raise ValidationException("Template name is required", field="template_name")
        
        if not isinstance(template_name, str):
            raise ValidationException(
                "Template name must be a string", 
                field="template_name", 
                value=type(template_name)
            )
        
        try:
            # Check cache first
            if template_name in self._template_cache:
                self.logger.debug(
                    "Template retrieved from cache",
                    extra={"template_name": template_name}
                )
                return self._template_cache[template_name]
            
            # Get template from core module
            template_config = get_prompt_template(template_name)
            
            # Cache the template
            self._template_cache[template_name] = template_config
            
            self.logger.info(
                "Template loaded and cached",
                extra={"template_name": template_name}
            )
            
            return template_config
            
        except ValueError as e:
            self.logger.error(
                "Template not found",
                extra={"template_name": template_name, "error": str(e)}
            )
            raise ValidationException(
                f"Template '{template_name}' not found: {str(e)}",
                field="template_name",
                value=template_name
            ) from e
        except Exception as e:
            self.logger.error(
                "Error loading template",
                extra={"template_name": template_name, "error": str(e)}
            )
            raise ValidationException(
                f"Error loading template '{template_name}': {str(e)}",
                field="template_name",
                value=template_name
            ) from e
    
    def list_templates(self) -> Dict[str, any]:
        """
        List all available prompt templates.
        
        Returns:
            Dictionary with template list and metadata
        """
        try:
            templates = list_prompt_templates()
            
            result = {
                "status": "success",
                "template_count": len(templates),
                "templates": templates,
                "cached_templates": list(self._template_cache.keys())
            }
            
            self.logger.info(
                "Templates listed",
                extra={
                    "template_count": len(templates),
                    "cached_count": len(self._template_cache)
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Error listing templates",
                extra={"error": str(e)}
            )
            raise ValidationException(
                f"Error listing templates: {str(e)}"
            ) from e
    
    def validate_template_name(self, template_name: str) -> bool:
        """
        Validate that a template name exists.
        
        Args:
            template_name: Name of the template to validate
            
        Returns:
            True if template exists, False otherwise
        """
        try:
            self.get_template(template_name)
            return True
        except ValidationException:
            return False
    
    def get_template_info(self, template_name: str) -> Dict[str, any]:
        """
        Get detailed information about a template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Dictionary with template information
        """
        try:
            template_config = self.get_template(template_name)
            
            return {
                "name": template_config.name,
                "description": template_config.description,
                "icon": template_config.icon,
                "color": template_config.color,
                "step_count": len(template_config.steps),
                "primary_step": {
                    "name": template_config.primary_step.name,
                    "output_format": template_config.primary_step.output_format,
                    "temperature": template_config.primary_step.temperature,
                    "max_tokens": template_config.primary_step.max_tokens
                } if template_config.steps else None
            }
            
        except ValidationException:
            return {
                "name": template_name,
                "error": "Template not found",
                "exists": False
            }
    
    def clear_cache(self) -> None:
        """Clear the template cache."""
        cache_size = len(self._template_cache)
        self._template_cache.clear()
        
        self.logger.info(
            "Template cache cleared",
            extra={"cleared_count": cache_size}
        )
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_templates": len(self._template_cache),
            "cache_limit": 100  # Could be made configurable
        }
