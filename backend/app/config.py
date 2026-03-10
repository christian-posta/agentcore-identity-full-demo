import os
from typing import List

class Settings:
    # API Configuration
    api_title: str = "Supply Chain Agent API"
    api_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Server Configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # CORS Configuration
    cors_allow_all: bool = os.getenv("CORS_ALLOW_ALL", "true").lower() == "true"
    allowed_origins: List[str] = ["*"] if os.getenv("CORS_ALLOW_ALL", "true").lower() == "true" else os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3050,http://127.0.0.1:3000,http://127.0.0.1:3050,http://localhost:5173,http://127.0.0.1:5173").split(",")
    
    # Auth0 Configuration
    auth0_domain: str = os.getenv("AUTH0_DOMAIN", "")
    auth0_audience: str = os.getenv("AUTH0_AUDIENCE", "")
    
    # Agent Configuration
    max_concurrent_agents: int = 5
    agent_timeout_seconds: int = 300
    
    # A2A Configuration (AgentGateway base URL; backend sends Auth0 token directly)
    supply_chain_agent_url: str = os.getenv("SUPPLY_CHAIN_AGENT_URL", "http://localhost:3000/supply-chain-agent")

settings = Settings()
