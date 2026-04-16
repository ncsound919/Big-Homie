"""
Tests for Media Generation System
Simple validation tests for the media generation providers
"""
import asyncio
from pathlib import Path
import pytest
from media_generation import (
    MediaGenerationManager,
    MediaType,
    MediaGenerationRequest,
    GoogleLyriaProvider,
    MiniMaxProvider,
    ComfyUIProvider
)

def test_media_manager_initialization():
    """Test that media manager initializes correctly"""
    manager = MediaGenerationManager()
    assert manager is not None
    print("✅ MediaGenerationManager initialized")

def test_provider_registration():
    """Test that providers are registered based on config"""
    manager = MediaGenerationManager()

    # Check that providers dict exists
    assert hasattr(manager, 'providers')
    print(f"✅ Registered {len(manager.providers)} providers")

    # List registered providers
    for name, provider in manager.providers.items():
        print(f"   - {name}: {provider.provider_name} (supports: {provider.supported_media_types})")

def test_get_providers_for_media_type():
    """Test getting providers by media type"""
    manager = MediaGenerationManager()

    # Test each media type
    for media_type in [MediaType.IMAGE, MediaType.VIDEO, MediaType.MUSIC]:
        providers = manager.get_providers_for_media_type(media_type)
        print(f"✅ {media_type.value} supported by: {providers}")

def test_google_lyria_provider():
    """Test Google Lyria provider initialization"""
    provider = GoogleLyriaProvider()
    assert provider.provider_name == "Google Lyria"
    assert MediaType.MUSIC in provider.supported_media_types
    print("✅ GoogleLyriaProvider initialized")

def test_minimax_provider():
    """Test MiniMax provider initialization"""
    provider = MiniMaxProvider()
    assert provider.provider_name == "MiniMax"
    assert MediaType.MUSIC in provider.supported_media_types
    assert MediaType.VIDEO in provider.supported_media_types
    print("✅ MiniMaxProvider initialized")

def test_comfyui_provider():
    """Test ComfyUI provider initialization"""
    provider = ComfyUIProvider()
    assert provider.provider_name == "ComfyUI"
    assert MediaType.IMAGE in provider.supported_media_types
    assert MediaType.VIDEO in provider.supported_media_types
    assert MediaType.MUSIC in provider.supported_media_types
    print("✅ ComfyUIProvider initialized")

def test_parameter_filtering():
    """Test that providers filter unsupported parameters correctly"""
    provider = GoogleLyriaProvider()

    # Supported params
    supported = ["prompt", "temperature"]

    # Test params with some unsupported
    test_params = {
        "prompt": "test",
        "temperature": 0.7,
        "durationSeconds": 60,  # Unsupported
        "genre": "jazz"  # Unsupported
    }

    filtered = provider._filter_unsupported_params(test_params, supported)

    # Should only have supported params
    assert "prompt" in filtered
    assert "temperature" in filtered
    assert "durationSeconds" not in filtered
    assert "genre" not in filtered

    print("✅ Parameter filtering works correctly")

def test_media_request_creation():
    """Test creating media generation requests"""
    request = MediaGenerationRequest(
        media_type=MediaType.MUSIC,
        prompt="Relaxing piano music",
        provider="google_lyria",
        parameters={"temperature": 0.8}
    )

    assert request.media_type == MediaType.MUSIC
    assert request.prompt == "Relaxing piano music"
    assert request.provider == "google_lyria"
    print("✅ MediaGenerationRequest created successfully")

def test_workflow_loading():
    """Test loading ComfyUI workflows"""
    provider = ComfyUIProvider()

    workflow_def = {
        "nodes": {
            "1": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "placeholder"}
            }
        }
    }

    provider.load_workflow("test_workflow", workflow_def)
    assert "test_workflow" in provider.workflows
    print("✅ ComfyUI workflow loading works")

@pytest.mark.asyncio
async def test_auto_provider_selection():
    """Test automatic provider selection"""
    manager = MediaGenerationManager()

    # This should work even without specifying a provider
    # (will select first available for the media type)
    providers = manager.get_providers_for_media_type(MediaType.MUSIC)

    if providers:
        print(f"✅ Auto-selection available: {providers[0]} will be used for music")
    else:
        print("⚠️  No music providers available (expected if none configured)")

def test_output_directory():
    """Test that output directory is created"""
    from config import settings
    output_dir = Path(settings.media_output_dir)

    # Directory should be created by settings.ensure_dirs()
    assert output_dir.exists()
    print(f"✅ Media output directory exists: {output_dir}")

def run_all_tests():
    """Run all synchronous tests"""
    print("\n" + "="*60)
    print("🧪 Running Media Generation Tests")
    print("="*60 + "\n")

    tests = [
        test_media_manager_initialization,
        test_provider_registration,
        test_get_providers_for_media_type,
        test_google_lyria_provider,
        test_minimax_provider,
        test_comfyui_provider,
        test_parameter_filtering,
        test_media_request_creation,
        test_workflow_loading,
        test_output_directory
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1

    # Run async tests
    try:
        asyncio.run(test_auto_provider_selection())
        passed += 1
    except Exception as e:
        print(f"❌ test_auto_provider_selection failed: {e}")
        failed += 1

    print("\n" + "="*60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    if failed == 0:
        print("✨ All tests passed! Media generation system is ready.")
    else:
        print(f"⚠️  {failed} test(s) failed. Please review.")

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
