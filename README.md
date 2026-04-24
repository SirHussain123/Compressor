# Compressor

Desktop video-processing app built with PyQt6 and FFmpeg.

## Bundled AI Tools

The app can use bundled external binaries for higher-quality enhancement, so
end users do not need to install them manually if you ship them with the app.

Place tools like this:

```text
Compressor/
  ai/
    rife/
      rife-ncnn-vulkan.exe
      *.bin
      *.param
    realesrgan/
      realesrgan-ncnn-vulkan.exe
      *.bin
      *.param
```

The app checks these local folders before falling back to the system `PATH`.
Legacy `tools/` lookups are still supported for older setups, but `ai/` is the
preferred bundled location.
