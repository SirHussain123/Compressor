"""
job_queue.py
------------
Manages a list of VideoJobs and drives their sequential execution.
Emits Qt signals so the UI can react to queue state changes.
"""


from PyQt6.QtCore import QObject, pyqtSignal
from core.video_job import VideoJob, JobStatus
from core.ffmpeg_worker import FFmpegWorker


class JobQueue(QObject):
    """
    Maintains an ordered list of VideoJobs and runs them one at a time.

    Signals:
        job_started(VideoJob):          A job has begun processing.
        job_progress(VideoJob, float):  Progress update (0–100).
        job_finished(VideoJob):         A job completed successfully.
        job_failed(VideoJob, str):      A job failed with an error message.
        queue_empty():                  All jobs have been processed.
    """

    job_started  = pyqtSignal(object)
    job_progress = pyqtSignal(object, float)
    job_finished = pyqtSignal(object)
    job_failed   = pyqtSignal(object, str)
    queue_empty  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._jobs: list[VideoJob] = []
        self._current_worker: FFmpegWorker | None = None
        self._running = False

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------

    def add_job(self, job: VideoJob):
        """Append a job to the queue."""
        self._jobs.append(job)

    def remove_job(self, job: VideoJob):
        """Remove a pending job. Cannot remove a running job."""
        if job in self._jobs and job.status != JobStatus.RUNNING:
            self._jobs.remove(job)

    def clear_finished(self):
        """Remove all completed or failed jobs from the list."""
        self._jobs = [j for j in self._jobs if j.status in (JobStatus.PENDING, JobStatus.RUNNING)]

    def jobs(self) -> list[VideoJob]:
        return list(self._jobs)

    # ------------------------------------------------------------------
    # Execution control
    # ------------------------------------------------------------------

    def start(self):
        """Begin processing pending jobs sequentially."""
        if not self._running:
            self._running = True
            self._process_next()

    def stop(self):
        """Stop the queue after the current job finishes."""
        self._running = False

    def cancel_current(self):
        """Cancel the currently running job."""
        if self._current_worker:
            self._current_worker.cancel()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _process_next(self):
        """Find and start the next pending job, or emit queue_empty."""
        if not self._running:
            return

        next_job = next(
            (j for j in self._jobs if j.status == JobStatus.PENDING), None
        )

        if next_job is None:
            self._running = False
            self.queue_empty.emit()
            return

        worker = FFmpegWorker(next_job)
        worker.progress.connect(lambda pct: self.job_progress.emit(next_job, pct))
        worker.job_complete.connect(self._on_job_complete)
        worker.job_failed.connect(self._on_job_failed)

        self._current_worker = worker
        self.job_started.emit(next_job)
        worker.start()

    def _on_job_complete(self, job: VideoJob):
        self.job_finished.emit(job)
        self._current_worker = None
        self._process_next()

    def _on_job_failed(self, job: VideoJob, error: str):
        self.job_failed.emit(job, error)
        self._current_worker = None
        self._process_next()