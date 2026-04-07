"""
Media Generation Module for Big Homie
Supports video, music, and image generation through multiple providers
"""
import asyncio
import copy
import uuid
import httpx
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
from loguru import logger
from config import settings

class MediaType(str, Enum):
    """Types of media that can be generated"""
    IMAGE = "image"
    VIDEO = "video"
    MUSIC = "music"
    AUDIO = "audio"

class TaskStatus(str, Enum):
    """Status of async media generation tasks"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class MediaGenerationRequest:
    """Request for media generation"""
    media_type: MediaType
    prompt: str
    provider: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    reference_image: Optional[str] = None  # Path to reference image
    task_id: Optional[str] = None

@dataclass
class MediaGenerationResult:
    """Result of media generation"""
    success: bool
    media_type: MediaType
    file_path: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    task_id: Optional[str] = None
    status: TaskStatus = TaskStatus.COMPLETED

class MediaProvider(ABC):
    """Base class for media generation providers"""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.supported_media_types: List[MediaType] = []

    @abstractmethod
    async def generate(self, request: MediaGenerationRequest) -> MediaGenerationResult:
        """Generate media based on request"""
        pass

    def supports_media_type(self, media_type: MediaType) -> bool:
        """Check if provider supports media type"""
        return media_type in self.supported_media_types

    def _filter_unsupported_params(
        self,
        params: Dict[str, Any],
        supported_params: List[str]
    ) -> Dict[str, Any]:
        """Filter out unsupported parameters with warnings instead of failing"""
        filtered = {}
        for key, value in params.items():
            if key in supported_params:
                filtered[key] = value
            else:
                logger.warning(
                    f"{self.provider_name}: Ignoring unsupported parameter '{key}' "
                    f"(value: {value})"
                )
        return filtered

    def _save_media_file(self, content: bytes, extension: str, media_type: MediaType) -> str:
        """Save media content to file and return path"""
        output_dir = Path(settings.media_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{media_type.value}_{timestamp}_{uuid.uuid4().hex[:8]}.{extension}"
        file_path = output_dir / filename

        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"Saved {media_type.value} to {file_path}")
        return str(file_path)


class GoogleLyriaProvider(MediaProvider):
    """Google Lyria music generation provider"""

    def __init__(self):
        super().__init__("Google Lyria")
        self.supported_media_types = [MediaType.MUSIC, MediaType.AUDIO]
        self.api_key = settings.google_lyria_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate(self, request: MediaGenerationRequest) -> MediaGenerationResult:
        """Generate music using Google Lyria"""
        if not settings.google_lyria_enabled or not self.api_key:
            return MediaGenerationResult(
                success=False,
                media_type=request.media_type,
                error="Google Lyria is not enabled or API key not configured"
            )

        try:
            # Filter parameters - Lyria doesn't support durationSeconds and other optional hints
            supported_params = ["prompt", "temperature", "topK", "topP"]
            filtered_params = self._filter_unsupported_params(
                request.parameters,
                supported_params
            )

            async with httpx.AsyncClient(timeout=settings.max_media_generation_time) as client:
                response = await client.post(
                    f"{self.base_url}/models/lyria:generateMusic",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": request.prompt,
                        **filtered_params
                    }
                )

                response.raise_for_status()
                data = response.json()

                # Download generated audio
                if "audioUrl" in data:
                    audio_response = await client.get(data["audioUrl"])
                    audio_response.raise_for_status()
                    file_path = self._save_media_file(
                        audio_response.content,
                        "mp3",
                        MediaType.MUSIC
                    )

                    return MediaGenerationResult(
                        success=True,
                        media_type=MediaType.MUSIC,
                        file_path=file_path,
                        url=data.get("audioUrl"),
                        metadata={
                            "provider": self.provider_name,
                            "prompt": request.prompt,
                            "duration": data.get("duration")
                        }
                    )
                else:
                    return MediaGenerationResult(
                        success=False,
                        media_type=request.media_type,
                        error="No audio URL in response"
                    )

        except httpx.HTTPStatusError as e:
            logger.error(f"Google Lyria API error: {e.response.status_code} - {e.response.text}")
            return MediaGenerationResult(
                success=False,
                media_type=request.media_type,
                error=f"API error: {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"Google Lyria generation failed: {e}")
            return MediaGenerationResult(
                success=False,
                media_type=request.media_type,
                error=str(e)
            )


class MiniMaxProvider(MediaProvider):
    """MiniMax music and video generation provider"""

    def __init__(self):
        super().__init__("MiniMax")
        self.supported_media_types = [MediaType.MUSIC, MediaType.VIDEO, MediaType.AUDIO]
        self.api_key = settings.minimax_api_key
        self.group_id = settings.minimax_group_id
        self.base_url = "https://api.minimax.chat/v1"
        self.tasks: Dict[str, Dict] = {}  # Track async tasks

    async def generate(self, request: MediaGenerationRequest) -> MediaGenerationResult:
        """Generate media using MiniMax"""
        if not settings.minimax_enabled or not self.api_key:
            return MediaGenerationResult(
                success=False,
                media_type=request.media_type,
                error="MiniMax is not enabled or API key not configured"
            )

        try:
            task_id = request.task_id or str(uuid.uuid4())

            if request.media_type == MediaType.MUSIC:
                endpoint = "music/generation"
            elif request.media_type == MediaType.VIDEO:
                endpoint = "video/generation"
            else:
                return MediaGenerationResult(
                    success=False,
                    media_type=request.media_type,
                    error=f"Unsupported media type: {request.media_type}"
                )

            # Submit generation request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/{endpoint}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "group_id": self.group_id,
                        "prompt": request.prompt,
                        **request.parameters
                    }
                )

                response.raise_for_status()
                data = response.json()

                # MiniMax returns async task ID
                if "task_id" in data:
                    self.tasks[task_id] = {
                        "provider_task_id": data["task_id"],
                        "status": TaskStatus.PROCESSING,
                        "media_type": request.media_type,
                        "submitted_at": datetime.now().isoformat()
                    }

                    # If async tracking is enabled, poll for completion
                    if settings.enable_async_media_tasks:
                        result = await self._poll_task_completion(
                            task_id,
                            data["task_id"],
                            request.media_type
                        )
                        return result
                    else:
                        # Return pending result
                        return MediaGenerationResult(
                            success=True,
                            media_type=request.media_type,
                            task_id=task_id,
                            status=TaskStatus.PROCESSING,
                            metadata={
                                "provider": self.provider_name,
                                "provider_task_id": data["task_id"],
                                "message": "Task submitted, check status later"
                            }
                        )

        except httpx.HTTPStatusError as e:
            logger.error(f"MiniMax API error: {e.response.status_code} - {e.response.text}")
            return MediaGenerationResult(
                success=False,
                media_type=request.media_type,
                error=f"API error: {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"MiniMax generation failed: {e}")
            return MediaGenerationResult(
                success=False,
                media_type=request.media_type,
                error=str(e)
            )

    async def _poll_task_completion(
        self,
        task_id: str,
        provider_task_id: str,
        media_type: MediaType,
        max_polls: int = 60,
        poll_interval: int = 5
    ) -> MediaGenerationResult:
        """Poll MiniMax API for task completion"""
        async with httpx.AsyncClient() as client:
            for _ in range(max_polls):
                try:
                    response = await client.get(
                        f"{self.base_url}/query/status",
                        params={"task_id": provider_task_id},
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )

                    response.raise_for_status()
                    data = response.json()

                    if data.get("status") == "completed":
                        # Download result
                        if "file_url" in data:
                            download_response = await client.get(data["file_url"])
                            download_response.raise_for_status()

                            extension = "mp3" if media_type == MediaType.MUSIC else "mp4"
                            file_path = self._save_media_file(
                                download_response.content,
                                extension,
                                media_type
                            )

                            self.tasks[task_id]["status"] = TaskStatus.COMPLETED
                            self.tasks[task_id]["file_path"] = file_path

                            return MediaGenerationResult(
                                success=True,
                                media_type=media_type,
                                file_path=file_path,
                                url=data.get("file_url"),
                                task_id=task_id,
                                status=TaskStatus.COMPLETED,
                                metadata={
                                    "provider": self.provider_name,
                                    "duration": data.get("duration")
                                }
                            )

                    elif data.get("status") == "failed":
                        self.tasks[task_id]["status"] = TaskStatus.FAILED
                        return MediaGenerationResult(
                            success=False,
                            media_type=media_type,
                            task_id=task_id,
                            status=TaskStatus.FAILED,
                            error=data.get("error", "Generation failed")
                        )

                    # Still processing, wait and retry
                    await asyncio.sleep(poll_interval)

                except Exception as e:
                    logger.error(f"Error polling task {provider_task_id}: {e}")
                    break

            # Timeout
            return MediaGenerationResult(
                success=False,
                media_type=media_type,
                task_id=task_id,
                status=TaskStatus.PROCESSING,
                error="Task completion polling timeout"
            )

    async def check_task_status(self, task_id: str) -> Optional[MediaGenerationResult]:
        """Check status of async task"""
        if task_id not in self.tasks:
            return None

        task_info = self.tasks[task_id]

        if task_info["status"] == TaskStatus.COMPLETED:
            return MediaGenerationResult(
                success=True,
                media_type=MediaType(task_info["media_type"]),
                file_path=task_info.get("file_path"),
                task_id=task_id,
                status=TaskStatus.COMPLETED
            )

        # Poll for update
        return await self._poll_task_completion(
            task_id,
            task_info["provider_task_id"],
            MediaType(task_info["media_type"]),
            max_polls=1  # Just check once
        )


class ComfyUIProvider(MediaProvider):
    """ComfyUI workflow-based image/video/music generation provider"""

    def __init__(self):
        super().__init__("ComfyUI")
        self.supported_media_types = [MediaType.IMAGE, MediaType.VIDEO, MediaType.MUSIC]
        self.base_url = settings.comfyui_base_url
        self.use_cloud = settings.comfyui_use_cloud
        self.api_key = settings.comfyui_cloud_api_key
        self.workflows: Dict[str, Dict] = {}  # Store workflow definitions

    def load_workflow(self, workflow_name: str, workflow_def: Dict):
        """Load a ComfyUI workflow definition"""
        self.workflows[workflow_name] = workflow_def
        logger.info(f"Loaded ComfyUI workflow: {workflow_name}")

    async def generate(self, request: MediaGenerationRequest) -> MediaGenerationResult:
        """Generate media using ComfyUI workflows"""
        if not settings.comfyui_enabled:
            return MediaGenerationResult(
                success=False,
                media_type=request.media_type,
                error="ComfyUI is not enabled"
            )

        try:
            workflow_name = request.parameters.get("workflow", settings.comfyui_default_workflow)

            if workflow_name not in self.workflows:
                return MediaGenerationResult(
                    success=False,
                    media_type=request.media_type,
                    error=f"Workflow '{workflow_name}' not found"
                )

            workflow = copy.deepcopy(self.workflows[workflow_name])

            # Inject prompt into workflow
            workflow = self._inject_prompt(workflow, request.prompt)

            # Upload reference image if provided
            if request.reference_image:
                workflow = await self._inject_reference_image(workflow, request.reference_image)

            # Execute workflow
            result = await self._execute_workflow(workflow, request.media_type)
            return result

        except Exception as e:
            logger.error(f"ComfyUI generation failed: {e}")
            return MediaGenerationResult(
                success=False,
                media_type=request.media_type,
                error=str(e)
            )

    def _inject_prompt(self, workflow: Dict, prompt: str) -> Dict:
        """Inject prompt into workflow definition"""
        # Find text/prompt nodes and update them
        for node_id, node in workflow.get("nodes", {}).items():
            if node.get("class_type") in ["CLIPTextEncode", "TextPrompt", "PromptNode"]:
                if "inputs" in node:
                    node["inputs"]["text"] = prompt

        return workflow

    async def _inject_reference_image(self, workflow: Dict, image_path: str) -> Dict:
        """Upload reference image and inject into workflow"""
        # Upload image to ComfyUI
        async with httpx.AsyncClient() as client:
            with open(image_path, 'rb') as f:
                files = {"image": f}
                upload_url = f"{self.base_url}/upload/image"

                if self.use_cloud:
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                else:
                    headers = {}

                response = await client.post(upload_url, files=files, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Inject uploaded image into LoadImage nodes
                image_name = data.get("name")
                for node_id, node in workflow.get("nodes", {}).items():
                    if node.get("class_type") == "LoadImage":
                        if "inputs" in node:
                            node["inputs"]["image"] = image_name

        return workflow

    async def _execute_workflow(
        self,
        workflow: Dict,
        media_type: MediaType
    ) -> MediaGenerationResult:
        """Execute ComfyUI workflow and download result"""
        async with httpx.AsyncClient(timeout=settings.max_media_generation_time) as client:
            # Queue workflow
            queue_url = f"{self.base_url}/prompt"
            headers = {}

            if self.use_cloud:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = await client.post(
                queue_url,
                json={"prompt": workflow},
                headers=headers
            )

            response.raise_for_status()
            data = response.json()
            prompt_id = data.get("prompt_id")

            # Poll for completion
            history_url = f"{self.base_url}/history/{prompt_id}"

            for _ in range(60):  # Max 5 minutes
                await asyncio.sleep(5)

                history_response = await client.get(history_url, headers=headers)
                history_response.raise_for_status()
                history_data = history_response.json()

                if prompt_id in history_data:
                    outputs = history_data[prompt_id].get("outputs", {})

                    # Find output node – ComfyUI may return images, videos, or audio
                    for node_id, node_output in outputs.items():
                        # Check all output keys that may contain downloadable files
                        output_file = None
                        for output_key in ("images", "videos", "audio", "gifs"):
                            files = node_output.get(output_key)
                            if files:
                                output_file = files[0]
                                break

                        if output_file is None:
                            continue

                        filename = output_file.get("filename")

                        download_url = f"{self.base_url}/view?filename={filename}"
                        download_response = await client.get(download_url, headers=headers)
                        download_response.raise_for_status()

                        # Determine extension
                        extension = Path(filename).suffix.lstrip('.')
                        file_path = self._save_media_file(
                            download_response.content,
                            extension,
                            media_type
                        )

                        return MediaGenerationResult(
                            success=True,
                            media_type=media_type,
                            file_path=file_path,
                            metadata={
                                "provider": self.provider_name,
                                "workflow_id": prompt_id,
                                "filename": filename
                            }
                        )

            return MediaGenerationResult(
                success=False,
                media_type=media_type,
                error="Workflow execution timeout"
            )


class MediaGenerationManager:
    """Manager for all media generation providers"""

    def __init__(self):
        self.providers: Dict[str, MediaProvider] = {}
        self._register_providers()

    def _register_providers(self):
        """Register all available providers"""
        # Google Lyria
        if settings.google_lyria_enabled:
            self.providers["google_lyria"] = GoogleLyriaProvider()

        # MiniMax
        if settings.minimax_enabled:
            self.providers["minimax"] = MiniMaxProvider()

        # ComfyUI
        if settings.comfyui_enabled:
            self.providers["comfyui"] = ComfyUIProvider()

        logger.info(f"Registered {len(self.providers)} media generation providers")

    def get_provider(self, provider_name: str) -> Optional[MediaProvider]:
        """Get provider by name"""
        return self.providers.get(provider_name)

    def get_providers_for_media_type(self, media_type: MediaType) -> List[str]:
        """Get list of provider names that support a media type"""
        return [
            name for name, provider in self.providers.items()
            if provider.supports_media_type(media_type)
        ]

    async def generate_media(
        self,
        media_type: MediaType,
        prompt: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> MediaGenerationResult:
        """Generate media using specified or auto-selected provider"""

        # Auto-select provider if not specified
        if not provider:
            available = self.get_providers_for_media_type(media_type)
            if not available:
                return MediaGenerationResult(
                    success=False,
                    media_type=media_type,
                    error=f"No providers available for {media_type.value}"
                )
            provider = available[0]  # Use first available

        provider_instance = self.get_provider(provider)
        if not provider_instance:
            return MediaGenerationResult(
                success=False,
                media_type=media_type,
                error=f"Provider '{provider}' not found or not enabled"
            )

        if not provider_instance.supports_media_type(media_type):
            return MediaGenerationResult(
                success=False,
                media_type=media_type,
                error=f"Provider '{provider}' does not support {media_type.value}"
            )

        request = MediaGenerationRequest(
            media_type=media_type,
            prompt=prompt,
            provider=provider,
            parameters=kwargs
        )

        return await provider_instance.generate(request)


# Global media generation manager
media_manager = MediaGenerationManager()
