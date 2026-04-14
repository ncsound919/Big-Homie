"""
Big Homie Integrations
Centralized integration registry for external services
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from loguru import logger

class IntegrationType(str, Enum):
    """Types of integrations"""
    CLOUD = "cloud"
    DEPLOYMENT = "deployment"
    PAYMENT = "payment"
    BLOCKCHAIN = "blockchain"
    DATA = "data"
    AI = "ai"
    BANKING = "banking"
    TRADING = "trading"
    CRYPTO = "crypto"
    BETTING = "betting"
    ECOMMERCE = "ecommerce"
    SUPPLY_CHAIN = "supply_chain"
    TELEPHONY = "telephony"
    FREELANCE = "freelance"

@dataclass
class IntegrationStatus:
    """Status of an integration"""
    name: str
    type: IntegrationType
    enabled: bool
    configured: bool
    healthy: bool
    error: Optional[str] = None

class IntegrationRegistry:
    """Registry for all external integrations"""

    def __init__(self):
        self._integrations: Dict[str, Any] = {}
        self._status: Dict[str, IntegrationStatus] = {}

    def register(self, name: str, integration: Any, integration_type: IntegrationType):
        """Register an integration"""
        self._integrations[name] = integration
        self._status[name] = IntegrationStatus(
            name=name,
            type=integration_type,
            enabled=True,
            configured=False,
            healthy=False
        )
        logger.info(f"Registered integration: {name} ({integration_type.value})")

    def get(self, name: str) -> Optional[Any]:
        """Get an integration by name"""
        return self._integrations.get(name)

    def get_status(self, name: str) -> Optional[IntegrationStatus]:
        """Get status of an integration"""
        return self._status.get(name)

    def list_integrations(self) -> List[IntegrationStatus]:
        """List all integrations and their status"""
        return list(self._status.values())

    async def health_check_all(self) -> Dict[str, bool]:
        """Run health checks on all integrations"""
        results = {}
        for name, integration in self._integrations.items():
            if hasattr(integration, 'health_check'):
                try:
                    healthy = await integration.health_check()
                    results[name] = healthy
                    self._status[name].healthy = healthy
                    self._status[name].error = None
                except Exception as e:
                    results[name] = False
                    self._status[name].healthy = False
                    self._status[name].error = str(e)
                    logger.error(f"Health check failed for {name}: {e}")
            else:
                results[name] = False
                self._status[name].healthy = False
                self._status[name].error = None
        return results

# Global registry
registry = IntegrationRegistry()
