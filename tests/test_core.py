from __future__ import annotations

import unittest
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


if __name__ == "__main__":
    unittest.main()
