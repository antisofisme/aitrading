"""
Account Manager - Manages multiple OANDA accounts with failover support
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class AccountManager:
    """
    Manages multiple OANDA accounts with priority-based failover
    Tracks account health and automatically switches on failures
    """

    def __init__(
        self,
        accounts_config: List[Dict[str, Any]],
        failover_config: Dict[str, Any],
        memory_store=None
    ):
        """
        Initialize Account Manager

        Args:
            accounts_config: List of account configurations from config.yaml
            failover_config: Failover settings
            memory_store: Central Hub memory store for shared state
        """
        self.accounts = self._parse_accounts(accounts_config)
        self.failover_config = failover_config
        self.memory_store = memory_store

        # Account health tracking
        self.account_health: Dict[str, Dict[str, Any]] = {}
        self.active_account_id: Optional[str] = None
        self.cooldown_until: Dict[str, datetime] = {}

        # Initialize health tracking
        for account in self.accounts:
            self.account_health[account['id']] = {
                'failures': 0,
                'last_check': None,
                'is_healthy': True
            }

    def _parse_accounts(self, accounts_config: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse and validate account configurations"""
        valid_accounts = []

        for account in accounts_config:
            if account.get('enabled', False) and account.get('id') and account.get('token'):
                valid_accounts.append({
                    'id': account['id'],
                    'token': account['token'],
                    'priority': account.get('priority', 999),
                    'enabled': True
                })

        # Sort by priority (lower number = higher priority)
        valid_accounts.sort(key=lambda x: x['priority'])

        logger.info(f"Loaded {len(valid_accounts)} valid accounts")
        return valid_accounts

    async def initialize(self) -> bool:
        """
        Initialize account manager and select initial active account

        Returns:
            bool: True if initialization successful
        """
        if not self.accounts:
            logger.error("No valid accounts configured")
            return False

        # Select highest priority healthy account
        for account in self.accounts:
            if await self._check_account_health(account['id']):
                self.active_account_id = account['id']
                logger.info(f"Active account set to: {account['id']} (priority: {account['priority']})")
                return True

        logger.error("No healthy accounts available")
        return False

    async def get_active_account(self) -> Optional[Dict[str, Any]]:
        """
        Get currently active account

        Returns:
            Dict with account details or None if no active account
        """
        if not self.active_account_id:
            await self.initialize()

        if self.active_account_id:
            return next(
                (acc for acc in self.accounts if acc['id'] == self.active_account_id),
                None
            )
        return None

    async def failover(self) -> Optional[Dict[str, Any]]:
        """
        Perform failover to next available account

        Returns:
            Dict with new active account or None if failover failed
        """
        if not self.active_account_id:
            logger.warning("No active account to failover from")
            return await self.get_active_account()

        # Mark current account as failed
        await self._mark_account_failed(self.active_account_id)

        # Try to find next healthy account
        current_priority = next(
            (acc['priority'] for acc in self.accounts if acc['id'] == self.active_account_id),
            0
        )

        # Look for next account with lower priority (higher number)
        for account in self.accounts:
            if account['priority'] <= current_priority:
                continue

            if await self._is_account_available(account['id']):
                old_account = self.active_account_id
                self.active_account_id = account['id']
                logger.warning(
                    f"Failover: {old_account} -> {account['id']} "
                    f"(priority: {account['priority']})"
                )

                # Update shared state in Central Hub
                if self.memory_store:
                    await self.memory_store.set(
                        'active_account',
                        {
                            'account_id': account['id'],
                            'timestamp': datetime.utcnow().isoformat(),
                            'reason': 'failover'
                        }
                    )

                return account

        logger.error("No healthy account available for failover")
        return None

    async def _check_account_health(self, account_id: str) -> bool:
        """
        Check if account is healthy

        Args:
            account_id: Account ID to check

        Returns:
            bool: True if account is healthy
        """
        # Check cooldown period
        if account_id in self.cooldown_until:
            if datetime.utcnow() < self.cooldown_until[account_id]:
                logger.debug(f"Account {account_id} in cooldown period")
                return False
            else:
                # Cooldown expired, remove it
                del self.cooldown_until[account_id]

        # Check health status
        health = self.account_health.get(account_id, {})
        return health.get('is_healthy', False)

    async def _is_account_available(self, account_id: str) -> bool:
        """
        Check if account is available (healthy and not in cooldown)

        Args:
            account_id: Account ID to check

        Returns:
            bool: True if account is available
        """
        return await self._check_account_health(account_id)

    async def _mark_account_failed(self, account_id: str) -> None:
        """
        Mark account as failed and apply cooldown if needed

        Args:
            account_id: Account ID to mark as failed
        """
        if account_id not in self.account_health:
            return

        health = self.account_health[account_id]
        health['failures'] += 1
        health['last_check'] = datetime.utcnow()

        max_failures = self.failover_config.get('max_failures_before_switch', 3)

        if health['failures'] >= max_failures:
            health['is_healthy'] = False
            cooldown_seconds = self.failover_config.get('cooldown_period', 300)
            self.cooldown_until[account_id] = datetime.utcnow() + timedelta(seconds=cooldown_seconds)

            logger.warning(
                f"Account {account_id} marked unhealthy after {health['failures']} failures. "
                f"Cooldown until {self.cooldown_until[account_id].isoformat()}"
            )

            # Update shared state
            if self.memory_store:
                await self.memory_store.set(
                    f'account_health:{account_id}',
                    {
                        'is_healthy': False,
                        'failures': health['failures'],
                        'cooldown_until': self.cooldown_until[account_id].isoformat()
                    }
                )

    async def mark_account_healthy(self, account_id: str) -> None:
        """
        Mark account as healthy and reset failure count

        Args:
            account_id: Account ID to mark as healthy
        """
        if account_id not in self.account_health:
            return

        health = self.account_health[account_id]
        health['failures'] = 0
        health['is_healthy'] = True
        health['last_check'] = datetime.utcnow()

        # Remove cooldown
        if account_id in self.cooldown_until:
            del self.cooldown_until[account_id]

        logger.info(f"Account {account_id} marked healthy")

        # Update shared state
        if self.memory_store:
            await self.memory_store.set(
                f'account_health:{account_id}',
                {
                    'is_healthy': True,
                    'failures': 0,
                    'last_check': datetime.utcnow().isoformat()
                }
            )

    async def run_health_checks(self) -> None:
        """
        Periodically check health of all accounts
        Should be run as a background task
        """
        interval = self.failover_config.get('health_check_interval', 60)

        while True:
            try:
                for account in self.accounts:
                    # Skip if in cooldown
                    if account['id'] in self.cooldown_until:
                        if datetime.utcnow() < self.cooldown_until[account['id']]:
                            continue

                    # Simple health check - could be enhanced with actual API call
                    health = self.account_health.get(account['id'], {})
                    if health.get('failures', 0) == 0:
                        health['is_healthy'] = True

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(interval)

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all configured accounts

        Returns:
            List of account dictionaries
        """
        return self.accounts

    def get_account_status(self) -> Dict[str, Any]:
        """
        Get status of all accounts

        Returns:
            Dict containing account health information
        """
        return {
            'active_account': self.active_account_id,
            'accounts': [
                {
                    'id': acc['id'],
                    'priority': acc['priority'],
                    'health': self.account_health.get(acc['id'], {}),
                    'in_cooldown': acc['id'] in self.cooldown_until,
                    'cooldown_until': self.cooldown_until.get(acc['id'], None)
                }
                for acc in self.accounts
            ]
        }
