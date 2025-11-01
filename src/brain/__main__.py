"""
CLI entry point for Brain.

Allows running: python -m brain
"""

import asyncio
from .repl import main

if __name__ == '__main__':
    asyncio.run(main())
