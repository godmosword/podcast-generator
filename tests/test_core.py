from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from pydub import AudioSegment
from pydub.generators import Sine

from backend.bgm_catalog import BgmNotFoundError, get_bgm_track, list_bgm_tracks
from backend.jobs import Job, jobs
from backend.main import app
from config import Config
from core.audio_processor import mix_bgm
from core.role_mapper import RoleMappingError, map_roles_to_voices
from core.script_parser import parse_script_details


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
            Sine(440).to_audio_segment(duration=1000).export(bgm_path, format="wav")
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


if __name__ == "__main__":
    unittest.main()
