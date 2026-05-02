from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from pydub import AudioSegment
from pydub.generators import Sine

from backend.bgm_catalog import BgmNotFoundError, get_bgm_track, list_bgm_tracks
from backend.config import VOICE_CATALOG, voice_provider
from backend.jobs import Job, jobs
from backend.main import app
from backend.security import get_client_ip, rate_limiter
from backend.routers.generate import GENERIC_GENERATE_ERROR, _run_job
from config import Config, Provider, voice_pitch
from core.audio_processor import mix_bgm
from core.role_mapper import RoleMappingError, map_roles_to_voices
from core.script_generator import ScriptSpec, _validate_and_clean
from core.script_parser import parse_script_details
from utils.script_metrics import measure_script


class ScriptParserTests(unittest.TestCase):
    def test_parses_speakers_in_order(self) -> None:
        parsed = parse_script_details("[主持人A]: 哈囉\n---PAUSE:0.5s---\n[主持人B]: 你好")

        self.assertEqual(parsed.speaker_count, 2)
        self.assertEqual(parsed.speakers, ["主持人A", "主持人B"])
        self.assertEqual(parsed.turns[0].index, 0)
        self.assertTrue(parsed.turns[1].is_silence)
        self.assertEqual(parsed.turns[1].pause_after_ms, 500)

    def test_plain_text_uses_single_speaker(self) -> None:
        parsed = parse_script_details("大家好\n歡迎收聽")

        self.assertEqual(parsed.speaker_count, 1)
        self.assertEqual(parsed.speakers, ["speaker_1"])


class RoleMapperTests(unittest.TestCase):
    def test_uses_overrides_first(self) -> None:
        mapping = map_roles_to_voices(["主持人A"], Config(), overrides={"主持人A": "zh-TW-YunJheNeural"})

        self.assertEqual(mapping["主持人A"], "zh-TW-YunJheNeural")

    def test_rejects_too_many_speakers(self) -> None:
        with self.assertRaises(RoleMappingError):
            map_roles_to_voices(["A", "B", "C", "D", "E"], Config())


class TTSConfigTests(unittest.TestCase):
    def test_voice_catalog_is_limited_to_requested_languages(self) -> None:
        edge_voices = [voice for voice in VOICE_CATALOG if voice["provider"] == Provider.EDGE.value]
        groups = {
            "zh-TW": [voice for voice in edge_voices if voice["language"] == "zh-TW"],
            "English": [voice for voice in edge_voices if voice["language"].startswith("en-")],
            "ja-JP": [voice for voice in edge_voices if voice["language"] == "ja-JP"],
        }

        self.assertEqual({voice["language"] for voice in edge_voices}, {"zh-TW", "en-US", "en-GB", "ja-JP"})
        self.assertEqual({key: len(value) for key, value in groups.items()}, {"zh-TW": 8, "English": 8, "ja-JP": 8})

    def test_child_voice_pitch_profiles(self) -> None:
        self.assertEqual(voice_pitch("zh-TW-YunJheNeural__boy-1"), "+22Hz")
        self.assertEqual(voice_pitch("zh-TW-HsiaoYuNeural__girl-2"), "+32Hz")
        self.assertEqual(voice_pitch("ja-JP-KeitaNeural__adult-male-2"), "-2Hz")
        self.assertEqual(voice_pitch("zh-TW-HsiaoChenNeural"), "+0Hz")

    def test_voice_provider_detects_paid_provider_voices(self) -> None:
        self.assertEqual(voice_provider("nova"), Provider.OPENAI)
        self.assertEqual(voice_provider("Rachel"), Provider.ELEVENLABS)
        self.assertEqual(voice_provider("zh-TW-HsiaoChenNeural"), Provider.EDGE)

    def test_production_cors_rejects_wildcard_or_empty_origins(self) -> None:
        with patch.dict(os.environ, {"APP_ENV": "production", "CORS_ORIGINS": "*"}):
            with self.assertRaises(ValueError):
                Config()

        with patch.dict(os.environ, {"APP_ENV": "production", "CORS_ORIGINS": ""}):
            with self.assertRaises(ValueError):
                Config()


class ScriptMetricsTests(unittest.TestCase):
    def test_english_metrics_ignore_chinese_speaker_tags(self) -> None:
        script = "[主持人A]: Hello world from Wavescript.\n[主持人B]: This is a clean estimate."
        metrics = measure_script(script, "en")

        self.assertEqual(metrics.unit_count, 9)
        self.assertEqual(metrics.unit_label_short, "words")

    def test_script_generator_validation_uses_language_units(self) -> None:
        spec = ScriptSpec(topic="AI", duration_min=5, host_count=1, tone="educational", language="en")
        body = " ".join(f"word{i}" for i in range(730))
        script, warnings = _validate_and_clean(f"[主持人A]: {body}", spec)

        self.assertTrue(script.startswith("[主持人A]:"))
        self.assertEqual(warnings, [])


class BgmCatalogTests(unittest.TestCase):
    def test_lists_manifest_tracks(self) -> None:
        with TemporaryDirectory() as temp_dir:
            bgm_dir = Path(temp_dir)
            (bgm_dir / "theme.wav").write_bytes(b"placeholder")
            (bgm_dir / "manifest.json").write_text(
                '[{"id":"theme","title":"Theme","mood":"bright","filename":"theme.wav","duration":12}]',
                encoding="utf-8",
            )

            tracks = list_bgm_tracks(bgm_dir)

            self.assertEqual(len(tracks), 1)
            self.assertEqual(tracks[0].id, "theme")
            self.assertEqual(tracks[0].title, "Theme")
            self.assertEqual(tracks[0].preview_url, "/api/bgm/theme/preview")

    def test_unknown_bgm_id_raises(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(BgmNotFoundError):
                get_bgm_track("missing", Path(temp_dir))


class AudioProcessorTests(unittest.TestCase):
    def test_mix_bgm_volume_parameter_changes_result_level(self) -> None:
        with TemporaryDirectory() as temp_dir:
            bgm_path = Path(temp_dir) / "tone.wav"
            exported = Sine(440).to_audio_segment(duration=1000).export(bgm_path, format="wav")
            exported.close()
            speech = AudioSegment.silent(duration=1000)

            quiet = mix_bgm(speech, str(bgm_path), bgm_volume_db=-30, fade_ms=0)
            loud = mix_bgm(speech, str(bgm_path), bgm_volume_db=-6, fade_ms=0)

            self.assertGreater(loud.dBFS, quiet.dBFS)


class ApiValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        rate_limiter.reset()

    def test_generate_rejects_unknown_bgm_id(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/api/generate",
            json={
                "script": "[主持人A]: 哈囉",
                "host_count": 1,
                "voice_assignments": [{"role": "主持人A", "voice": "zh-TW-HsiaoChenNeural"}],
                "audio": {"bgm_enabled": True, "bgm_id": "missing-track", "output_format": "mp3"},
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown BGM track", response.json()["detail"])

    def test_generate_rejects_unknown_voice_id(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/api/generate",
            json={
                "script": "[主持人A]: 哈囉",
                "host_count": 1,
                "voice_assignments": [{"role": "主持人A", "voice": "not-a-voice"}],
                "audio": {"bgm_enabled": False, "output_format": "mp3"},
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_preview_rejects_unknown_voice_id(self) -> None:
        client = TestClient(app)
        response = client.post("/api/preview", json={"text": "hello", "voice": "not-a-voice"})

        self.assertEqual(response.status_code, 422)

    def test_generate_rejects_too_long_script(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/api/generate",
            json={
                "script": "x" * 50001,
                "host_count": 1,
                "voice_assignments": [{"role": "主持人A", "voice": "zh-TW-HsiaoChenNeural"}],
                "audio": {"bgm_enabled": False, "output_format": "mp3"},
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_generate_rejects_too_many_voice_assignments(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/api/generate",
            json={
                "script": "[A]: one",
                "host_count": 4,
                "voice_assignments": [
                    {"role": f"host{i}", "voice": "zh-TW-HsiaoChenNeural"}
                    for i in range(5)
                ],
                "audio": {"bgm_enabled": False, "output_format": "mp3"},
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_generate_rejects_invalid_output_format(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/api/generate",
            json={
                "script": "[主持人A]: 哈囉",
                "host_count": 1,
                "voice_assignments": [{"role": "主持人A", "voice": "zh-TW-HsiaoChenNeural"}],
                "audio": {"bgm_enabled": False, "output_format": "flac"},
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_generate_rate_limit_returns_429(self) -> None:
        client = TestClient(app)
        payload = {
            "script": "[主持人A]: 哈囉",
            "host_count": 1,
            "voice_assignments": [{"role": "主持人A", "voice": "zh-TW-HsiaoChenNeural"}],
            "audio": {"bgm_enabled": True, "bgm_id": "missing-track", "output_format": "mp3"},
        }

        with patch.dict(os.environ, {"RATE_LIMIT_GENERATE_PER_MINUTE": "2"}):
            self.assertEqual(client.post("/api/generate", json=payload).status_code, 400)
            self.assertEqual(client.post("/api/generate", json=payload).status_code, 400)
            self.assertEqual(client.post("/api/generate", json=payload).status_code, 429)

    def test_preview_rate_limit_returns_429(self) -> None:
        client = TestClient(app)
        payload = {"text": "hello", "voice": "nova"}

        with patch.dict(os.environ, {"RATE_LIMIT_PREVIEW_PER_MINUTE": "2", "OPENAI_API_KEY": ""}):
            with patch("backend.routers.preview.logger.exception"):
                self.assertEqual(client.post("/api/preview", json=payload).status_code, 503)
                self.assertEqual(client.post("/api/preview", json=payload).status_code, 503)
            self.assertEqual(client.post("/api/preview", json=payload).status_code, 429)

    def test_script_generation_rate_limit_returns_429(self) -> None:
        client = TestClient(app)
        payload = {"topic": "AI", "duration_min": 5, "host_count": 1}

        with patch.dict(os.environ, {"RATE_LIMIT_AI_PER_MINUTE": "2", "ANTHROPIC_API_KEY": ""}):
            self.assertEqual(client.post("/api/script/generate", json=payload).status_code, 503)
            self.assertEqual(client.post("/api/script/generate", json=payload).status_code, 503)
            self.assertEqual(client.post("/api/script/generate", json=payload).status_code, 429)

    def test_analyze_rate_limit_returns_429(self) -> None:
        client = TestClient(app)
        payload = {"text": "這是一段足夠長的分析文字內容。", "language": "zh-TW"}

        with patch.dict(os.environ, {"RATE_LIMIT_AI_PER_MINUTE": "2", "ANTHROPIC_API_KEY": ""}):
            self.assertEqual(client.post("/api/analyze", json=payload).status_code, 503)
            self.assertEqual(client.post("/api/analyze", json=payload).status_code, 503)
            self.assertEqual(client.post("/api/analyze", json=payload).status_code, 429)

    def test_generate_job_hides_raw_synthesis_errors(self) -> None:
        async def fail_run_text(*args, **kwargs) -> str:
            raise RuntimeError("secret path /tmp/api-key")

        request = {
            "script": "[主持人A]: 哈囉",
            "host_count": 1,
            "voice_assignments": [{"role": "主持人A", "voice": "zh-TW-HsiaoChenNeural"}],
            "audio": {"bgm_enabled": False, "output_format": "mp3"},
        }
        from backend.models.schemas import GenerateRequest

        job_id = "failed-job"
        jobs[job_id] = Job(id=job_id)
        try:
            with (
                patch("backend.routers.generate.PodcastPipeline.run_text", new=fail_run_text),
                patch("backend.routers.generate.logger.exception"),
            ):
                asyncio.run(_run_job(job_id, GenerateRequest(**request)))

            self.assertEqual(jobs[job_id].error, GENERIC_GENERATE_ERROR)
            event = jobs[job_id].events.get_nowait()
            self.assertEqual(event["error"], GENERIC_GENERATE_ERROR)
            self.assertNotIn("secret", event["message"])
        finally:
            jobs.pop(job_id, None)

    def test_done_event_snapshot_includes_file_url(self) -> None:
        client = TestClient(app)
        job_id = "test-done-job"
        jobs[job_id] = Job(id=job_id, status="done", progress=100, message="Done.", output_path=Path("output/test.mp3"))

        try:
            with client.stream("GET", f"/api/generate/{job_id}/events") as response:
                first_line = next(response.iter_lines())

            self.assertEqual(response.status_code, 200)
            self.assertIn(f'"file_url":"/api/files/{job_id}"', first_line.replace(" ", ""))
        finally:
            jobs.pop(job_id, None)

    def test_prune_jobs_removes_old_completed_output(self) -> None:
        from backend.jobs import prune_jobs

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "old.mp3"
            output_path.write_bytes(b"audio")
            now = datetime.now(timezone.utc)
            job = Job(
                id="old-job",
                status="done",
                progress=100,
                message="Done.",
                output_path=output_path,
                created_at=now - timedelta(seconds=20),
                updated_at=now - timedelta(seconds=20),
            )
            jobs[job.id] = job

            try:
                removed = prune_jobs(ttl_seconds=10, now=now)

                self.assertEqual(removed, ["old-job"])
                self.assertNotIn("old-job", jobs)
                self.assertFalse(output_path.exists())
            finally:
                jobs.pop(job.id, None)


class ProxyClientIpTests(unittest.TestCase):
    class _Client:
        def __init__(self, host: str) -> None:
            self.host = host

    class _Request:
        def __init__(self, host: str, headers: dict[str, str]) -> None:
            self.client = ProxyClientIpTests._Client(host)
            self.headers = headers

    def test_trusted_proxy_uses_forwarded_for(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TRUST_PROXY_HEADERS": "true",
                "TRUSTED_PROXY_CIDRS": "10.0.0.0/8",
            },
        ):
            config = Config()
            request = self._Request("10.1.2.3", {"x-forwarded-for": "203.0.113.7, 10.1.2.3"})

            self.assertEqual(get_client_ip(request, config), "203.0.113.7")

    def test_untrusted_proxy_ignores_forwarded_for(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TRUST_PROXY_HEADERS": "true",
                "TRUSTED_PROXY_CIDRS": "10.0.0.0/8",
            },
        ):
            config = Config()
            request = self._Request("192.0.2.10", {"x-forwarded-for": "203.0.113.7"})

            self.assertEqual(get_client_ip(request, config), "192.0.2.10")


if __name__ == "__main__":
    unittest.main()
