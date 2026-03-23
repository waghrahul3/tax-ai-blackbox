"""Application-level configuration."""

import os
from typing import Dict, Any, List
from utils.logger import get_logger


class AppConfig:
    """Centralized application configuration."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._config = self._load_app_config()
    
    def _load_app_config(self) -> Dict[str, Any]:
        """Load application configuration."""
        config = {
            "app_name": os.getenv("APP_NAME", "Tax AI Agent"),
            "app_version": os.getenv("APP_VERSION", "0.0.0"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", "8000")),
            "log_level": os.getenv("LOG_LEVEL", "DEBUG").upper(),
            "cors_origins": self._get_cors_origins(),
            "security_config": self._get_security_config(),
            "database_config": self._get_database_config()
        }
        
        self.logger.info(
            "App config loaded",
            extra={
                "app_name": config["app_name"],
                "version": config["app_version"],
                "environment": config["environment"],
                "debug": config["debug"]
            }
        )
        
        return config
    
    def _get_cors_origins(self) -> List[str]:
        """Get CORS origins configuration."""
        origins_env = os.getenv("CORS_ORIGINS", "*")
        if origins_env == "*":
            return ["*"]
        return [origin.strip() for origin in origins_env.split(',') if origin.strip()]
    
    def _get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            "enable_https": os.getenv("ENABLE_HTTPS", "false").lower() == "true",
            "ssl_cert_path": os.getenv("SSL_CERT_PATH"),
            "ssl_key_path": os.getenv("SSL_KEY_PATH"),
            "max_request_size": int(os.getenv("MAX_REQUEST_SIZE", "100")),
            "enable_rate_limiting": os.getenv("ENABLE_RATE_LIMITING", "false").lower() == "true",
            "api_key_required": os.getenv("API_KEY_REQUIRED", "false").lower() == "true",
            "allowed_hosts": self._get_allowed_hosts()
        }
    
    def _get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            "database_url": os.getenv("DATABASE_URL"),
            "database_pool_size": int(os.getenv("DATABASE_POOL_SIZE", "10")),
            "database_max_overflow": int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
        }
    
    def _get_allowed_hosts(self) -> List[str]:
        """Get allowed hosts configuration."""
        hosts_env = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
        return [host.strip() for host in hosts_env.split(',') if host.strip()]
    
    def get_app_name(self) -> str:
        """Get application name."""
        return self._config["app_name"]
    
    def get_app_version(self) -> str:
        """Get application version."""
        return self._config["app_version"]
    
    def get_environment(self) -> str:
        """Get environment (development, staging, production)."""
        return self._config["environment"]
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self._config["debug"]
    
    def get_host(self) -> str:
        """Get server host."""
        return self._config["host"]
    
    def get_port(self) -> int:
        """Get server port."""
        return self._config["port"]
    
    def get_log_level(self) -> str:
        """Get log level."""
        return self._config["log_level"]
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins."""
        return self._config["cors_origins"].copy()
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self._config["security_config"].copy()
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self._config["database_config"].copy()
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self._config["environment"].lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development."""
        return self._config["environment"].lower() == "development"
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get application configuration summary."""
        return {
            "app_name": self._config["app_name"],
            "version": self._config["app_version"],
            "environment": self._config["environment"],
            "debug": self._config["debug"],
            "host": self._config["host"],
            "port": self._config["port"],
            "log_level": self._config["log_level"],
            "cors_origins_count": len(self._config["cors_origins"]),
            "security": {
                "enable_https": self._config["security_config"]["enable_https"],
                "enable_rate_limiting": self._config["security_config"]["enable_rate_limiting"],
                "api_key_required": self._config["security_config"]["api_key_required"]
            }
        }
