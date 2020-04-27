import pytest

from aiohttp_rest_framework.db import DatabaseServiceABC


async def test_abc_service():
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        DatabaseServiceABC()
