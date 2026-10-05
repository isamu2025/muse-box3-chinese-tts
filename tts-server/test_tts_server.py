import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.requests import ClientDisconnect
import tts_server as server


class FakeSpeech:
    def __init__(self, *args, **kwargs):
        self.closed = False

    async def stream(self):
        try:
            yield {"type": "WordBoundary", "text": "ignored"}
            yield {"type": "audio", "data": b"\xff\xf3\x64\xc4abc"}
            yield {"type": "audio", "data": b"def"}
        finally:
            self.closed = True


class SpeechTests(unittest.TestCase):
    def setUp(self):
        server.slots = asyncio.Semaphore(2)

    def test_streams_audio_and_releases_slot(self):
        with patch.object(server.edge_tts, "Communicate", FakeSpeech), TestClient(server.app) as client:
            response = client.post("/tts", content="你好\nMuse", headers={"Content-Type": "text/plain; charset=utf-8"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["content-type"], "audio/mpeg")
            self.assertEqual(response.content, b"\xff\xf3\x64\xc4abcdef")
        self.assertEqual(server.slots._value, 2)

    def test_rejects_invalid_input_without_upstream_request(self):
        with patch.object(server.edge_tts, "Communicate") as upstream, TestClient(server.app) as client:
            for body, content_type, status in [(b"x", "application/json", 415),
                                                (b"\xff", "text/plain", 400),
                                                (b" \n", "text/plain", 400),
                                                (b"x" * 4096, "text/plain", 413)]:
                with self.subTest(status=status):
                    self.assertEqual(client.post("/tts", content=body, headers={"Content-Type": content_type}).status_code, status)
            upstream.assert_not_called()

    def test_upstream_failure_releases_slot(self):
        class BrokenSpeech(FakeSpeech):
            async def stream(self):
                raise RuntimeError("upstream unavailable")
                yield
        with patch.object(server.edge_tts, "Communicate", BrokenSpeech), TestClient(server.app) as client:
            with self.assertRaises(RuntimeError):
                client.post("/tts", content=b"hello", headers={"Content-Type": "text/plain"})
        self.assertEqual(server.slots._value, 2)

    def test_busy_server_returns_503(self):
        server.slots = asyncio.Semaphore(0)
        with TestClient(server.app) as client:
            self.assertEqual(client.post("/tts", content=b"hello", headers={"Content-Type": "text/plain"}).status_code, 503)


class CancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancel_closes_upstream_generator(self):
        speech = FakeSpeech()
        with patch.object(server.edge_tts, "Communicate", return_value=speech):
            stream = server.speech_chunks("hello")
            await anext(stream)
            await stream.aclose()
        self.assertTrue(speech.closed)

    async def test_response_releases_slot_if_headers_cannot_be_sent(self):
        server.slots = asyncio.Semaphore(0)
        response = server.SpeechResponse(server.speech_chunks("hello"), media_type="audio/mpeg")
        async def send(message):
            raise OSError("client disconnected")
        async def receive():
            await asyncio.sleep(10)
        with self.assertRaises((OSError, ClientDisconnect)):
            await response({"type": "http", "asgi": {"spec_version": "2.4"}}, receive, send)
        self.assertEqual(server.slots._value, 1)


if __name__ == "__main__":
    unittest.main()
