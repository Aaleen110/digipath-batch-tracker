import ipaddress
import socket
import time
from urllib.parse import urlparse

import httpx


class WebhookNotificationError(Exception):
    """Raised when a webhook notification fails after all retries."""


class UnsafeWebhookURLError(Exception):
    """Raised when a webhook URL points to an unsafe destination."""


MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1
REQUEST_TIMEOUT_SECONDS = 5


def validate_webhook_url(webhook_url: str) -> None:
    """
    Validate that a webhook URL is safe for the server to call.

    The webhook URL is ultimately controlled by API input, so we must
    not blindly make an outbound request to any arbitrary address.
    """

    parsed_url = urlparse(webhook_url)

    # We only allow HTTPS because webhook communication may contain
    # sensitive batch information and should be encrypted in transit.
    if parsed_url.scheme != "https":
        raise UnsafeWebhookURLError(
            "Webhook URL must use HTTPS"
        )

    hostname = parsed_url.hostname

    if not hostname:
        raise UnsafeWebhookURLError(
            "Webhook URL must contain a hostname"
        )

    # Resolve the hostname before making the request. A hostname can
    # look public (for example, example.com) but resolve to a private
    # or internal IP address. This check helps prevent SSRF attacks.
    try:
        addresses = socket.getaddrinfo(
            hostname,
            None,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise UnsafeWebhookURLError(
            "Webhook hostname could not be resolved"
        ) from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        # Never allow requests to private, loopback, link-local,
        # multicast, or otherwise non-public IP addresses.
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise UnsafeWebhookURLError(
                "Webhook URL resolves to a non-public IP address"
            )


def notify_webhook(
    webhook_url: str,
    payload: dict,
) -> None:
    """
    Send a webhook notification with exponential backoff retries.
    """

    validate_webhook_url(webhook_url)

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = httpx.post(
                webhook_url,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            response.raise_for_status()

            return

        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            if attempt == MAX_RETRIES:
                raise WebhookNotificationError(
                    "Webhook notification failed after all retries"
                ) from exc

            # Exponential backoff prevents us from repeatedly hitting
            # a partner service that may already be unavailable.
            backoff = INITIAL_BACKOFF_SECONDS * (2**attempt)

            time.sleep(backoff)