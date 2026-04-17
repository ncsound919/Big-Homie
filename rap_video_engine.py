"""
rap_video_engine.py — Big Homie Vertical: AI Rap Video Generation MaaS

Pipeline:
  1. LLM generates lyrics
  2. MiniMax / Google Lyria generates beat
  3. Bark TTS synthesizes vocal rap (local, free)
  4. MiniMax video_generate creates scene visuals per section
  5. FFmpeg stitches audio + video
  6. Output uploaded to Cloudflare R2, URL returned

Usage:
  from rap_video_engine import RapVideoEngine
  engine = RapVideoEngine()
  result = await engine.generate(theme="hustle and grind", style="trap", bars=16)
  print(result["video_url"])
"""

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(os.getenv("MEDIA_OUTPUT_DIR", "~/.big_homie/media_outputs")).expanduser()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RAP_STYLES = {
    "trap": {
        "beat_prompt": "hard trap beat, 808 bass, hi-hats, dark synths, 140 BPM",
        "vocal_tone": "deep, melodic trap rap delivery",
    },
    "boom_bap": {
        "beat_prompt": "classic boom bap hip hop, punchy snare, jazz samples, 90 BPM",
        "vocal_tone": "lyrical, rhythmic, East Coast delivery",
    },
    "drill": {
        "beat_prompt": "UK/Chicago drill beat, sliding 808s, dark melody, 140 BPM",
        "vocal_tone": "aggressive, rhythmic drill cadence",
    },
    "lo_fi_rap": {
        "beat_prompt": "lo-fi hip hop instrumental, dusty samples, vinyl crackle, 85 BPM",
        "vocal_tone": "calm, introspective rap delivery",
    },
    "afrobeats": {
        "beat_prompt": "afrobeats fusion, talking drums, melodic guitar, 100 BPM",
        "vocal_tone": "melodic, soulful afro rap",
    },
}

VISUAL_MOODS = {
    "trap": "cinematic nighttime city streets, neon lights, luxury cars, slow motion",
    "boom_bap": "black and white New York City borough scenes, graffiti, vintage aesthetic",
    "drill": "dark urban environment, dramatic lighting, fast cuts, moody atmosphere",
    "lo_fi_rap": "cozy studio apartment, warm lighting, rain on window, chill atmosphere",
    "afrobeats": "vibrant African cityscape, colorful fashion, golden hour lighting, energy",
}


@dataclass
class RapVideoResult:
    success: bool
    job_id: str
    theme: str
    style: str
    lyrics: str = ""
    beat_path: str = ""
    vocal_path: str = ""
    video_path: str = ""
    video_url: str = ""  # Cloudflare R2 URL if uploaded
    cost_usd: float = 0.0
    error: str = ""
    metadata: dict = field(default_factory=dict)


class RapVideoEngine:
    """
    Autonomous rap video generation pipeline.
    Integrates: LLM lyrics → MiniMax beat → Bark vocals → MiniMax video → FFmpeg stitch
    """

    def __init__(self):
        self.enabled = os.getenv("RAP_VIDEO_ENABLED", "true").lower() == "true"
        self.bark_enabled = os.getenv("BARK_ENABLED", "false").lower() == "true"
        self.bark_model_path = os.getenv("BARK_MODEL_PATH", "~/.big_homie/models/bark")
        self.r2_enabled = os.getenv("CF_R2_ENABLED", "false").lower() == "true"
        self.r2_bucket = os.getenv("CF_R2_BUCKET", "big-homie-media")
        self.ffmpeg_path = os.getenv("FFMPEG_PATH", "ffmpeg")

    async def generate(
        self,
        theme: str,
        style: str = "trap",
        bars: int = 16,
        include_vocals: bool = True,
        visual_clips: int = 4,
        custom_lyrics: Optional[str] = None,
    ) -> RapVideoResult:
        """
        Full rap video generation pipeline.

        Args:
            theme: Topic/subject of the rap (e.g. "hustle and grind", "AI taking over")
            style: Rap style key from RAP_STYLES dict
            bars: Number of lyric bars to generate
            include_vocals: Whether to synthesize vocals via Bark
            visual_clips: Number of video scene clips to generate
            custom_lyrics: Skip LLM lyrics generation and use provided text

        Returns:
            RapVideoResult with paths and URL
        """
        job_id = str(uuid.uuid4())[:8]
        style_data = RAP_STYLES.get(style, RAP_STYLES["trap"])
        total_cost = 0.0

        logger.info(f"[RapVideo:{job_id}] Starting generation — theme='{theme}' style='{style}'")

        try:
            # ── Step 1: Generate Lyrics ───────────────────────────────────────────
            if custom_lyrics:
                lyrics = custom_lyrics
                logger.info(
                    f"[RapVideo:{job_id}] Using custom lyrics ({len(lyrics.split())} words)"
                )
            else:
                lyrics = await self._generate_lyrics(theme, style, bars, style_data["vocal_tone"])
                logger.info(f"[RapVideo:{job_id}] Lyrics generated ({bars} bars)")

            # ── Step 2: Generate Beat ─────────────────────────────────────────────
            beat_path, beat_cost = await self._generate_beat(job_id, style_data["beat_prompt"])
            total_cost += beat_cost
            logger.info(f"[RapVideo:{job_id}] Beat generated: {beat_path}")

            # ── Step 3: Synthesize Vocals (optional) ──────────────────────────────
            vocal_path = ""
            if include_vocals and self.bark_enabled:
                vocal_path = await self._synthesize_vocals(job_id, lyrics)
                logger.info(f"[RapVideo:{job_id}] Vocals synthesized: {vocal_path}")
            elif include_vocals:
                logger.warning(f"[RapVideo:{job_id}] Bark not enabled — skipping vocal synthesis")

            # ── Step 4: Generate Visual Clips ─────────────────────────────────────
            visual_mood = VISUAL_MOODS.get(style, VISUAL_MOODS["trap"])
            clip_paths, clip_cost = await self._generate_visuals(
                job_id, theme, visual_mood, visual_clips
            )
            total_cost += clip_cost
            logger.info(f"[RapVideo:{job_id}] {len(clip_paths)} visual clips generated")

            # ── Step 5: Stitch with FFmpeg ────────────────────────────────────────
            video_path = await self._stitch_video(job_id, beat_path, vocal_path, clip_paths)
            logger.info(f"[RapVideo:{job_id}] Video stitched: {video_path}")

            # ── Step 6: Upload to R2 (optional) ───────────────────────────────────
            video_url = ""
            if self.r2_enabled and video_path:
                video_url = await self._upload_to_r2(job_id, video_path)
                logger.info(f"[RapVideo:{job_id}] Uploaded: {video_url}")

            return RapVideoResult(
                success=True,
                job_id=job_id,
                theme=theme,
                style=style,
                lyrics=lyrics,
                beat_path=beat_path,
                vocal_path=vocal_path,
                video_path=video_path,
                video_url=video_url,
                cost_usd=total_cost,
                metadata={"bars": bars, "clips": len(clip_paths), "style_config": style_data},
            )

        except Exception as e:
            logger.error(f"[RapVideo:{job_id}] Pipeline failed: {e}")
            return RapVideoResult(
                success=False, job_id=job_id, theme=theme, style=style, error=str(e)
            )

    # ─────────────────────────────────────────────────────────────────────────────
    # Private pipeline steps
    # ─────────────────────────────────────────────────────────────────────────────

    async def _generate_lyrics(self, theme: str, style: str, bars: int, vocal_tone: str) -> str:
        """Generate rap lyrics via LLM (routes through router.py)"""
        try:
            from llm_gateway import TaskType, llm

            prompt = f"""Write {bars} bars of original rap lyrics.

Theme: {theme}
Style: {style} — {vocal_tone}
Format: {bars} lines, rhyme scheme AABB or ABAB, no chorus/hook unless bars > 16.
Do NOT include section labels like [Verse] or [Hook].
Make it authentic, vivid, and specific. No generic filler lines."""

            response = await llm.complete(
                messages=[{"role": "user", "content": prompt}],
                task_type=TaskType.CREATIVE,
            )
            return response.content if hasattr(response, "content") else str(response)
        except ImportError:
            return f"Big Homie on the beat, {theme} is the theme, building an empire chasing the dream."

    async def _generate_beat(self, job_id: str, beat_prompt: str) -> tuple[str, float]:
        """Generate instrumental beat via media_generation.py (MiniMax or Google Lyria)"""
        try:
            from media_generation import MediaType, media_manager

            result = await media_manager.generate_media(
                media_type=MediaType.MUSIC,
                prompt=beat_prompt,
                provider="minimax",
            )
            cost = result.metadata.get("cost_usd", 0.02) if result.success else 0.0
            path = result.file_path if result.success else ""
            if not result.success:
                # Fallback to Google Lyria
                result = await media_manager.generate_media(
                    media_type=MediaType.MUSIC,
                    prompt=beat_prompt,
                    provider="google_lyria",
                )
                path = result.file_path if result.success else ""
                cost = result.metadata.get("cost_usd", 0.01) if result.success else 0.0
            return path, cost
        except Exception as e:
            logger.warning(f"[RapVideo:{job_id}] Beat generation failed: {e}")
            return "", 0.0

    async def _synthesize_vocals(self, job_id: str, lyrics: str) -> str:
        """Synthesize rap vocals via Bark TTS (local, free)"""
        try:
            import numpy as np
            import soundfile as sf
            from bark import SAMPLE_RATE, generate_audio, preload_models

            preload_models()
            # Split lyrics into chunks (Bark handles ~250 chars max cleanly)
            chunks = [lyrics[i : i + 200] for i in range(0, len(lyrics), 200)]
            audio_arrays = []
            for chunk in chunks:
                audio = generate_audio(f"[rap voice, rhythmic]{chunk}")
                audio_arrays.append(audio)

            combined = np.concatenate(audio_arrays)
            vocal_path = str(OUTPUT_DIR / f"vocal_{job_id}.wav")
            sf.write(vocal_path, combined, SAMPLE_RATE)
            return vocal_path
        except ImportError:
            logger.warning(f"[RapVideo:{job_id}] Bark not installed. Install: pip install bark")
            return ""
        except Exception as e:
            logger.warning(f"[RapVideo:{job_id}] Bark synthesis failed: {e}")
            return ""

    async def _generate_visuals(
        self, job_id: str, theme: str, visual_mood: str, count: int
    ) -> tuple[list, float]:
        """Generate video scene clips in parallel via MiniMax"""
        try:
            from media_generation import MediaType, media_manager

            prompts = [
                f"Cinematic rap video scene {i + 1} of {count}: {theme}. Visual style: {visual_mood}. "
                f"Smooth camera movement, professional cinematography, 5 seconds."
                for i in range(count)
            ]

            # Generate in parallel
            tasks = [
                media_manager.generate_media(
                    media_type=MediaType.VIDEO,
                    prompt=p,
                    provider="minimax",
                    duration=5,
                    width=1920,
                    height=1080,
                )
                for p in prompts
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            clip_paths = []
            total_cost = 0.0
            for r in results:
                if isinstance(r, Exception):
                    logger.warning(f"[RapVideo:{job_id}] Clip generation error: {r}")
                    continue
                if r.success:
                    clip_paths.append(r.file_path)
                    total_cost += r.metadata.get("cost_usd", 0.05)

            return clip_paths, total_cost
        except Exception as e:
            logger.warning(f"[RapVideo:{job_id}] Visual generation failed: {e}")
            return [], 0.0

    async def _stitch_video(
        self, job_id: str, beat_path: str, vocal_path: str, clip_paths: list
    ) -> str:
        """Stitch clips + audio with FFmpeg via persistent_shell.py"""
        if not clip_paths:
            logger.warning(f"[RapVideo:{job_id}] No clips to stitch")
            return ""
        try:
            from persistent_shell import shell

            output_path = str(OUTPUT_DIR / f"rap_video_{job_id}.mp4")

            # Build FFmpeg concat file
            concat_file = str(OUTPUT_DIR / f"concat_{job_id}.txt")
            with open(concat_file, "w") as f:
                for clip in clip_paths:
                    f.write(f"file '{clip}'\n")

            # Determine audio: prefer mixed vocals+beat, fallback to beat only
            if vocal_path and beat_path:
                audio_filter = '-filter_complex "[0:a][1:a]amix=inputs=2:duration=longest" '
                audio_input = f'-i "{beat_path}" -i "{vocal_path}" '
            elif beat_path:
                audio_input = f'-i "{beat_path}" '
                audio_filter = ""
            else:
                audio_input = ""
                audio_filter = ""

            cmd = (
                f"{self.ffmpeg_path} -y "
                f'-f concat -safe 0 -i "{concat_file}" '
                f"{audio_input}"
                f"{audio_filter}"
                f"-c:v libx264 -c:a aac -shortest "
                f'"{output_path}"'
            )
            result = await shell.run(cmd)
            if result and os.path.exists(output_path):
                return output_path
            else:
                logger.warning(f"[RapVideo:{job_id}] FFmpeg did not produce output")
                return ""
        except Exception as e:
            logger.warning(f"[RapVideo:{job_id}] Stitch failed: {e}")
            return ""

    async def _upload_to_r2(self, job_id: str, file_path: str) -> str:
        """Upload finished video to Cloudflare R2 and return public URL"""
        try:
            import boto3

            s3 = boto3.client(
                "s3",
                endpoint_url=f"https://{os.getenv('CF_ACCOUNT_ID')}.r2.cloudflarestorage.com",
                aws_access_key_id=os.getenv("CF_R2_ACCESS_KEY"),
                aws_secret_access_key=os.getenv("CF_R2_SECRET_KEY"),
            )
            key = f"rap_videos/{job_id}/{Path(file_path).name}"
            s3.upload_file(file_path, self.r2_bucket, key)
            public_url = f"https://pub-{os.getenv('CF_R2_PUBLIC_ID', 'xxx')}.r2.dev/{key}"
            return public_url
        except Exception as e:
            logger.warning(f"[RapVideo:{job_id}] R2 upload failed: {e}")
            return f"file://{file_path}"


# ─────────────────────────────────────────────────────────────────────────────
# Convenience function for direct use
# ─────────────────────────────────────────────────────────────────────────────

_engine = RapVideoEngine()


async def generate_rap_video(
    theme: str,
    style: str = "trap",
    bars: int = 16,
    include_vocals: bool = True,
    visual_clips: int = 4,
    custom_lyrics: Optional[str] = None,
) -> RapVideoResult:
    """Top-level convenience wrapper. Import and call directly."""
    return await _engine.generate(
        theme=theme,
        style=style,
        bars=bars,
        include_vocals=include_vocals,
        visual_clips=visual_clips,
        custom_lyrics=custom_lyrics,
    )
