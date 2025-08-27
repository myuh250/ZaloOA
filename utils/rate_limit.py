import time
import logging


logger = logging.getLogger(__name__)

# In-memory store for user last message timestamps
user_last_message = {}

# Minimum interval between messages from the same user (seconds)
MIN_MESSAGE_INTERVAL = 5

# Timestamp of last cleanup
last_cleanup = time.time()


def cleanup_rate_limit_cache() -> None:
    """Clean up stale user timestamps periodically to limit memory usage."""
    global last_cleanup, user_last_message
    current_time = time.time()

    # Cleanup every 30 minutes
    if current_time - last_cleanup > 300:
        # Remove users inactive for over 1 hour
        cutoff_time = current_time - 600
        user_last_message = {
            uid: timestamp for uid, timestamp in user_last_message.items()
            if timestamp > cutoff_time
        }
        last_cleanup = current_time
        logger.info(
            f"Rate limit cache cleaned up, {len(user_last_message)} active users remaining"
        )


def is_rate_limited(user_id: str) -> bool:
    """Return True if the user should be rate limited, False otherwise."""
    cleanup_rate_limit_cache()

    current_time = time.time()
    last_time = user_last_message.get(user_id, 0)

    if current_time - last_time < MIN_MESSAGE_INTERVAL:
        logger.warning(
            f"Rate limited user {user_id}: {current_time - last_time:.1f}s since last message"
        )
        return True

    user_last_message[user_id] = current_time
    return False

