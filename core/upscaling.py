"""
upscaling.py
------------
Upscaling logic for video jobs.
Currently supports FFmpeg Lanczos scaling. Structured for Real-ESRGAN later.
"""


from core.video_job import VideoJob, UpscaleMode


# Common upscale target presets
UPSCALE_PRESETS = {
    "720p":  (1280, 720),
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4K":    (3840, 2160),
}


class UpscalingEngine:
    """
    Configures a VideoJob for upscaling.
    Actual filter strings are built in ffmpeg_worker.py.
    """

    def apply_lanczos(self, job: VideoJob, width: int, height: int):
        """
        Configure a job for high-quality Lanczos upscaling via FFmpeg.

        Args:
            job:    The VideoJob to configure.
            width:  Target width in pixels.
            height: Target height in pixels.
        """
        job.upscale_mode = UpscaleMode.LANCZOS
        job.upscale_width = width
        job.upscale_height = height

    def apply_preset(self, job: VideoJob, preset_name: str):
        """
        Apply a named resolution preset (e.g. "1080p", "4K").

        Args:
            preset_name: Key from UPSCALE_PRESETS.

        Raises:
            KeyError: If the preset name is not recognised.
        """
        if preset_name not in UPSCALE_PRESETS:
            raise KeyError(f"Unknown preset '{preset_name}'. "
                           f"Available: {list(UPSCALE_PRESETS.keys())}")
        w, h = UPSCALE_PRESETS[preset_name]
        self.apply_lanczos(job, w, h)

    def disable(self, job: VideoJob):
        """Remove upscaling from a job."""
        job.upscale_mode = UpscaleMode.NONE
        job.upscale_width = None
        job.upscale_height = None

    # ------------------------------------------------------------------
    # Future: Real-ESRGAN stub
    # ------------------------------------------------------------------

    def apply_realesrgan(self, job: VideoJob, scale: int = 4):
        """
        Placeholder for Real-ESRGAN AI upscaling.
        Requires Real-ESRGAN to be installed as an external binary.
        """
        raise NotImplementedError("Real-ESRGAN integration is planned for a future release.")

    @staticmethod
    def is_realesrgan_available() -> bool:
        """Check whether the Real-ESRGAN binary is accessible on PATH."""
        import shutil
        return shutil.which("realesrgan-ncnn-vulkan") is not None