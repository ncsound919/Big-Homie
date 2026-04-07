# Media Generation Guide

Big Homie now supports AI-powered image, video, and music generation through multiple providers!

## 🎨 Overview

The media generation system provides:
- **Image Generation** via ComfyUI workflows
- **Video Generation** via MiniMax or ComfyUI workflows
- **Music Generation** via Google Lyria, MiniMax, or ComfyUI workflows
- **Async Task Tracking** for long-running generations
- **Smart Parameter Handling** that warns about unsupported params instead of failing

## 🚀 Quick Start

### Configuration

Add the following to your `.env` file:

```bash
# Enable media generation
ENABLE_MEDIA_GENERATION=true

# Google Lyria (Music)
GOOGLE_LYRIA_API_KEY=your_api_key_here
GOOGLE_LYRIA_ENABLED=true

# MiniMax (Music & Video)
MINIMAX_API_KEY=your_api_key_here
MINIMAX_GROUP_ID=your_group_id
MINIMAX_ENABLED=true

# ComfyUI (Image, Video, Music via workflows)
COMFYUI_ENABLED=true
COMFYUI_BASE_URL=http://localhost:8188  # Local ComfyUI
# OR for Comfy Cloud:
COMFYUI_USE_CLOUD=true
COMFYUI_CLOUD_API_KEY=your_comfy_cloud_key

# Media output directory
MEDIA_OUTPUT_DIR=~/.big_homie/media_outputs
MAX_MEDIA_GENERATION_TIME=300  # 5 minutes timeout
ENABLE_ASYNC_MEDIA_TASKS=true
```

## 🎵 Music Generation

### Using Google Lyria

```python
from media_generation import media_manager, MediaType

result = await media_manager.generate_media(
    media_type=MediaType.MUSIC,
    prompt="Upbeat electronic dance music with heavy bass",
    provider="google_lyria"
)

print(f"Music saved to: {result.file_path}")
```

**Via MCP Tool:**

```python
result = await mcp.execute_tool(
    "music_generate",
    {
        "prompt": "Relaxing piano melody for meditation",
        "provider": "google_lyria",
        "durationSeconds": 60  # Will be ignored with a warning
    },
    context={"confirmed": True}
)
```

**Key Features:**
- ✅ Ignores unsupported parameters like `durationSeconds` with warnings
- ✅ Returns downloadable MP3 file
- ✅ Includes metadata about the generation

### Using MiniMax

```python
result = await media_manager.generate_media(
    media_type=MediaType.MUSIC,
    prompt="Epic orchestral soundtrack with drums and strings",
    provider="minimax",
    genre="orchestral",
    mood="epic",
    tempo="fast"
)

if result.status == TaskStatus.PROCESSING:
    print(f"Task {result.task_id} is processing...")
    # Poll for completion later
else:
    print(f"Music ready: {result.file_path}")
```

### Using ComfyUI Workflows

```python
# First, load a music generation workflow
from media_generation import media_manager

comfyui_provider = media_manager.get_provider("comfyui")
comfyui_provider.load_workflow("music_gen", {
    "nodes": {
        "1": {
            "class_type": "PromptNode",
            "inputs": {"text": ""}
        },
        # ... workflow definition
    }
})

# Generate music
result = await media_manager.generate_media(
    media_type=MediaType.MUSIC,
    prompt="Ambient background music",
    provider="comfyui",
    workflow="music_gen"
)
```

## 🎬 Video Generation

### Using MiniMax

```python
result = await media_manager.generate_media(
    media_type=MediaType.VIDEO,
    prompt="A cat playing piano in a jazz club",
    provider="minimax",
    duration=5,  # 5 seconds
    width=1920,
    height=1080,
    fps=30
)

if result.success:
    print(f"Video: {result.file_path}")
```

**Via MCP Tool:**

```python
result = await mcp.execute_tool(
    "video_generate",
    {
        "prompt": "Timelapse of a sunset over mountains",
        "provider": "minimax",
        "duration": 10,
        "width": 1280,
        "height": 720
    },
    context={"confirmed": True}
)
```

### Using ComfyUI

```python
# Load video workflow
comfyui_provider.load_workflow("video_gen", workflow_definition)

result = await media_manager.generate_media(
    media_type=MediaType.VIDEO,
    prompt="Futuristic cityscape at night",
    provider="comfyui",
    workflow="video_gen"
)
```

## 🖼️ Image Generation

### Using ComfyUI

```python
result = await media_manager.generate_media(
    media_type=MediaType.IMAGE,
    prompt="A serene lake surrounded by mountains at sunrise",
    provider="comfyui",
    width=1024,
    height=768
)
```

**With Reference Image:**

```python
result = await media_manager.generate_media(
    media_type=MediaType.IMAGE,
    prompt="Same scene but in winter with snow",
    provider="comfyui",
    reference_image="/path/to/reference.jpg",
    width=1024,
    height=768
)
```

**Via MCP Tool:**

```python
result = await mcp.execute_tool(
    "image_generate",
    {
        "prompt": "Fantasy castle on a floating island",
        "workflow": "default",
        "width": 512,
        "height": 512
    },
    context={"confirmed": True}
)
```

## 🔄 Async Task Tracking

For long-running tasks (especially video and music), Big Homie supports async task tracking:

```python
# Submit task
result = await media_manager.generate_media(
    media_type=MediaType.VIDEO,
    prompt="Long cinematic sequence",
    provider="minimax"
)

if result.status == TaskStatus.PROCESSING:
    task_id = result.task_id
    print(f"Task submitted: {task_id}")

    # Check status later
    minimax_provider = media_manager.get_provider("minimax")
    status_result = await minimax_provider.check_task_status(task_id)

    if status_result.status == TaskStatus.COMPLETED:
        print(f"Complete! File: {status_result.file_path}")
```

**Automatic Polling:**

If `ENABLE_ASYNC_MEDIA_TASKS=true`, the system automatically polls for completion:

```python
# This will wait for completion (up to MAX_MEDIA_GENERATION_TIME)
result = await media_manager.generate_media(
    media_type=MediaType.MUSIC,
    prompt="Long symphony",
    provider="minimax"
)

# Returns when complete
print(f"Done: {result.file_path}")
```

## 🎯 Provider Comparison

| Feature | Google Lyria | MiniMax | ComfyUI |
|---------|-------------|---------|---------|
| **Music** | ✅ Fast | ✅ High Quality | ✅ Custom Workflows |
| **Video** | ❌ | ✅ Yes | ✅ Custom Workflows |
| **Image** | ❌ | ❌ | ✅ Yes |
| **Async Tasks** | ❌ Sync Only | ✅ Yes | ✅ Yes |
| **Param Filtering** | ✅ Warns on unsupported | ✅ Full Support | ✅ Workflow-based |
| **Reference Images** | ❌ | ❌ | ✅ Yes |
| **Custom Workflows** | ❌ | ❌ | ✅ Yes |

## 📁 ComfyUI Workflow Format

ComfyUI workflows are JSON definitions that describe the generation pipeline:

```json
{
  "nodes": {
    "1": {
      "class_type": "CLIPTextEncode",
      "inputs": {
        "text": "placeholder prompt"
      }
    },
    "2": {
      "class_type": "LoadImage",
      "inputs": {
        "image": "placeholder.png"
      }
    },
    "3": {
      "class_type": "KSampler",
      "inputs": {
        "seed": 42,
        "steps": 20,
        "cfg": 7.0
      }
    }
  }
}
```

**Loading Workflows:**

```python
import json
from media_generation import media_manager

# Load from file
with open("my_workflow.json") as f:
    workflow_def = json.load(f)

comfyui = media_manager.get_provider("comfyui")
comfyui.load_workflow("my_custom_workflow", workflow_def)

# Use it
result = await media_manager.generate_media(
    media_type=MediaType.IMAGE,
    prompt="Your prompt here",
    provider="comfyui",
    workflow="my_custom_workflow"
)
```

## 🔧 Advanced Features

### Smart Parameter Filtering

Providers automatically filter unsupported parameters with warnings:

```python
# Google Lyria doesn't support durationSeconds
result = await media_manager.generate_media(
    media_type=MediaType.MUSIC,
    prompt="Jazz music",
    provider="google_lyria",
    durationSeconds=120,  # ⚠️ Ignored with warning
    genre="jazz"  # ⚠️ Ignored with warning
)

# Log output:
# WARNING: Google Lyria: Ignoring unsupported parameter 'durationSeconds' (value: 120)
# WARNING: Google Lyria: Ignoring unsupported parameter 'genre' (value: jazz)
```

### Auto-Provider Selection

Don't know which provider to use? Let Big Homie choose:

```python
# Automatically selects first available provider for music
result = await media_manager.generate_media(
    media_type=MediaType.MUSIC,
    prompt="Classical piano"
    # No provider specified - auto-selects
)

# Check which was used
print(f"Used provider: {result.metadata['provider']}")
```

### Available Providers Query

```python
from media_generation import media_manager, MediaType

# Get all providers for a media type
music_providers = media_manager.get_providers_for_media_type(MediaType.MUSIC)
print(f"Music providers: {music_providers}")
# Output: ['google_lyria', 'minimax', 'comfyui']

video_providers = media_manager.get_providers_for_media_type(MediaType.VIDEO)
print(f"Video providers: {video_providers}")
# Output: ['minimax', 'comfyui']
```

## 🛠️ Error Handling

```python
result = await media_manager.generate_media(
    media_type=MediaType.VIDEO,
    prompt="Test video",
    provider="minimax"
)

if not result.success:
    print(f"Generation failed: {result.error}")

    # Common errors:
    # - "Provider 'xyz' not found or not enabled"
    # - "No providers available for video"
    # - "API error: 401" (authentication failed)
    # - "Task completion polling timeout"
```

## 📊 Output Files

Generated media is saved to `~/.big_homie/media_outputs/`:

```
~/.big_homie/media_outputs/
├── music_20260407_120000_a1b2c3d4.mp3
├── video_20260407_121500_e5f6g7h8.mp4
├── image_20260407_130000_i9j0k1l2.png
└── ...
```

File naming: `{type}_{timestamp}_{uuid}.{extension}`

## 🧪 Testing

Test media generation in Python:

```python
import asyncio
from media_generation import media_manager, MediaType

async def test_music():
    result = await media_manager.generate_media(
        media_type=MediaType.MUSIC,
        prompt="Test music generation",
        provider="google_lyria"
    )
    assert result.success
    assert result.file_path
    print(f"✅ Music test passed: {result.file_path}")

asyncio.run(test_music())
```

## 📝 Agent Integration

Agents can now generate media directly in their responses:

**Example Agent Conversation:**

```
User: "Create a relaxing background music track"

Agent: [Uses music_generate tool]
       ✅ Generated relaxing piano music
       📁 File: ~/.big_homie/media_outputs/music_20260407_120000_abc123.mp3
       🎵 Duration: 30 seconds
       💰 Cost: $0.05
```

**Example with Video:**

```
User: "Generate a short video of a sunset"

Agent: [Uses video_generate tool]
       ⏳ Video generation in progress...
       [Polls for completion]
       ✅ Video ready!
       📁 File: ~/.big_homie/media_outputs/video_20260407_121500_def456.mp4
       🎬 Resolution: 1280x720
       ⏱️ Duration: 5 seconds
```

## 🔐 Security

- All media generation tools require `confirmed=True` in context
- Generated files are saved to a sandboxed directory
- Reference images must be within allowed directories (for ComfyUI)
- API keys are never exposed in responses

## 💡 Tips & Best Practices

1. **Be Specific**: Detailed prompts produce better results
   - ❌ "music"
   - ✅ "upbeat electronic dance music with synth bass and drums, 128 BPM"

2. **Choose the Right Provider**:
   - Quick music → Google Lyria
   - High-quality music/video → MiniMax
   - Custom workflows → ComfyUI

3. **Handle Async Tasks**:
   - For long generations, enable async task tracking
   - Check task status periodically
   - Set reasonable timeouts

4. **Workflow Reuse**:
   - Load ComfyUI workflows once, reuse many times
   - Store workflows as JSON files for easy management

5. **Monitor Costs**:
   - Each provider has different pricing
   - Check metadata for cost information
   - Use cost guards in production

## 🚨 Troubleshooting

**"Provider not found or not enabled"**
- Check `.env` configuration
- Ensure provider is enabled (e.g., `GOOGLE_LYRIA_ENABLED=true`)
- Verify API keys are set

**"Workflow not found"**
- Load the workflow before using it
- Check workflow name spelling
- Verify workflow JSON is valid

**"Task completion polling timeout"**
- Increase `MAX_MEDIA_GENERATION_TIME`
- Check provider API status
- Verify network connectivity

**ComfyUI connection errors**
- Ensure ComfyUI is running (local) or credentials are correct (cloud)
- Check `COMFYUI_BASE_URL` is correct
- Test with ComfyUI web interface first

---

**Big Homie Media Generation** - Create stunning visuals and audio with AI! 🎨🎵🎬
