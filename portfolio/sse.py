import json
import logging
import time

from django.utils import timezone

from .services import PortfolioService

logger = logging.getLogger(__name__)


def portfolio_sse_stream(user):
    """Generate SSE events for portfolio updates

    Yields portfolio data every 100ms (10Hz max as per requirements)
    """
    portfolio_service = PortfolioService(user)

    while True:
        try:
            # Get current portfolio data
            summary = portfolio_service.get_portfolio_summary()

            # Format for SSE
            data = {
                "type": "portfolio-update",
                "timestamp": timezone.now().isoformat(),
                "total_value_usd": summary["total_value_usd"],
                "change_24h": summary["change_24h"],
            }

            yield json.dumps(data)

            # Wait before next update (throttled to 10Hz max as per requirements)
            time.sleep(0.1)  # 100ms = 10Hz

        except Exception as e:
            # Log error and continue
            logger.error(f"SSE Error for user {user.id}: {e}")

            # Send error event
            error_data = {
                "type": "error",
                "message": "Failed to fetch portfolio data",
                "timestamp": timezone.now().isoformat(),
            }
            yield json.dumps(error_data)

            # Wait longer before retrying after error
            time.sleep(5)
