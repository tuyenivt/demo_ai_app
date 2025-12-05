from httpx import HTTPStatusError


def should_retry_http(e: Exception) -> bool:
    """
    Determine whether the HTTP exception should be retried.

    Retry only:
    - 429 Too Many Requests
    - 5xx server errors
    """
    if isinstance(e, HTTPStatusError):
        status = e.response.status_code
        return status == 429 or 500 <= status < 600

    return False
