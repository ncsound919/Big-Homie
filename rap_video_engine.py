"""rap_video_engine.py — Big Homie Rap Video MaaS Vertical
Full pipeline: lyrics → beat → vocal synth → video scenes → FFmpeg render
Revenue stream: RevenueStream.MAAS  ($49/video one-shot)
"""
from __future__ import annotations
import asyncio, json, uuid, os, shutil, tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger


class RapStyle(str, Enum):
    TRAP       = "trap"
    BOOM_BAP   = "boom_bap"
    DRILL      = "drill"
    LO_FI      = "lo_fi"
    PHONK      = "phonk"


@dataclass
class RapVideoJob:
    id: str
    theme: str
    style: RapStyle
    bars: int
    artist_name: str
    include_vocals: bool
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    lyrics: Optional[str] = None
    beat_path: Optional[str] = None
    vocals_path: Optional[str] = None
    video_scenes: List[str] = field(default_factory=list)
    output_path: Optional[str] = None
    cost_usd: float = 0.0
    error: Optional[str] = None
    stages_completed: List[str] = field(default_factory=list)


# ── Style → production prompts ────────────────────────────────────────────
STYLE_PROMPTS = {
    RapStyle.TRAP:     "heavy 808s, hi-hat rolls, dark minor key, 140 BPM trap beat",
    RapStyle.BOOM_BAP: "classic boom bap, vinyl samples, heavy kick and snare, 90 BPM",
    RapStyle.DRILL:    "UK/Chicago drill, sliding 808s, dark melody, 140 BPM, minor pentatonic",
    RapStyle.LO_FI:    "lo-fi hip hop, warm vinyl crackle, jazzy chords, 85 BPM, chill",
    RapStyle.PHONK:    "phonk beat, cowbell, distorted 808, Memphis rap influence, 130 BPM",
}

VISUAL_STYLES = {
    RapStyle.TRAP:     "dark urban night, neon lights, slow motion, cinematic",
    RapStyle.BOOM_BAP: "black and white New York streets, graffiti, film grain",
    RapStyle.DRILL:    "grey concrete, hoodie silhouettes, dramatic lighting",
    RapStyle.LO_FI:    "warm anime aesthetic, rain on windows, cozy studio",
    RapStyle.PHONK:    "retro Memphis underground, VHS aesthetic, dim lighting",
}


class RapVideoEngine:
    OUTPUT_DIR = Path.home() / ".big_homie" / "rap_video_outputs"
    TEMP_DIR   = Path.home() / ".big_homie" / "rap_video_temp"

    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # ── LLM helper ─────────────────────────────────────────────────────
    async def _llm(self, prompt: str, tier: str = "complex") -> str:
        try:
            from llm_gateway import llm, TaskType
            tier_map = {"fast": TaskType.SIMPLE, "general": TaskType.GENERAL, "complex": TaskType.COMPLEX}
            resp = await llm.complete(
                messages=[{"role": "user", "content": prompt}],
                task_type=tier_map.get(tier, TaskType.COMPLEX),
            )
            return resp.content if hasattr(resp, "content") else str(resp)
        except ImportError:
            await asyncio.sleep(0.05)
            return f"[STUB LYRICS for: {prompt[:80]}]"

    # ── Stage 1: Lyrics ────────────────────────────────────────────────
    async def _gen_lyrics(self, theme: str, style: RapStyle,
                           bars: int, artist_name: str) -> str:
        prompt = f"""You are a professional rap lyricist. Write {bars} bars of rap lyrics.

THEME: {theme}
STYLE: {style.value} — {STYLE_PROMPTS[style]}
ARTIST NAME: {artist_name}

STRUCTURE:
- 4-bar intro (hype line)
- 16-bar verse 1
- 8-bar hook/chorus (catchy, repeatable)
- 16-bar verse 2
- 8-bar hook/chorus (repeat)
- 4-bar outro

RULES:
- Raw, authentic lyrics matching the {style.value} style
- Strong internal rhyme schemes
- Metaphors related to the theme
- Mark sections: [INTRO] [VERSE 1] [HOOK] [VERSE 2] [HOOK] [OUTRO]
- Include BPM annotation at top: BPM: [number]

WRITE THE FULL LYRICS NOW:"""
        return await self._llm(prompt, "complex")

    # ── Stage 2: Beat generation ────────────────────────────────────────
    async def _gen_beat(self, job_id: str, style: RapStyle) -> Optional[str]:
        beat_path = self.TEMP_DIR / f"beat_{job_id}.mp3"

        # Try MiniMax Music API
        try:
            from media_generation import media_manager, MediaType
            result = await media_manager.generate_media(
                media_type=MediaType.MUSIC,
                prompt=f"{STYLE_PROMPTS[style]}, instrumental only, no vocals",
                provider="minimax",
                duration=90,
            )
            if result.success and result.file_path:
                shutil.copy(result.file_path, beat_path)
                logger.info(f"[RapVideo] Beat generated via MiniMax -> {beat_path}")
                return str(beat_path)
        except (ImportError, Exception) as e:
            logger.warning(f"[RapVideo] MiniMax beat failed: {e}")

        # Try Google Lyria (Gemini music)
        if os.getenv("GOOGLE_LYRIA_ENABLED", "false").lower() == "true":
            try:
                from media_generation import media_manager, MediaType
                result = await media_manager.generate_media(
                    media_type=MediaType.MUSIC,
                    prompt=f"{STYLE_PROMPTS[style]}, instrumental",
                    provider="lyria",
                )
                if result.success and result.file_path:
                    shutil.copy(result.file_path, beat_path)
                    return str(beat_path)
            except (ImportError, Exception) as e:
                logger.warning(f"[RapVideo] Lyria beat failed: {e}")

        logger.warning("[RapVideo] No beat generator available — skipping beat stage")
        return None

    # ── Stage 3: Vocal synthesis ────────────────────────────────────────
    async def _gen_vocals(self, job_id: str, lyrics: str,
                           style: RapStyle) -> Optional[str]:
        vocals_path = self.TEMP_DIR / f"vocals_{job_id}.mp3"
        clean_lyrics = "\n".join(
            line for line in lyrics.splitlines()
            if not line.startswith("[") and line.strip()
        )[:1000]

        # Try ElevenLabs
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
        if elevenlabs_key:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(
                        "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB",
                        headers={"xi-api-key": elevenlabs_key, "Content-Type": "application/json"},
                        json={
                            "text": clean_lyrics,
                            "model_id": "eleven_turbo_v2",
                            "voice_settings": {"stability": 0.4, "similarity_boost": 0.7},
                        },
                    )
                    if resp.status_code == 200:
                        vocals_path.write_bytes(resp.content)
                        logger.info(f"[RapVideo] Vocals via ElevenLabs -> {vocals_path}")
                        return str(vocals_path)
            except Exception as e:
                logger.warning(f"[RapVideo] ElevenLabs failed: {e}")

        # Try local Bark TTS
        bark_path = os.getenv("BARK_MODEL_PATH", "")
        if bark_path or os.getenv("BARK_ENABLED", "false").lower() == "true":
            try:
                from bark import generate_audio, SAMPLE_RATE  # type: ignore
                import scipy.io.wavfile as wav  # type: ignore
                import numpy as np

                audio = generate_audio(clean_lyrics[:500])
                wav_path = self.TEMP_DIR / f"vocals_{job_id}.wav"
                wav.write(str(wav_path), SAMPLE_RATE, audio)
                # Convert wav -> mp3 via ffmpeg
                ret = await asyncio.create_subprocess_exec(
                    "ffmpeg", "-y", "-i", str(wav_path), str(vocals_path),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await ret.wait()
                logger.info(f"[RapVideo] Vocals via Bark -> {vocals_path}")
                return str(vocals_path)
            except Exception as e:
                logger.warning(f"[RapVideo] Bark failed: {e}")

        logger.warning("[RapVideo] No vocal synthesizer available — skipping vocals stage")
        return None

    # ── Stage 4: Video scene generation ────────────────────────────────
    async def _gen_scenes(self, job_id: str, theme: str,
                           style: RapStyle, count: int = 5) -> List[str]:
        visual = VISUAL_STYLES[style]
        scene_paths = []

        try:
            from media_generation import media_manager, MediaType
            tasks = [
                media_manager.generate_media(
                    media_type=MediaType.VIDEO,
                    prompt=f"{visual}, {theme}, scene {i+1} of {count}, cinematic music video",
                    provider="minimax",
                    duration=5,
                )
                for i in range(count)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if not isinstance(result, Exception) and result.success and result.file_path:
                    dest = self.TEMP_DIR / f"scene_{job_id}_{i:02d}.mp4"
                    shutil.copy(result.file_path, dest)
                    scene_paths.append(str(dest))
        except (ImportError, Exception) as e:
            logger.warning(f"[RapVideo] Scene gen failed: {e}")

        return scene_paths

    # ── Stage 5: FFmpeg render ──────────────────────────────────────────
    async def _render_video(
        self, job_id: str, scene_paths: List[str],
        beat_path: Optional[str], vocals_path: Optional[str],
    ) -> Optional[str]:
        if not scene_paths and not beat_path:
            logger.warning("[RapVideo] No scenes or beat — cannot render")
            return None

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            logger.error("[RapVideo] ffmpeg not found — install with: sudo apt install ffmpeg")
            return None

        output_path = self.OUTPUT_DIR / f"rap_video_{job_id}.mp4"

        try:
            if scene_paths:
                # Concatenate scenes
                concat_list = self.TEMP_DIR / f"concat_{job_id}.txt"
                concat_list.write_text("\n".join(f"file '{p}'" for p in scene_paths))
                silent_video = self.TEMP_DIR / f"silent_{job_id}.mp4"
                proc = await asyncio.create_subprocess_exec(
                    ffmpeg, "-y", "-f", "concat", "-safe", "0",
                    "-i", str(concat_list), "-c", "copy", str(silent_video),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
                video_source = str(silent_video)
            else:
                # No scenes: create black video
                video_source = None

            # Mix audio
            if beat_path and vocals_path:
                mixed_audio = self.TEMP_DIR / f"mixed_{job_id}.mp3"
                proc = await asyncio.create_subprocess_exec(
                    ffmpeg, "-y",
                    "-i", beat_path, "-i", vocals_path,
                    "-filter_complex", "[0:a]volume=0.7[a0];[1:a]volume=1.2[a1];[a0][a1]amix=inputs=2[aout]",
                    "-map", "[aout]", str(mixed_audio),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
                audio_source = str(mixed_audio)
            elif beat_path:
                audio_source = beat_path
            elif vocals_path:
                audio_source = vocals_path
            else:
                audio_source = None

            # Final combine
            cmd = [ffmpeg, "-y"]
            if video_source:
                cmd += ["-i", video_source]
            else:
                cmd += ["-f", "lavfi", "-i", "color=c=black:s=1280x720:r=30"]
            if audio_source:
                cmd += ["-i", audio_source, "-c:a", "aac", "-b:a", "192k"]
            cmd += ["-c:v", "libx264", "-preset", "fast", "-t", "90",
                    "-pix_fmt", "yuv420p", str(output_path)]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()

            if output_path.exists():
                logger.success(f"[RapVideo] Rendered -> {output_path}")
                return str(output_path)

        except Exception as e:
            logger.error(f"[RapVideo] Render failed: {e}")

        return None

    # ── Main pipeline ──────────────────────────────────────────────────
    async def generate_rap_video(
        self,
        theme: str,
        style: str = "trap",
        bars: int = 16,
        artist_name: str = "Big Homie",
        include_vocals: bool = True,
    ) -> RapVideoJob:
        job = RapVideoJob(
            id=uuid.uuid4().hex[:8],
            theme=theme,
            style=RapStyle(style),
            bars=bars,
            artist_name=artist_name,
            include_vocals=include_vocals,
            status="running",
        )
        logger.info(f"[RapVideo] Starting job={job.id} theme='{theme}' style={style}")

        try:
            # Stage 1: Lyrics
            logger.info("[RapVideo] Stage 1/5 — generating lyrics")
            job.lyrics = await self._gen_lyrics(theme, job.style, bars, artist_name)
            job.stages_completed.append("lyrics")
            job.cost_usd += 0.02

            # Stages 2-4: Beat, Vocals, Scenes (parallel)
            logger.info("[RapVideo] Stages 2-4 — beat + vocals + scenes (parallel)")
            beat_task   = self._gen_beat(job.id, job.style)
            vocals_task = self._gen_vocals(job.id, job.lyrics, job.style) if include_vocals else asyncio.sleep(0)
            scenes_task = self._gen_scenes(job.id, theme, job.style)

            beat_result, vocals_result, scenes_result = await asyncio.gather(
                beat_task, vocals_task, scenes_task, return_exceptions=True
            )

            job.beat_path    = beat_result   if not isinstance(beat_result, Exception)   else None
            job.vocals_path  = vocals_result if not isinstance(vocals_result, Exception) else None
            job.video_scenes = scenes_result if not isinstance(scenes_result, Exception) else []
            job.stages_completed.extend(["beat", "vocals", "scenes"])
            job.cost_usd += 0.10

            # Stage 5: Render
            logger.info("[RapVideo] Stage 5/5 — FFmpeg render")
            job.output_path = await self._render_video(
                job.id, job.video_scenes, job.beat_path, job.vocals_path,
            )
            job.stages_completed.append("render")
            job.cost_usd += 0.01

            job.status   = "completed"
            job.cost_usd = round(job.cost_usd, 4)
            self._save(job)
            logger.success(
                f"[RapVideo] job={job.id} done | "
                f"output={job.output_path} | cost=${job.cost_usd:.4f}"
            )

        except Exception as e:
            job.status = "failed"
            job.error  = str(e)
            logger.error(f"[RapVideo] job={job.id} FAILED: {e}")
            self._save(job)

        return job

    # ── Persistence ────────────────────────────────────────────────────
    def _save(self, job: RapVideoJob) -> Path:
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.OUTPUT_DIR / f"rap_job_{ts}_{job.id}.json"
        path.write_text(json.dumps({
            "id": job.id, "created_at": job.created_at,
            "status": job.status,
            "theme": job.theme, "style": job.style.value,
            "bars": job.bars, "artist_name": job.artist_name,
            "lyrics_preview": (job.lyrics or "")[:300],
            "beat_path": job.beat_path,
            "vocals_path": job.vocals_path,
            "scene_count": len(job.video_scenes),
            "output_path": job.output_path,
            "cost_usd": job.cost_usd,
            "error": job.error,
            "stages_completed": job.stages_completed,
        }, indent=2))
        return path

    def list_jobs(self, limit: int = 20) -> List[Dict]:
        files = sorted(self.OUTPUT_DIR.glob("rap_job_*.json"), reverse=True)[:limit]
        return [json.loads(f.read_text()) for f in files]

    # ── Revenue hook ────────────────────────────────────────────────────
    async def bill_video(self, job: RapVideoJob, price_usd: float = 49.0):
        try:
            from revenue_engine import RevenueEngine, RevenueTask, RevenueStream, RiskLevel
            engine = RevenueEngine()
            task   = RevenueTask(
                id=job.id,
                stream=RevenueStream.MAAS,
                description=f"Rap video: {job.theme[:60]} ({job.style.value})",
                goal_usd=price_usd,
                risk=RiskLevel.LOW,
                status="completed",
                revenue_usd=price_usd,
                cost_usd=job.cost_usd,
            )
            task.completed_at = datetime.now()
            engine.tasks[task.id] = task
            logger.success(f"[RapVideo] billed ${price_usd:.2f} for job {job.id}")
        except ImportError:
            pass


# ── Singleton ─────────────────────────────────────────────────────────────
rap_video_engine = RapVideoEngine()


# ── GSD router entry point ────────────────────────────────────────────────
async def handle_rap_request(task_text: str) -> Dict:
    """Called by gsd_router when context is @rap."""
    # Extract style hint from task text
    style = "trap"
    for s in ["trap", "boom_bap", "drill", "lo_fi", "phonk"]:
        if s.replace("_", " ") in task_text.lower() or s in task_text.lower():
            style = s
            break
    job = await rap_video_engine.generate_rap_video(
        theme=task_text,
        style=style,
        bars=16,
        artist_name="Big Homie",
    )
    return {
        "job_id":      job.id,
        "status":      job.status,
        "output_path": job.output_path,
        "cost_usd":    job.cost_usd,
    }


# ── Quick test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    async def _run():
        theme = " ".join(sys.argv[1:]) or "building an empire from nothing, hustle and grind"
        print(f"\n Generating rap video for: '{theme}'\n")
        job = await rap_video_engine.generate_rap_video(
            theme=theme, style="trap", bars=16, artist_name="Big Homie",
        )
        print(f"\nJob {job.id} | status={job.status} | cost=${job.cost_usd:.4f}")
        print(f"Output: {job.output_path or 'not rendered (set media API keys)'}")
        if job.lyrics:
            print(f"\nLyrics preview:\n{job.lyrics[:400]}...")
    asyncio.run(_run())
