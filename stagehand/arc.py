import asyncio
from pathlib import Path


async def launch_arc_browser(port: int = 9222) -> asyncio.subprocess.Process:
    """Launch the Arc browser with remote debugging enabled.

    Args:
        port: The debugging port to expose.

    Returns:
        The created subprocess running Arc.
    """
    arc_path = Path("/Applications/Arc.app/Contents/MacOS/Arc")
    if not arc_path.exists():
        raise FileNotFoundError(f"Arc browser not found at {arc_path}")

    return await asyncio.create_subprocess_exec(
        str(arc_path),
        f"--remote-debugging-port={port}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
