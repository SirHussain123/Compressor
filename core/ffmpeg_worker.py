"""
ffmpeg_worker.py
----------------
QThread-based worker that executes a VideoJob using FFmpeg.
Emits signals for progress, completion, and errors so the UI stays responsive.
"""


import subprocess
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from core.video_job import VideoJob, JobStatus


class FFmpegWorker(QThread):
    """
    Runs an FFmpeg command for a single VideoJob in a background thread.

    Signals:
        progress(float):         0.0 – 100.0 progress value
        job_complete(VideoJob):  Emitted when FFmpeg exits successfully
        job_failed(VideoJob, str): Emitted on non-zero exit or exception
    """

    progress    = pyqtSignal(float)
    job_complete = pyqtSignal(object)
    job_failed   = pyqtSignal(object, str)

    def __init__(self, job: VideoJob, parent=None):
        super().__init__(parent)
        self.job = job
        self._process: subprocess.Popen | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self):
        """Entry point — called by QThread.start()."""
        self.job.status = JobStatus.RUNNING
        try:
            cmd = self._build_command()
            self._execute(cmd)
        except Exception as e:
            self._fail(str(e))

    def cancel(self):
        """Terminate the underlying FFmpeg process if running."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self.job.status = JobStatus.CANCELLED

    # ------------------------------------------------------------------
    # Command building
    # ------------------------------------------------------------------

    def _build_command(self) -> list[str]:
        """
        Translate a VideoJob into an FFmpeg CLI argument list.
        Returns a list suitable for subprocess.Popen.
        """
        job = self.job
        cmd = ["ffmpeg", "-y", "-i", job.input_path]

        # --- Video filters (scale, fps, interpolation, upscale) ---
        vf_filters = []

        # Resolution / upscale
        target_w = job.upscale_width or job.target_width
        target_h = job.upscale_height or job.target_height
        if target_w and target_h:
            vf_filters.append(f"scale={target_w}:{target_h}:flags=lanczos")

        # FPS change
        if job.target_fps:
            vf_filters.append(f"fps={job.target_fps}")

        # Frame interpolation (2x minterpolate)
        from core.video_job import InterpolationMode
        if job.interpolation_mode == InterpolationMode.TWO_X:
            src_fps = job.source_metadata.fps if job.source_metadata else 30
            target = src_fps * 2
            vf_filters.append(
                f"minterpolate=fps={target}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
            )

        if vf_filters:
            cmd += ["-vf", ",".join(vf_filters)]

        # --- Codec ---
        if job.video_codec:
            cmd += ["-c:v", job.video_codec]
        else:
            cmd += ["-c:v", "libx264"]  # sensible default

        # --- CRF / Bitrate ---
        if job.crf is not None:
            cmd += ["-crf", str(job.crf)]
        elif job.bitrate_kbps:
            cmd += ["-b:v", f"{job.bitrate_kbps}k"]

        # --- Preset ---
        if job.preset:
            cmd += ["-preset", job.preset]

        # --- Audio ---
        if job.strip_audio:
            cmd += ["-an"]
        elif job.audio_codec:
            cmd += ["-c:a", job.audio_codec]
        else:
            cmd += ["-c:a", "copy"]

        # --- Progress reporting ---
        cmd += ["-progress", "pipe:1", "-nostats"]

        cmd.append(job.output_path)
        return cmd

    # ------------------------------------------------------------------
    # Execution & progress parsing
    # ------------------------------------------------------------------

    def _execute(self, cmd: list[str]):
        """
        Run FFmpeg and parse progress from stdout.

        stderr is drained on a background thread to prevent the OS pipe buffer
        (~64 KB) from filling up and deadlocking the process before stdout
        finishes. We collect stderr so we can report it on failure.
        """
        duration = self.job.source_metadata.duration if self.job.source_metadata else None

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Drain stderr in a daemon thread so it never blocks FFmpeg
        stderr_lines: list[str] = []

        def _drain_stderr():
            for line in self._process.stderr:
                stderr_lines.append(line)

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        # Read stdout (progress key=value pairs) on THIS thread
        for line in self._process.stdout:
            self._parse_progress_line(line.strip(), duration)

        self._process.wait()
        stderr_thread.join()  # Ensure all stderr has been collected

        if self._process.returncode == 0:
            self.job.status = JobStatus.DONE
            self.job.progress = 100.0
            self.progress.emit(100.0)
            self.job_complete.emit(self.job)
        else:
            stderr_output = "".join(stderr_lines)
            self._fail(stderr_output)

    def _parse_progress_line(self, line: str, duration: float | None):
        """
        Parse key=value lines from FFmpeg's -progress pipe output.
        Emits progress signal when out_time_ms is available.
        """
        if line.startswith("out_time_ms=") and duration:
            try:
                elapsed_ms = int(line.split("=")[1])
                elapsed_s = elapsed_ms / 1_000_000
                pct = min(100.0, (elapsed_s / duration) * 100)
                self.job.progress = pct
                self.progress.emit(pct)
            except ValueError:
                pass

    def _fail(self, message: str):
        self.job.status = JobStatus.FAILED
        self.job.error_message = message
        self.job_failed.emit(self.job, message)