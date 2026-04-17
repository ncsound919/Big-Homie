"""
LLM Gateway - Multi-provider unified interface
Supports: Anthropic, OpenAI, OpenRouter, Ollama, Groq, GitHub Copilot
With vision support, cost guards, thought logging, and rate-limit backoff
"""
import asyncio
import json
import time
import httpx
from typing import Optional, Dict, Any, List, AsyncGenerator, Union
from enum import Enum
from loguru import logger
from config import settings
from mcp_integration import mcp
import free_api_stack

class Provider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    GROQ = "groq"
    COPILOT = "copilot"

class TaskType(str, Enum):
    REASONING = "reasoning"
    CODING = "coding"
    FAST = "fast"
    GENERAL = "general"

class LLMGateway:
    """Unified LLM interface with automatic provider selection"""

    OPENAI_FALLBACK_MODEL = "gpt-4"
    ANTHROPIC_FALLBACK_MODEL = "claude-sonnet-4-5"
    OPENROUTER_REASONING_FALLBACK = "anthropic/claude-3.5-sonnet"
    OPENROUTER_FAST_FALLBACK = "google/gemini-flash-1.5-8b"
    OPENROUTER_GENERAL_FALLBACK = "google/gemini-flash-1.5-8b"
    OLLAMA_GENERAL_FALLBACK = "qwen2.5:7b"
    OLLAMA_CODER_FALLBACK = "deepseek-coder:6.7b"
    GROQ_DEFAULT_MODEL = free_api_stack.GROQ_MODEL

    # Rate-limit cooldown: default 60 seconds before retrying a rate-limited provider
    RATE_LIMIT_COOLDOWN = 60.0

    def __init__(self):
        self.anthropic_client = None
        self.openai_client = None
        self.total_cost = 0.0
        # Track when each provider's rate limit expires (provider value -> unix timestamp)
        self._rate_limit_until: Dict[str, float] = {}

        # Initialize clients based on available API keys
        if settings.anthropic_api_key:
            from anthropic import Anthropic
            self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)

        if settings.openai_api_key:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=settings.openai_api_key)

        # Initialize cost guard and thoughts logger
        if settings.enable_cost_guards:
            from cost_guards import cost_guard
            self.cost_guard = cost_guard
        else:
            self.cost_guard = None

        if settings.enable_thought_logging:
            from thoughts_logger import thoughts_logger
            self.thoughts_logger = thoughts_logger
        else:
            self.thoughts_logger = None

    def select_model(self, task_type: TaskType) -> tuple[Provider, str]:
        """Select best model for task type"""
        routing_map = {
            TaskType.REASONING: (Provider.ANTHROPIC, settings.reasoning_model),
            TaskType.CODING: (Provider.OPENAI, settings.coding_model),
            TaskType.FAST: (Provider.ANTHROPIC, settings.fast_model),
            TaskType.GENERAL: (Provider.ANTHROPIC, settings.default_model),
        }

        provider, model = routing_map.get(task_type, (Provider.ANTHROPIC, settings.default_model))

        # Fallback logic
        if provider == Provider.ANTHROPIC and not self.anthropic_client:
            if self.openai_client:
                provider, model = Provider.OPENAI, self.OPENAI_FALLBACK_MODEL
            elif settings.ollama_enabled:
                provider, model = Provider.OLLAMA, self.OLLAMA_GENERAL_FALLBACK

        return provider, model

    def _infer_provider_from_model(self, model: str) -> Optional[Provider]:
        """Infer provider from a model identifier when possible."""
        model_lower = model.lower()

        if "/" in model:
            return Provider.OPENROUTER
        if model_lower.startswith("claude"):
            return Provider.ANTHROPIC
        if model_lower.startswith("gpt-"):
            return Provider.OPENAI
        if ":" in model:
            return Provider.OLLAMA
        if model_lower.startswith("llama") or model_lower.startswith("mixtral"):
            return Provider.GROQ

        return None

    def _resolve_provider_and_model(
        self,
        task_type: TaskType,
        provider_override: Optional[Union[Provider, str]] = None,
        model_override: Optional[str] = None
    ) -> tuple[Provider, str]:
        """Resolve the requested provider/model while preserving existing defaults."""
        provider, model = self.select_model(task_type)

        if model_override:
            model = model_override

        if provider_override:
            provider = provider_override if isinstance(provider_override, Provider) else Provider(provider_override)
        elif model_override:
            inferred_provider = self._infer_provider_from_model(model_override)
            if inferred_provider:
                provider = inferred_provider

        return provider, model

    def _provider_is_available(self, provider: Provider) -> bool:
        """Check whether a provider is configured and available."""
        if provider == Provider.ANTHROPIC:
            return self.anthropic_client is not None
        if provider == Provider.OPENAI:
            return self.openai_client is not None
        if provider == Provider.OPENROUTER:
            return bool(settings.openrouter_api_key)
        if provider == Provider.OLLAMA:
            return bool(settings.ollama_enabled)
        if provider == Provider.HUGGINGFACE:
            return bool(settings.huggingface_enabled and settings.huggingface_api_key)
        if provider == Provider.GROQ:
            return free_api_stack.check_providers().get("groq", False)
        return False

    def _get_fallback_candidates(self, task_type: TaskType) -> List[tuple[Provider, str]]:
        """Get ordered fallback candidates for a task type."""
        fallback_map = {
            TaskType.REASONING: [
                (Provider.OPENAI, self.OPENAI_FALLBACK_MODEL),
                (Provider.OPENROUTER, self.OPENROUTER_REASONING_FALLBACK),
                (Provider.GROQ, self.GROQ_DEFAULT_MODEL),
                (Provider.HUGGINGFACE, settings.huggingface_default_model),
                (Provider.OLLAMA, self.OLLAMA_GENERAL_FALLBACK),
            ],
            TaskType.CODING: [
                (Provider.ANTHROPIC, self.ANTHROPIC_FALLBACK_MODEL),
                (Provider.OPENROUTER, self.OPENROUTER_REASONING_FALLBACK),
                (Provider.GROQ, self.GROQ_DEFAULT_MODEL),
                (Provider.HUGGINGFACE, settings.huggingface_default_model),
                (Provider.OLLAMA, self.OLLAMA_CODER_FALLBACK),
            ],
            TaskType.FAST: [
                (Provider.GROQ, self.GROQ_DEFAULT_MODEL),
                (Provider.OPENAI, "gpt-4o-mini"),
                (Provider.OPENROUTER, self.OPENROUTER_FAST_FALLBACK),
                (Provider.HUGGINGFACE, settings.huggingface_default_model),
                (Provider.OLLAMA, self.OLLAMA_GENERAL_FALLBACK),
            ],
            TaskType.GENERAL: [
                (Provider.OPENAI, self.OPENAI_FALLBACK_MODEL),
                (Provider.OPENROUTER, self.OPENROUTER_GENERAL_FALLBACK),
                (Provider.GROQ, self.GROQ_DEFAULT_MODEL),
                (Provider.HUGGINGFACE, settings.huggingface_default_model),
                (Provider.OLLAMA, self.OLLAMA_GENERAL_FALLBACK),
            ],
        }
        return fallback_map.get(task_type, fallback_map[TaskType.GENERAL])

    def _build_attempt_chain(
        self,
        task_type: TaskType,
        primary_provider: Provider,
        primary_model: str
    ) -> List[tuple[Provider, str]]:
        """Build the ordered provider/model attempt chain."""
        attempts: List[tuple[Provider, str]] = [(primary_provider, primary_model)]

        if primary_provider == Provider.ANTHROPIC:
            attempts.extend([(Provider.OPENAI, self.OPENAI_FALLBACK_MODEL)])
        elif primary_provider == Provider.OPENAI:
            attempts.extend([(Provider.ANTHROPIC, self.ANTHROPIC_FALLBACK_MODEL)])
        elif primary_provider == Provider.OPENROUTER:
            attempts.extend([
                (Provider.OPENAI, self.OPENAI_FALLBACK_MODEL),
                (Provider.ANTHROPIC, self.ANTHROPIC_FALLBACK_MODEL),
            ])

        attempts.extend(self._get_fallback_candidates(task_type))

        now = time.monotonic()
        deduped_attempts: List[tuple[Provider, str]] = []
        seen = set()
        for provider, model in attempts:
            key = (provider.value, model)
            if key in seen or not self._provider_is_available(provider):
                continue
            # Skip providers that are currently rate-limited
            rate_limit_expiry = self._rate_limit_until.get(provider.value, 0)
            if rate_limit_expiry > now:
                logger.debug(
                    f"Skipping rate-limited provider {provider.value} "
                    f"(cooldown expires in {rate_limit_expiry - now:.1f}s)"
                )
                continue
            deduped_attempts.append((provider, model))
            seen.add(key)

        return deduped_attempts

    def _is_retryable_provider_error(self, error: Exception) -> bool:
        """Detect provider errors that should trigger silent fallback."""
        error_text = str(error).lower()
        retryable_markers = [
            "429",
            "rate limit",
            "too many requests",
            "temporarily unavailable",
            "overloaded",
            "timeout",
            "timed out",
            "connection reset",
            "service unavailable",
            "api_connection",
        ]
        return any(marker in error_text for marker in retryable_markers)

    async def _invoke_provider(
        self,
        provider: Provider,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]],
        stream: bool,
        **kwargs
    ) -> Dict[str, Any]:
        """Invoke a completion on a specific provider."""
        if provider == Provider.ANTHROPIC:
            return await self._anthropic_complete(messages, model, tools, stream, **kwargs)
        if provider == Provider.OPENAI:
            return await self._openai_complete(messages, model, tools, stream, **kwargs)
        if provider == Provider.OLLAMA:
            return await self._ollama_complete(messages, model, tools, stream, **kwargs)
        if provider == Provider.OPENROUTER:
            return await self._openrouter_complete(messages, model, tools, stream, **kwargs)
        if provider == Provider.HUGGINGFACE:
            return await self._huggingface_complete(messages, model, tools, stream, **kwargs)
        if provider == Provider.GROQ:
            return await self._groq_complete(messages, model, tools, stream, **kwargs)
        raise ValueError(f"Provider {provider} not supported yet")

    def preview_cost(
        self,
        messages: List[Dict[str, str]],
        task_type: TaskType = TaskType.GENERAL,
        provider: Optional[Union[Provider, str]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Preview estimated cost and warn when it crosses the spend threshold."""
        if not self.cost_guard:
            return None

        resolved_provider, resolved_model = self._resolve_preview_target(task_type, provider, model)
        estimate = self.cost_guard.estimate_cost(
            messages=messages,
            model=resolved_model,
            max_output_tokens=max_tokens or settings.max_tokens
        )
        warning_triggered = estimate.estimated_cost >= settings.spend_warning_threshold

        return {
            "provider": resolved_provider.value,
            "model": resolved_model,
            "estimated_cost": estimate.estimated_cost,
            "warning_triggered": warning_triggered,
            "warning_threshold": settings.spend_warning_threshold,
        }

    def _resolve_preview_target(
        self,
        task_type: TaskType,
        provider: Optional[Union[Provider, str]] = None,
        model: Optional[str] = None
    ) -> tuple[Provider, str]:
        """Resolve the first available provider/model pair for preview and execution."""
        resolved_provider, resolved_model = self._resolve_provider_and_model(task_type, provider, model)
        attempts = self._build_attempt_chain(task_type, resolved_provider, resolved_model)
        if attempts:
            return attempts[0]

        logger.warning(
            f"No available provider/model attempts found for {task_type.value}; "
            f"falling back to resolved selection {resolved_provider.value}/{resolved_model}"
        )
        return resolved_provider, resolved_model

    async def complete(
        self,
        messages: List[Dict[str, str]],
        task_type: TaskType = TaskType.GENERAL,
        tools: Optional[List[Dict]] = None,
        enable_mcp_tools: bool = True,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion with automatic provider routing and MCP tool support"""

        requested_provider = kwargs.pop("provider", None)
        requested_model = kwargs.pop("model", None)
        provider, model = self._resolve_provider_and_model(task_type, requested_provider, requested_model)
        logger.info(f"Using {provider.value} with model {model} for {task_type.value}")

        # Log model selection thought
        if self.thoughts_logger and settings.log_model_selections:
            self.thoughts_logger.log_model_selection(
                model=model,
                reason=f"Selected for {task_type.value} task",
                cost_estimate=None
            )

        # Add MCP tools if enabled
        all_tools = tools or []
        if enable_mcp_tools:
            mcp_tools = mcp.get_tools_for_llm()
            all_tools.extend(mcp_tools)
            if mcp_tools:
                logger.debug(f"Added {len(mcp_tools)} MCP tools to request")

        attempts = self._build_attempt_chain(task_type, provider, model)
        last_error: Optional[Exception] = None
        max_output_tokens = kwargs.get("max_tokens", settings.max_tokens)

        for attempt_index, (attempt_provider, attempt_model) in enumerate(attempts):
            try:
                if self.cost_guard:
                    attempt_estimate = self.cost_guard.estimate_cost(
                        messages=messages,
                        model=attempt_model,
                        max_output_tokens=max_output_tokens
                    )

                    if self.thoughts_logger and settings.log_cost_decisions:
                        budget_status = self.cost_guard.get_budget_status()
                        self.thoughts_logger.log_cost_analysis(
                            operation=f"{attempt_provider.value}/{attempt_model}",
                            estimated_cost=attempt_estimate.estimated_cost,
                            budget_impact=f"Daily: ${budget_status.daily_spent:.2f}/${budget_status.daily_limit:.2f}"
                        )

                    approved = await self.cost_guard.check_budget_and_approve(attempt_estimate)
                    if not approved:
                        logger.warning(
                            f"Operation denied by cost guard for {attempt_provider.value}/{attempt_model}"
                        )
                        if attempt_index == 0:
                            return {
                                "content": "Operation cancelled: Cost guard denied approval",
                                "tool_calls": [],
                                "stop_reason": "cost_guard_denied",
                                "usage": {"input_tokens": 0, "output_tokens": 0}
                            }

                        last_error = RuntimeError(
                            f"Cost guard denied approval for fallback model "
                            f"{attempt_provider.value}/{attempt_model} "
                            f"(estimated ${attempt_estimate.estimated_cost:.4f})"
                        )
                        continue

                if attempt_index > 0:
                    logger.warning(
                        f"Falling back to {attempt_provider.value}/{attempt_model} for {task_type.value}"
                    )
                    if self.thoughts_logger:
                        self.thoughts_logger.log_decision(
                            decision=f"Fallback to {attempt_provider.value}/{attempt_model}",
                            rationale="Primary provider was unavailable or hit a retryable failure",
                            metadata={"task_type": task_type.value}
                        )

                result = await self._invoke_provider(
                    attempt_provider,
                    attempt_model,
                    messages,
                    all_tools if all_tools else None,
                    stream,
                    **kwargs
                )

                # Record actual cost with cost guard
                if self.cost_guard and "usage" in result:
                    input_tokens = result["usage"].get("input_tokens", 0)
                    output_tokens = result["usage"].get("output_tokens", 0)
                    if attempt_provider == Provider.ANTHROPIC:
                        actual_cost = self._calculate_anthropic_cost(attempt_model, input_tokens, output_tokens)
                    elif attempt_provider == Provider.OPENROUTER:
                        actual_cost = self._calculate_openrouter_cost(attempt_model, input_tokens, output_tokens)
                    elif attempt_provider == Provider.HUGGINGFACE:
                        actual_cost = self._calculate_huggingface_cost(attempt_model, input_tokens, output_tokens)
                    else:
                        actual_cost = self._calculate_openai_cost(attempt_model, input_tokens, output_tokens)
                    self.cost_guard.record_cost(actual_cost)

                result["_model"] = attempt_model
                result["_request_metadata"] = {"fallback_used": attempt_index > 0}
                return result

            except Exception as e:
                last_error = e
                logger.error(f"LLM request failed with {attempt_provider.value}/{attempt_model}: {str(e)}")

                is_retryable = self._is_retryable_provider_error(e)

                # Track rate-limited providers so they are skipped on subsequent chains
                error_text = str(e).lower()
                if any(m in error_text for m in ("429", "rate limit", "too many requests")):
                    self._rate_limit_until[attempt_provider.value] = (
                        time.monotonic() + self.RATE_LIMIT_COOLDOWN
                    )
                    logger.warning(
                        f"Provider {attempt_provider.value} rate-limited; "
                        f"cooldown for {self.RATE_LIMIT_COOLDOWN}s"
                    )

                if attempt_index == len(attempts) - 1 or not is_retryable:
                    break

                # Exponential backoff before falling through to next provider
                backoff = min(0.5 * (2 ** attempt_index), 8.0)
                logger.info(f"Retryable error; backing off {backoff:.1f}s before next provider")
                await asyncio.sleep(backoff)

        if last_error:
            raise last_error
        raise RuntimeError("No configured providers are available for this request")

    async def _anthropic_complete(
        self, messages: List[Dict], model: str, tools: Optional[List], stream: bool, **kwargs
    ) -> Dict[str, Any]:
        """Anthropic Claude completion"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")

        # Extract system message if present
        system = None
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                filtered_messages.append(msg)

        params = {
            "model": model,
            "messages": filtered_messages,
            "max_tokens": kwargs.get("max_tokens", settings.max_tokens),
            "temperature": kwargs.get("temperature", settings.temperature),
        }

        if system:
            params["system"] = system

        if tools:
            params["tools"] = tools

        response = self.anthropic_client.messages.create(**params)

        # Track cost
        if settings.track_costs:
            cost = self._calculate_anthropic_cost(
                model, response.usage.input_tokens, response.usage.output_tokens
            )
            self.total_cost += cost
            logger.info(f"Request cost: ${cost:.4f} | Total: ${self.total_cost:.4f}")

        text_content = "".join(
            block.text for block in response.content
            if getattr(block, "type", None) == "text" and hasattr(block, "text")
        ) if response.content else ""

        return {
            "content": text_content,
            "tool_calls": [tc for tc in response.content if tc.type == "tool_use"] if tools else [],
            "_raw_content": list(response.content) if tools else [],
            "_provider": Provider.ANTHROPIC.value,
            "_model": model,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        }

    async def _openai_complete(
        self, messages: List[Dict], model: str, tools: Optional[List], stream: bool, **kwargs
    ) -> Dict[str, Any]:
        """OpenAI GPT completion"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        params = {
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", settings.max_tokens),
            "temperature": kwargs.get("temperature", settings.temperature),
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        response = self.openai_client.chat.completions.create(**params)
        choice = response.choices[0]

        # Track cost
        if settings.track_costs:
            cost = self._calculate_openai_cost(
                model, response.usage.prompt_tokens, response.usage.completion_tokens
            )
            self.total_cost += cost
            logger.info(f"Request cost: ${cost:.4f} | Total: ${self.total_cost:.4f}")

        return {
            "content": choice.message.content or "",
            "tool_calls": choice.message.tool_calls if tools and choice.message.tool_calls else [],
            "_provider": Provider.OPENAI.value,
            "_model": model,
            "stop_reason": choice.finish_reason,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
        }

    async def _ollama_complete(
        self, messages: List[Dict], model: str, tools: Optional[List], stream: bool, **kwargs
    ) -> Dict[str, Any]:
        """Ollama local model completion"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", settings.temperature),
                    }
                },
                timeout=120.0
            )

            if response.status_code != 200:
                raise ValueError(f"Ollama request failed: {response.text}")

            data = response.json()
            return {
                "content": data["message"]["content"],
                "tool_calls": [],
                "_provider": Provider.OLLAMA.value,
                "_model": model,
                "stop_reason": "stop",
                "usage": {
                    "input_tokens": 0,  # Ollama doesn't provide token counts
                    "output_tokens": 0,
                }
            }

    async def _openrouter_complete(
        self, messages: List[Dict], model: str, tools: Optional[List], stream: bool, **kwargs
    ) -> Dict[str, Any]:
        """OpenRouter completion (supports vision/multimodal models)"""
        if not settings.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured (set OPENROUTER_API_KEY)")

        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", settings.max_tokens),
            "temperature": kwargs.get("temperature", settings.temperature),
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json=params,
                timeout=60.0,
            )

            if response.status_code != 200:
                raise ValueError(f"OpenRouter request failed ({response.status_code}): {response.text}")

            data = response.json()
            choices = data.get("choices")
            if not choices:
                raise ValueError(f"OpenRouter returned no choices: {data}")
            choice = choices[0]
            usage = data.get("usage", {})

            # Track cost
            if settings.track_costs:
                cost = self._calculate_openrouter_cost(
                    model,
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0),
                )
                self.total_cost += cost
                logger.info(f"Request cost: ${cost:.4f} | Total: ${self.total_cost:.4f}")

            return {
                "content": choice["message"].get("content") or "",
                "tool_calls": choice["message"].get("tool_calls", []) if tools else [],
                "_provider": Provider.OPENROUTER.value,
                "_model": model,
                "stop_reason": choice.get("finish_reason", "stop"),
                "usage": {
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                },
            }

    async def _huggingface_complete(
        self, messages: List[Dict], model: str, tools: Optional[List], stream: bool, **kwargs
    ) -> Dict[str, Any]:
        """Hugging Face Inference API completion"""
        if not settings.huggingface_api_key:
            raise ValueError("Hugging Face API key not configured (set HUGGINGFACE_API_KEY)")

        # Hugging Face uses the OpenAI-compatible chat completions API
        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", settings.max_tokens),
            "temperature": kwargs.get("temperature", settings.temperature),
        }

        # Hugging Face Inference API supports tools for some models
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api-inference.huggingface.co/models/" + model + "/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.huggingface_api_key}",
                    "Content-Type": "application/json",
                },
                json=params,
                timeout=120.0,  # Longer timeout for potential cold starts
            )

            if response.status_code != 200:
                raise ValueError(f"Hugging Face request failed ({response.status_code}): {response.text}")

            data = response.json()
            choices = data.get("choices")
            if not choices:
                raise ValueError(f"Hugging Face returned no choices: {data}")
            choice = choices[0]
            usage = data.get("usage", {})

            # Track cost (Hugging Face is typically cheaper or free for some models)
            if settings.track_costs:
                cost = self._calculate_huggingface_cost(
                    model,
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0),
                )
                self.total_cost += cost
                logger.info(f"Request cost: ${cost:.4f} | Total: ${self.total_cost:.4f}")

            return {
                "content": choice["message"].get("content") or "",
                "tool_calls": choice["message"].get("tool_calls", []) if tools else [],
                "_provider": Provider.HUGGINGFACE.value,
                "_model": model,
                "stop_reason": choice.get("finish_reason", "stop"),
                "usage": {
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                },
            }

    async def _groq_complete(
        self, messages: List[Dict], model: str, tools: Optional[List], stream: bool, **kwargs
    ) -> Dict[str, Any]:
        """Groq completion via free_api_stack (fast Llama 3 inference)."""
        temperature = kwargs.get("temperature", settings.temperature)
        max_tokens = kwargs.get("max_tokens", settings.max_tokens)

        # Flatten messages to simple role/content dicts that groq_chat expects
        flat_messages = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                non_text = [b for b in content if isinstance(b, dict) and b.get("type") != "text"]
                if non_text:
                    logger.debug(f"Groq: dropping {len(non_text)} non-text content block(s) (unsupported)")
                content = " ".join(
                    block.get("text", "") for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            flat_messages.append({"role": msg["role"], "content": content})

        # groq_chat is synchronous; run in executor to avoid blocking the loop
        result_text = await asyncio.to_thread(
            free_api_stack.groq_chat,
            flat_messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if result_text is None:
            raise ValueError("Groq completion returned no result (check GROQ_API_KEY)")

        return {
            "content": result_text,
            "tool_calls": [],
            "_provider": Provider.GROQ.value,
            "_model": model,
            "stop_reason": "stop",
            "usage": {
                "input_tokens": 0,  # Groq free tier doesn't expose token counts
                "output_tokens": 0,
            },
        }

    def _calculate_anthropic_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate Anthropic API cost"""
        # Pricing as of 2026 (per million tokens)
        pricing = {
            "claude-opus-4-5": (15.0, 75.0),
            "claude-sonnet-4-5": (3.0, 15.0),
            "claude-haiku": (0.25, 1.25),
        }

        input_price, output_price = pricing.get(model, (3.0, 15.0))
        cost = (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
        return cost

    def _calculate_openai_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate OpenAI API cost"""
        # Pricing as of 2026 (per million tokens)
        pricing = {
            "gpt-4": (30.0, 60.0),
            "gpt-4-turbo": (10.0, 30.0),
            "gpt-3.5-turbo": (0.5, 1.5),
        }

        input_price, output_price = pricing.get(model, (10.0, 30.0))
        cost = (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
        return cost

    def _calculate_openrouter_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate OpenRouter API cost"""
        # Pricing per million tokens for common vision models
        pricing = {
            "google/gemini-flash-1.5-8b": (0.04, 0.04),
            "anthropic/claude-3-haiku": (0.25, 1.25),
            "google/gemini-pro-1.5": (1.25, 5.0),
            "anthropic/claude-3.5-sonnet": (3.0, 15.0),
        }

        input_price, output_price = pricing.get(model, (1.0, 3.0))
        cost = (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
        return cost

    def _calculate_huggingface_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate Hugging Face Inference API cost"""
        # Hugging Face Inference API pricing (per million tokens)
        # Many models are free or very low cost
        pricing = {
            "meta-llama/Llama-3.1-70B-Instruct": (0.0, 0.0),  # Free tier
            "meta-llama/Llama-3.1-8B-Instruct": (0.0, 0.0),   # Free tier
            "mistralai/Mistral-7B-Instruct-v0.3": (0.0, 0.0), # Free tier
            "Qwen/Qwen2.5-72B-Instruct": (0.0, 0.0),          # Free tier
            # Paid inference endpoints (example pricing)
            "meta-llama/Meta-Llama-3-70B": (0.65, 0.65),
            "mistralai/Mixtral-8x7B-Instruct-v0.1": (0.27, 0.27),
        }

        input_price, output_price = pricing.get(model, (0.0, 0.0))  # Default to free
        cost = (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
        return cost

    def get_total_cost(self) -> float:
        """Get total cost for session"""
        return self.total_cost

    def reset_cost(self):
        """Reset cost counter"""
        self.total_cost = 0.0

    async def vision_complete(
        self,
        messages: List[Dict],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Public entry point for vision/multimodal completions via OpenRouter.

        Args:
            messages: Multimodal messages (may include image_url content blocks)
            model: OpenRouter model ID (e.g. 'google/gemini-flash-1.5-8b')
            **kwargs: Additional parameters (max_tokens, temperature)

        Returns:
            Completion response dict with 'content', 'usage', etc.
        """
        return await self._openrouter_complete(messages, model, None, False, **kwargs)

    async def complete_with_tools(
        self,
        messages: List[Dict[str, str]],
        task_type: TaskType = TaskType.GENERAL,
        max_tool_rounds: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Complete with automatic tool execution loop

        Handles multi-turn tool use where the model requests tools,
        we execute them, and feed results back until completion.

        Args:
            messages: Conversation messages
            task_type: Type of task for model selection
            max_tool_rounds: Maximum tool execution iterations
            **kwargs: Additional parameters

        Returns:
            Final response after all tool executions
        """
        current_messages = messages.copy()
        tool_round = 0

        while tool_round < max_tool_rounds:
            # Get completion with tools enabled
            response = await self.complete(
                current_messages,
                task_type=task_type,
                enable_mcp_tools=True,
                **kwargs
            )

            # Check if model requested tools
            tool_calls = response.get("tool_calls", [])

            if not tool_calls:
                # No tools requested, return final response
                return response

            # Safety check: prevent runaway loops
            if tool_round >= max_tool_rounds - 1:
                logger.warning(f"Max tool rounds ({max_tool_rounds}) reached, returning current response")
                return response

            provider = response.get("_provider", Provider.ANTHROPIC.value)

            # Execute all requested tools, collecting results per call
            tool_results = []
            for tool_call in tool_calls:
                if provider == Provider.ANTHROPIC.value:
                    # Anthropic ToolUseBlock: .name, .input, .id
                    tool_name = tool_call.name
                    tool_args = tool_call.input
                    tool_call_id = tool_call.id
                else:
                    # OpenAI ChatCompletionMessageToolCall: .function.name/.arguments (JSON str), .id
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    tool_call_id = tool_call.id

                logger.info(f"Executing tool: {tool_name}")

                # Execute tool via MCP
                result = await mcp.execute_tool(tool_name, tool_args)

                result_content = result.data if result.success else f"Error: {result.error}"
                if isinstance(result_content, dict):
                    result_content = json.dumps(result_content)
                elif not isinstance(result_content, str):
                    result_content = str(result_content)

                tool_results.append({
                    "tool_call_id": tool_call_id,
                    "content": result_content,
                })

            # Build provider-specific follow-up messages
            if provider == Provider.ANTHROPIC.value:
                # Anthropic: replay original content blocks in assistant turn, then tool_result blocks in user turn
                current_messages.append({
                    "role": "assistant",
                    "content": response.get("_raw_content", []),
                })
                current_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tr["tool_call_id"],
                            "content": tr["content"],
                        }
                        for tr in tool_results
                    ],
                })
            else:
                # OpenAI: assistant message carries serialised tool_calls; one "tool" message per result
                current_messages.append({
                    "role": "assistant",
                    "content": response.get("content") or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                })
                for tr in tool_results:
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tr["tool_call_id"],
                        "content": tr["content"],
                    })

            tool_round += 1

        # Max rounds reached, return last response
        logger.warning(f"Max tool rounds ({max_tool_rounds}) reached")
        return response

# Global gateway instance
llm = LLMGateway()
