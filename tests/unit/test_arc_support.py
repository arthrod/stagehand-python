import asyncio
import unittest.mock as mock

import pytest

from stagehand import Stagehand
from stagehand.config import StagehandConfig
import httpx


@pytest.mark.asyncio
async def test_create_arc_session_sets_session_and_cdp_url(monkeypatch):
    config = StagehandConfig(env="ARC")
    client = Stagehand(config=config)

    mock_process = mock.Mock()

    async def fake_launch_arc(port):
        return mock_process

    with mock.patch("stagehand.api.launch_arc_browser", fake_launch_arc), \
         mock.patch("asyncio.sleep", new=mock.AsyncMock()):
        await client._create_arc_session()

    assert client.session_id is not None
    assert client.local_browser_launch_options["cdp_url"] == "http://localhost:9222"
    assert client._arc_process is mock_process


@pytest.mark.asyncio
async def test_create_arc_session_respects_custom_cdp_url(monkeypatch):
    config = StagehandConfig(
        env="ARC", local_browser_launch_options={"cdp_url": "http://localhost:9333"}
    )
    client = Stagehand(config=config)

    mock_process = mock.Mock()
    captured = {}

    async def fake_launch_arc(port):
        captured["port"] = port
        return mock_process

    with mock.patch("stagehand.api.launch_arc_browser", fake_launch_arc), \
         mock.patch("asyncio.sleep", new=mock.AsyncMock()):
        await client._create_arc_session()

    assert captured["port"] == 9333
    assert client.local_browser_launch_options["cdp_url"] == "http://localhost:9333"
    assert client._arc_process is mock_process


@pytest.mark.asyncio
async def test_create_arc_session_falls_back_to_chromium(monkeypatch):
    config = StagehandConfig(env="ARC")
    client = Stagehand(config=config)

    async def fake_launch_arc(port):
        raise FileNotFoundError("Arc not installed")

    with mock.patch("stagehand.api.launch_arc_browser", fake_launch_arc), \
         mock.patch("asyncio.sleep", new=mock.AsyncMock()):
        await client._create_arc_session()

    assert client.session_id is not None
    assert "cdp_url" not in client.local_browser_launch_options
    assert client._arc_process is None


@pytest.mark.asyncio
async def test_init_calls_create_arc_session(monkeypatch):
    config = StagehandConfig(env="ARC")
    client = Stagehand(config=config)

    mock_playwright = mock.Mock()
    mock_playwright_instance = mock.AsyncMock()
    mock_playwright_instance.start = mock.AsyncMock(return_value=mock_playwright)

    mock_browser_tuple = (mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock(), None)

    async def fake_create_arc_session():
        client.local_browser_launch_options["cdp_url"] = "http://localhost:9222"

    with mock.patch("stagehand.main.async_playwright", return_value=mock_playwright_instance), \
         mock.patch("stagehand.main.connect_local_browser", new=mock.AsyncMock(return_value=mock_browser_tuple)), \
         mock.patch.object(Stagehand, "_create_arc_session", new=mock.AsyncMock(side_effect=fake_create_arc_session)) as mock_arc:
        await client.init()
        mock_arc.assert_awaited_once()
        assert client.local_browser_launch_options["cdp_url"] == "http://localhost:9222"


@pytest.mark.asyncio
async def test_attach_arc_session_sets_session_and_cdp_url(monkeypatch):
    config = StagehandConfig(env="ARC_PERSIST")
    client = Stagehand(config=config)

    mock_resp = mock.Mock()
    mock_resp.status_code = 200
    with mock.patch.object(client._client, "get", return_value=mock_resp), \
         mock.patch("stagehand.api.launch_arc_browser") as launch_mock:
        await client._attach_arc_session()
        launch_mock.assert_not_called()

    assert client.session_id is not None
    assert client.local_browser_launch_options["cdp_url"] == "http://localhost:9222"


@pytest.mark.asyncio
async def test_attach_arc_session_falls_back_to_chromium(monkeypatch):
    config = StagehandConfig(env="ARC_PERSIST")
    client = Stagehand(config=config)

    async def fake_get(url, *args, **kwargs):
        raise httpx.ConnectError("no arc", request=None)

    with mock.patch.object(client._client, "get", side_effect=fake_get):
        await client._attach_arc_session()

    assert client.session_id is not None
    assert "cdp_url" not in client.local_browser_launch_options


@pytest.mark.asyncio
async def test_attach_arc_session_respects_custom_cdp_url(monkeypatch):
    config = StagehandConfig(
        env="ARC_PERSIST", local_browser_launch_options={"cdp_url": "http://localhost:9333"}
    )
    client = Stagehand(config=config)

    mock_resp = mock.Mock()
    mock_resp.status_code = 200
    with mock.patch.object(client._client, "get", return_value=mock_resp):
        await client._attach_arc_session()

    assert client.session_id is not None
    assert client.local_browser_launch_options["cdp_url"] == "http://localhost:9333"


@pytest.mark.asyncio
async def test_init_calls_attach_arc_session(monkeypatch):
    config = StagehandConfig(env="ARC_PERSIST")
    client = Stagehand(config=config)

    mock_playwright = mock.Mock()
    mock_playwright_instance = mock.AsyncMock()
    mock_playwright_instance.start = mock.AsyncMock(return_value=mock_playwright)

    mock_browser_tuple = (mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock(), None)

    async def fake_attach_arc_session():
        client.local_browser_launch_options["cdp_url"] = "http://localhost:9222"

    with mock.patch("stagehand.main.async_playwright", return_value=mock_playwright_instance), \
         mock.patch("stagehand.main.connect_local_browser", new=mock.AsyncMock(return_value=mock_browser_tuple)), \
         mock.patch.object(Stagehand, "_attach_arc_session", new=mock.AsyncMock(side_effect=fake_attach_arc_session)) as mock_attach:
        await client.init()
        mock_attach.assert_awaited_once()
        assert client.local_browser_launch_options["cdp_url"] == "http://localhost:9222"
