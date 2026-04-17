"""
Multi-Agent Profiles System for Big Homie
Run unlimited isolated agents with persistent role definitions
"""

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from config import settings


@dataclass
class AgentProfile:
    """Represents an agent profile with persistent configuration"""

    profile_id: str
    name: str
    role: str
    system_prompt: str
    model: str
    temperature: float
    max_tokens: int
    tools_enabled: list[str]
    memory_isolated: bool
    created_at: str
    updated_at: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict:
        """Convert profile to dictionary"""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "AgentProfile":
        """Create profile from dictionary"""
        return AgentProfile(**data)


class AgentProfileManager:
    """
    Manages multiple agent profiles with isolated configurations

    Features:
    - Persistent profile storage
    - Profile switching
    - Isolated memory per profile (optional)
    - Custom system prompts and tools per profile
    - Profile templates
    """

    def __init__(self):
        """Initialize the profile manager"""
        self.profiles_dir = settings.data_dir / "agent_profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self.profiles_dir / "_state.json"
        self.profiles: dict[str, AgentProfile] = {}
        self.active_profile_id: Optional[str] = None
        self._load_profiles()

    def _load_profiles(self):
        """Load all profiles from disk"""
        for profile_file in self.profiles_dir.glob("*.json"):
            if profile_file.name == "_state.json":
                continue
            try:
                with open(profile_file) as f:
                    data = json.load(f)
                    profile = AgentProfile.from_dict(data)
                    self.profiles[profile.profile_id] = profile
                    logger.info(f"Loaded agent profile: {profile.name}")
            except Exception as e:
                logger.error(f"Error loading profile {profile_file}: {e}")

        # Load or create default profile
        if not self.profiles:
            self._create_default_profile()

        # Restore the last active profile from persisted state
        if self._state_file.exists():
            try:
                state = json.loads(self._state_file.read_text())
                saved_id = state.get("active_profile_id")
                if saved_id and saved_id in self.profiles:
                    self.active_profile_id = saved_id
            except Exception as e:
                logger.warning(f"Could not restore active profile state: {e}")

        # Fall back to first profile when no valid state is available
        if not self.active_profile_id and self.profiles:
            self.active_profile_id = list(self.profiles.keys())[0]

    def _create_default_profile(self):
        """Create the default agent profile"""
        default_profile = AgentProfile(
            profile_id="default",
            name="Big Homie Default",
            role="General Purpose AI Assistant",
            system_prompt=(
                "You are Big Homie, a helpful AI assistant with access to tools and capabilities."
            ),
            model=settings.default_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            tools_enabled=["all"],
            memory_isolated=False,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            metadata={},
        )
        self.save_profile(default_profile)

    @staticmethod
    def _sanitize_profile_id(profile_id: str) -> str:
        """
        Sanitize a profile ID to a safe filesystem name.

        Only lowercase alphanumerics, hyphens, and underscores are allowed.
        Raises ValueError if the raw profile_id contains path separators
        (forward-slash or backslash), which are the only characters that enable
        directory traversal. The remaining re.sub to [a-z0-9_-] makes the
        result safe as a plain filename component regardless of any other
        characters present.
        """
        if "/" in profile_id or "\\" in profile_id:
            raise ValueError(f"Invalid profile_id '{profile_id}': path separators are not allowed")
        sanitized = re.sub(r"[^a-z0-9_\-]", "", profile_id.lower())
        if not sanitized:
            raise ValueError(
                f"Invalid profile_id '{profile_id}': "
                "must contain at least one "
                "alphanumeric character"
            )
        return sanitized

    def create_profile(
        self,
        name: str,
        role: str,
        system_prompt: str,
        profile_id: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools_enabled: Optional[list[str]] = None,
        memory_isolated: bool = True,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AgentProfile:
        """
        Create a new agent profile

        Args:
            name: Profile name
            role: Agent role description
            system_prompt: Custom system prompt
            profile_id: Optional custom ID (auto-generated if not provided)
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max output tokens
            tools_enabled: List of enabled tools (or ["all"])
            memory_isolated: Whether to use isolated memory
            metadata: Additional metadata

        Returns:
            Created AgentProfile
        """
        if not profile_id:
            # Generate ID from name
            profile_id = name.lower().replace(" ", "_")

        # Sanitize to prevent path traversal attacks
        profile_id = self._sanitize_profile_id(profile_id)

        if profile_id in self.profiles:
            raise ValueError(f"Profile with ID '{profile_id}' already exists")

        profile = AgentProfile(
            profile_id=profile_id,
            name=name,
            role=role,
            system_prompt=system_prompt,
            model=model or settings.default_model,
            temperature=temperature if temperature is not None else settings.temperature,
            max_tokens=max_tokens or settings.max_tokens,
            tools_enabled=tools_enabled or ["all"],
            memory_isolated=memory_isolated,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            metadata=metadata or {},
        )

        self.save_profile(profile)
        logger.info(f"Created agent profile: {name} ({profile_id})")

        return profile

    def save_profile(self, profile: AgentProfile):
        """Save a profile to disk"""
        profile.updated_at = datetime.now().isoformat()
        self.profiles[profile.profile_id] = profile

        profile_file = self.profiles_dir / f"{profile.profile_id}.json"
        with open(profile_file, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)

        logger.debug(f"Saved profile: {profile.name}")

    def get_profile(self, profile_id: str) -> Optional[AgentProfile]:
        """Get a profile by ID"""
        return self.profiles.get(profile_id)

    def list_profiles(self) -> list[AgentProfile]:
        """List all profiles"""
        return list(self.profiles.values())

    def delete_profile(self, profile_id: str):
        """Delete a profile"""
        if profile_id == "default":
            raise ValueError("Cannot delete the default profile")

        if profile_id not in self.profiles:
            raise ValueError(f"Profile '{profile_id}' not found")

        # Switch to default if deleting active profile
        if self.active_profile_id == profile_id:
            self.switch_profile("default")

        # Delete from disk
        profile_file = self.profiles_dir / f"{profile_id}.json"
        if profile_file.exists():
            profile_file.unlink()

        del self.profiles[profile_id]
        logger.info(f"Deleted profile: {profile_id}")

    def switch_profile(self, profile_id: str) -> AgentProfile:
        """
        Switch to a different profile

        Args:
            profile_id: Profile ID to switch to

        Returns:
            The activated profile

        Raises:
            ValueError: If profile not found
        """
        if profile_id not in self.profiles:
            raise ValueError(f"Profile '{profile_id}' not found")

        self.active_profile_id = profile_id
        profile = self.profiles[profile_id]
        logger.info(f"Switched to profile: {profile.name} ({profile_id})")

        # Persist the active profile so the selection survives restarts
        try:
            self._state_file.write_text(json.dumps({"active_profile_id": profile_id}, indent=2))
        except Exception as e:
            logger.warning(f"Could not persist active profile state: {e}")

        return profile

    def get_active_profile(self) -> Optional[AgentProfile]:
        """Get the currently active profile"""
        if self.active_profile_id:
            return self.profiles.get(self.active_profile_id)
        return None

    def update_profile(
        self,
        profile_id: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools_enabled: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AgentProfile:
        """
        Update an existing profile

        Args:
            profile_id: Profile to update
            name: New name (optional)
            role: New role (optional)
            system_prompt: New system prompt (optional)
            model: New model (optional)
            temperature: New temperature (optional)
            max_tokens: New max_tokens (optional)
            tools_enabled: New tools list (optional)
            metadata: New metadata (optional)

        Returns:
            Updated profile
        """
        if profile_id not in self.profiles:
            raise ValueError(f"Profile '{profile_id}' not found")

        profile = self.profiles[profile_id]

        if name:
            profile.name = name
        if role:
            profile.role = role
        if system_prompt:
            profile.system_prompt = system_prompt
        if model:
            profile.model = model
        if temperature is not None:
            profile.temperature = temperature
        if max_tokens:
            profile.max_tokens = max_tokens
        if tools_enabled:
            profile.tools_enabled = tools_enabled
        if metadata:
            profile.metadata.update(metadata)

        self.save_profile(profile)

        return profile

    def create_from_template(self, template_name: str, **kwargs) -> AgentProfile:
        """
        Create a profile from a template

        Available templates:
        - coder: Specialized coding assistant
        - researcher: Research and analysis specialist
        - writer: Content creation specialist
        - analyst: Data analysis specialist

        Args:
            template_name: Template to use
            **kwargs: Additional parameters to override template

        Returns:
            Created profile
        """
        templates = {
            "coder": {
                "name": "Code Assistant",
                "role": "Expert Software Engineer",
                "system_prompt": (
                    "You are an expert software engineer"
                    " with deep knowledge of multiple"
                    " programming languages, design"
                    " patterns, and best practices."
                    " Focus on writing clean, efficient,"
                    " and well-documented code."
                ),
                "model": settings.coding_model,
                "temperature": 0.3,
                "tools_enabled": ["all"],
            },
            "researcher": {
                "name": "Research Assistant",
                "role": "Research Specialist",
                "system_prompt": (
                    "You are a thorough research"
                    " specialist. Your goal is to find"
                    " accurate, comprehensive information"
                    " and provide well-sourced, detailed"
                    " analysis."
                ),
                "model": settings.reasoning_model,
                "temperature": 0.5,
                "tools_enabled": ["web_search", "github_search_repos", "browser_navigate"],
            },
            "writer": {
                "name": "Content Writer",
                "role": "Creative Writing Specialist",
                "system_prompt": (
                    "You are a skilled content writer"
                    " with expertise in various writing"
                    " styles. Create engaging,"
                    " well-structured content tailored"
                    " to the audience."
                ),
                "model": settings.default_model,
                "temperature": 0.8,
                "tools_enabled": ["web_search"],
            },
            "analyst": {
                "name": "Data Analyst",
                "role": "Data Analysis Specialist",
                "system_prompt": (
                    "You are a data analyst with strong"
                    " analytical and statistical skills."
                    " Analyze data thoroughly and provide"
                    " clear, actionable insights."
                ),
                "model": settings.reasoning_model,
                "temperature": 0.4,
                "tools_enabled": ["all"],
            },
        }

        if template_name not in templates:
            raise ValueError(
                f"Unknown template: {template_name}. Available: {list(templates.keys())}"
            )

        template = templates[template_name]
        template.update(kwargs)

        return self.create_profile(**template)

    def export_profile(self, profile_id: str, export_path: Path):
        """Export a profile to a JSON file"""
        profile = self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile '{profile_id}' not found")

        with open(export_path, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)

        logger.info(f"Exported profile to: {export_path}")

    def import_profile(self, import_path: Path) -> AgentProfile:
        """Import a profile from a JSON file"""
        with open(import_path) as f:
            data = json.load(f)

        profile = AgentProfile.from_dict(data)

        # Ensure unique ID
        base_id = profile.profile_id
        counter = 1
        while profile.profile_id in self.profiles:
            profile.profile_id = f"{base_id}_{counter}"
            counter += 1

        self.save_profile(profile)
        logger.info(f"Imported profile: {profile.name}")

        return profile


# Global profile manager instance
profile_manager = AgentProfileManager()
