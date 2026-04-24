import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtWidgets import QApplication

from core.video_job import JobStatus, VideoJob
from core.video_probe import VideoMetadata
from ui.job_list_widget import JobListWidget


def build_meta(path: str) -> VideoMetadata:
    return VideoMetadata(
        path=path,
        codec_name="h264",
        codec_long_name="H.264",
        width=1920,
        height=1080,
        fps=30.0,
        duration=60.0,
        bitrate=4_000_000,
        file_size=30 * 1024 * 1024,
        audio_codec="aac",
        audio_sample_rate=48000,
        audio_channels=2,
        format_name="mp4",
    )


class JobListWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_remove_first_job_keeps_remaining_rows_accessible(self):
        widget = JobListWidget()
        job1 = VideoJob(input_path="C:/clips/one.mp4", source_metadata=build_meta("one.mp4"))
        job2 = VideoJob(input_path="C:/clips/two.mp4", source_metadata=build_meta("two.mp4"))

        widget.add_job(job1)
        widget.add_job(job2)
        widget.remove_job(job1)

        self.assertEqual(widget._count_label.text(), "1 file")
        self.assertFalse(widget._empty_label.isVisible())

        job2.status = JobStatus.RUNNING
        widget.update_status(job2)
        widget.update_progress(job2, 42.0)

        row = widget._rows[id(job2)]
        self.assertEqual(row._status_label.text(), "Processing")
        self.assertEqual(row._progress_bar.value(), 42)

    def test_duplicate_input_paths_can_coexist_and_remove_independently(self):
        widget = JobListWidget()
        job1 = VideoJob(input_path="C:/clips/shared.mp4", source_metadata=build_meta("shared.mp4"))
        job2 = VideoJob(input_path="C:/clips/shared.mp4", source_metadata=build_meta("shared.mp4"))

        widget.add_job(job1)
        widget.add_job(job2)
        widget.remove_job(job1)

        self.assertEqual(widget._count_label.text(), "1 file")
        self.assertIn(id(job2), widget._rows)


if __name__ == "__main__":
    unittest.main()
