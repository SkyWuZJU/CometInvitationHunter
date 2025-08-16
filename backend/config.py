import os
from typing import Optional

class Config:
    """Configuration management for the application"""
    
    def __init__(self, env_file: Optional[str] = None):
        # Load .env file by default
        if env_file is None:
            # Look for .env in the backend directory (where this config.py file is located)
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            env_file = os.path.join(backend_dir, '.env')
        if env_file:
            self.load_env_file(env_file)
    
    def load_env_file(self, env_file: str):
        """Load environment variables from file"""
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    @property
    def database_url(self) -> str:
        return os.getenv('DATABASE_URL', 'sqlite:///./comet_hunter.db')
    
    @property
    def utools_api_key(self) -> str:
        return os.getenv('UTOOLS_API_KEY', '')
    
    @property
    def utools_base_url(self) -> str:
        return os.getenv('UTOOLS_BASE_URL', 'https://twitter.good6.top/api/base/apitools')
    
    @property
    def target_user_id(self) -> str:
        return os.getenv('TARGET_USER_ID', '1260183271930904577')
    
    @property
    def backend_port(self) -> int:
        return int(os.getenv('BACKEND_PORT', '8000'))
    
    @property
    def cors_origins(self) -> list:
        origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
        return [origin.strip() for origin in origins.split(',')]
    
    @property
    def log_level(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO')
    
    @property
    def resend_api_key(self) -> str:
        return os.getenv('RESEND_API_KEY', '')
    
    @property
    def from_email(self) -> str:
        return os.getenv('FROM_EMAIL', 'onboarding@resend.dev')
    
    # Legacy SMTP support (fallback)
    @property
    def smtp_server(self) -> str:
        return os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    
    @property
    def smtp_port(self) -> int:
        return int(os.getenv('SMTP_PORT', '587'))
    
    @property
    def smtp_username(self) -> str:
        return os.getenv('SMTP_USERNAME', '')
    
    @property
    def smtp_password(self) -> str:
        return os.getenv('SMTP_PASSWORD', '')
    
    @property
    def monitoring_interval(self) -> int:
        return int(os.getenv('MONITORING_INTERVAL', '300'))  # 5 minutes default
    
    # Twitter OAuth 1.0a configuration
    @property
    def twitter_consumer_key(self) -> str:
        return os.getenv('TWITTER_CONSUMER_KEY', '')
    
    @property
    def twitter_consumer_secret(self) -> str:
        return os.getenv('TWITTER_CONSUMER_SECRET', '')
    
    @property
    def twitter_callback_url(self) -> str:
        return os.getenv('TWITTER_CALLBACK_URL', 'http://localhost:3000')

# Global config instance
config = Config()