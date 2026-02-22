"""
interpolation.py
----------------
Frame interpolation logic.
Currently supports 2x FFmpeg minterpolate. Structured for RIFE integration later.
"""


from core.video_job import VideoJob, InterpolationMode


class InterpolationEngine:
    """
    Configures a VideoJob for frame interpolation.
    The actual FFmpeg filter string is built inside ffmpeg_worker.py.
    This class sets the job parameters and validates feasibility.
    """

    def apply_2x(self, job: VideoJob):
        """
        Configure a job for 2x frame interpolation using FFmpeg's minterpolate.
        The output FPS will be double the source FPS.

        Args:
            job: Must have source_metadata populated before calling.
        """
        if not job.source_metadata:
            raise ValueError("source_metadata must be set before applying interpolation.")

        job.interpolation_mode = InterpolationMode.TWO_X

    def disable(self, job: VideoJob):
        """Remove interpolation from a job."""
        job.interpolation_mode = InterpolationMode.NONE

    def estimated_output_fps(self, job: VideoJob) -> float | None:
        """
        Return the expected output FPS after interpolation, or None if not applicable.
        """
        if not job.source_metadata:
            return None

        if job.interpolation_mode == InterpolationMode.TWO_X:
            return job.source_metadata.fps * 2

        return job.source_metadata.fps

    # ------------------------------------------------------------------
    # Future: RIFE integration stub
    # ------------------------------------------------------------------

    def apply_rife(self, job: VideoJob):
        """
        Placeholder for RIFE neural frame interpolation.
        Will require RIFE to be installed as an external tool.
        """
        raise NotImplementedError("RIFE integration is planned for a future release.")