# Wind Desk video demo

The finished video is [demo/wind-desk-narrated-demo.mp4](demo/wind-desk-narrated-demo.mp4).

- Total: **8 minutes 19 seconds** (498.59 seconds measured in the rendered file).
- Part 1, customer pilot presentation: **00:00–03:32**, about 3 minutes 32 seconds.
- Part 2, technical review and handover: **03:32–08:19**, about 4 minutes 47 seconds.
- Format: 1920 × 1080, 24 fps, H.264 video, stereo AAC audio.
- Narration: synthetic English voice, Microsoft Zira Desktop.
- Captions: burned into the video, included as an English subtitle track, and supplied separately in [demo/captions.srt](demo/captions.srt).
- Chapters are embedded in the MP4. Suggested publishing text is in [demo/video-description.txt](demo/video-description.txt).
- The complete narration is in [demo/transcript.md](demo/transcript.md).

Part 1 uses the project's existing real portal screen recording and demonstrates decision dates, cutoffs, forecast versus actual generation, coverage, period-level evidence, CSV export, and methodology. The January 15, 10:00 example was checked against the current database: 24 matched periods, 48 actual periods, MAE 897.33 MW, bias +393.5 MW, and partial forecast energy 95,701 MWh. It explicitly avoids unsupported procurement or cost-saving claims.

Part 2 uses designed architecture visuals and current code excerpts. It covers React and DRF boundaries, the two Elexon endpoints, client/service/utils responsibilities, atomic ingestion, forecast vintage selection, metric definitions, frontend validation, retries and circuit protection, tests, and setup/deployment handover.

Verification for this artifact: 37 backend tests, six frontend tests, and Ruff lint passed. The final MP4 was fully decoded without playback errors; the audio track was checked for non-silence and clipping (mean -19.3 dB, peak -4.2 dB). Representative frames across both parts were visually inspected. Both parts are below five minutes and the complete film is below ten minutes. Caption timing is generated from narration segment lengths and is approximate within each segment.

This is a local video artifact; it has not been uploaded or published.

## Rebuild

`demo/storyboard.py` owns narration and visual direction. `demo/prepare.py` renders the visual plates and manifest using Pillow. Run `demo/narrate.ps1` in PowerShell 7 with the installed Microsoft Zira Desktop voice to create WAV narration, then run `demo/render.py` to assemble the film with the project's ffmpeg-static executable. The rendering script checks both part limits before encoding. Generated assets remain in `demo/assets/`.
