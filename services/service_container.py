"""Dependency injection container for services."""

from typing import Dict, Any, TypeVar, Type, Callable
from utils.logger import get_logger
from exceptions.base_exceptions import ConfigurationException

T = TypeVar('T')


class ServiceContainer:
    """Simple dependency injection container for managing services."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """
        Register a singleton service instance.
        
        Args:
            name: Service name
            instance: Service instance
        """
        if name in self._singletons:
            self.logger.warning(
                "Overriding existing singleton service",
                extra={"service_name": name}
            )
        
        self._singletons[name] = instance
        self.logger.debug(
            "Singleton service registered",
            extra={"service_name": name}
        )
    
    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Register a factory function for creating service instances.
        
        Args:
            name: Service name
            factory: Factory function
        """
        if name in self._factories:
            self.logger.warning(
                "Overriding existing factory service",
                extra={"service_name": name}
            )
        
        self._factories[name] = factory
        self.logger.debug(
            "Factory service registered",
            extra={"service_name": name}
        )
    
    def register_transient(self, name: str, service_class: Type[T]) -> None:
        """
        Register a transient service (new instance each time).
        
        Args:
            name: Service name
            service_class: Service class
        """
        def factory() -> T:
            return service_class()
        
        self.register_factory(name, factory)
    
    def get(self, name: str) -> Any:
        """
        Get a service instance.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            ConfigurationException: If service is not registered
        """
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]
        
        # Check factories
        if name in self._factories:
            try:
                instance = self._factories[name]()
                self.logger.debug(
                    "Service instance created from factory",
                    extra={"service_name": name}
                )
                return instance
            except Exception as e:
                raise ConfigurationException(
                    f"Failed to create service '{name}': {str(e)}",
                    config_key=name
                ) from e
        
        raise ConfigurationException(
            f"Service '{name}' is not registered",
            config_key=name
        )
    
    def get_optional(self, name: str, default: Any = None) -> Any:
        """
        Get a service instance, returning default if not found.
        
        Args:
            name: Service name
            default: Default value if service not found
            
        Returns:
            Service instance or default
        """
        try:
            return self.get(name)
        except ConfigurationException:
            return default
    
    def has(self, name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            name: Service name
            
        Returns:
            True if service is registered
        """
        return name in self._singletons or name in self._factories
    
    def remove(self, name: str) -> bool:
        """
        Remove a service registration.
        
        Args:
            name: Service name
            
        Returns:
            True if service was removed
        """
        removed = False
        
        if name in self._singletons:
            del self._singletons[name]
            removed = True
            self.logger.debug(
                "Singleton service removed",
                extra={"service_name": name}
            )
        
        if name in self._factories:
            del self._factories[name]
            removed = True
            self.logger.debug(
                "Factory service removed",
                extra={"service_name": name}
            )
        
        return removed
    
    def clear(self) -> None:
        """Clear all service registrations."""
        singleton_count = len(self._singletons)
        factory_count = len(self._factories)
        
        self._singletons.clear()
        self._factories.clear()
        
        self.logger.info(
            "Service container cleared",
            extra={
                "removed_singletons": singleton_count,
                "removed_factories": factory_count
            }
        )
    
    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered services.
        
        Returns:
            Dictionary with service information
        """
        return {
            "singletons": list(self._singletons.keys()),
            "factories": list(self._factories.keys()),
            "total_services": len(self._singletons) + len(self._factories)
        }


# Global service container instance
_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global service container."""
    return _container


def configure_services() -> None:
    """Configure default services in the container."""
    from services.content_cleaning_service import ContentCleaningService
    from services.document_processing_service import DocumentProcessingService
    from services.llm_service import LLMService
    from services.output_generation_service import OutputGenerationService
    from services.file_validation_service import FileValidationService
    from services.template_service import TemplateService
    
    container = get_container()
    
    # Register singleton services
    container.register_singleton("content_cleaning", ContentCleaningService())
    container.register_singleton("llm", LLMService())
    container.register_singleton("file_validation", FileValidationService())
    container.register_singleton("template", TemplateService())
    
    # Register factory services (need storage dependency)
    container.register_factory("document_processing", DocumentProcessingService)
    container.register_factory("output_generation", OutputGenerationService)
    
    container.logger.info("Default services configured")


def get_service(name: str) -> Any:
    """
    Get a service from the global container.
    
    Args:
        name: Service name
        
    Returns:
        Service instance
    """
    return get_container().get(name)
