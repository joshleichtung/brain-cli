"""
Run the observability API server.

Usage:
    python -m brain.observability.server

Or:
    uvicorn brain.observability.api:app --reload
"""

import uvicorn


def main():
    """Run the observability API server."""
    uvicorn.run(
        "brain.observability.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
