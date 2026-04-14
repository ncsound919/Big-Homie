"""
Big Homie Configuration
Centralized configuration management with environment variable support
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings with validation"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # Application Info
    app_name: str = "Big Homie"
    app_version: str = "1.0.0"
    debug: bool = False

    # LLM Providers
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""

    # Default Models
    default_model: str = "claude-sonnet-4-5"
    reasoning_model: str = "claude-opus-4-5"
    fast_model: str = "claude-haiku"
    coding_model: str = "gpt-4"

    # Local Models (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_enabled: bool = False

    # Hugging Face Inference
    huggingface_api_key: str = ""
    huggingface_enabled: bool = False
    huggingface_default_model: str = "meta-llama/Llama-3.1-70B-Instruct"

    # GitHub Copilot
    github_token: str = ""
    copilot_enabled: bool = False

    # Memory
    memory_db_path: str = str(Path.home() / ".big_homie" / "memory.db")
    vector_db_dir: str = str(Path.home() / ".big_homie" / "vector_db")

    # API Services
    serp_api_key: str = ""

    # Finance (Alpaca)
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"

    # Server
    server_host: str = "127.0.0.1"
    server_port: int = 9000
    orchestrator_secret: str = "change-me-in-production"

    # UI Settings
    ui_theme: str = "dark"
    ui_font_size: int = 12

    # Agent Settings
    max_iterations: int = 25
    temperature: float = 0.7
    max_tokens: int = 4096

    # Cost Tracking
    track_costs: bool = True
    cost_alert_threshold: float = 10.0  # USD
    spend_warning_threshold: float = 0.25  # Warn before requests projected to exceed this amount

    # Heartbeat / Autonomous
    heartbeat_enabled: bool = True
    heartbeat_interval: int = 45  # minutes
    max_autonomous_cost: float = 5.0  # USD per day
    quiet_hours_start: str = "23:00"
    quiet_hours_end: str = "06:00"

    # Sub-Agents
    enable_sub_agents: bool = True
    max_parallel_sub_agents: int = 3

    # Self-Improvement
    daily_log_review: bool = True
    log_review_time: str = "03:00"  # 3 AM daily review

    # Cognitive Core (Tier 1)
    default_reasoning_strategy: str = "auto"  # auto, cot, react, tot, cot_sc
    max_reasoning_steps: int = 10
    tree_of_thought_branches: int = 3
    tree_of_thought_depth: int = 3
    self_consistency_samples: int = 3

    # Context Window Manager (Tier 2)
    max_context_tokens: int = 100000
    context_reserve_tokens: int = 4096
    context_compression_enabled: bool = True

    # Document Intelligence (Tier 3)
    enable_document_intelligence: bool = True
    max_document_size_mb: int = 50

    # Environment Sensing (Tier 3)
    enable_environment_monitoring: bool = True
    environment_monitor_interval: int = 60  # seconds

    # Database Operations (Tier 4)
    enable_database_ops: bool = True

    # Swarm Intelligence (Tier 5)
    enable_swarm: bool = True
    swarm_max_agents: int = 6
    swarm_consensus_required: bool = False

    # Autonomous Loop (Tier 6)
    autonomous_loop_max_iterations: int = 10
    evaluator_quality_threshold: float = 0.85
    evaluator_max_cycles: int = 3

    # Skill Acquisition (Tier 6)
    enable_skill_learning: bool = True

    # RL Feedback (Tier 6)
    enable_rl_feedback: bool = True

    # ============================================================
    # Karpathy LLM Methods (Tier 6.5)
    # Advanced inference-time compute techniques
    # ============================================================
    enable_karpathy_methods: bool = True

    # Temperature Calibration
    karpathy_temperature_calibration: bool = True  # Auto-tune temperature per task
    karpathy_temp_factual: float = 0.0             # Deterministic (math, facts)
    karpathy_temp_analytical: float = 0.2          # Structured (code, logic)
    karpathy_temp_balanced: float = 0.5            # Mixed (Q&A, summarization)
    karpathy_temp_creative: float = 0.9            # Open-ended (brainstorm)
    karpathy_temp_exploratory: float = 1.0         # Maximum diversity

    # Scratchpad Reasoning
    karpathy_scratchpad_enabled: bool = True        # Private thinking before answering
    karpathy_scratchpad_show_to_user: bool = False  # Whether to expose scratchpad

    # Best-of-N Sampling
    karpathy_best_of_n: int = 3           # Number of drafts to generate
    karpathy_bon_temperature: float = 0.7  # Temperature for draft generation
    karpathy_bon_enabled: bool = True

    # Few-Shot Library
    karpathy_few_shot_enabled: bool = True
    karpathy_few_shot_k: int = 3  # Examples to retrieve per query

    # Process Reward Model
    karpathy_prm_enabled: bool = True
    karpathy_prm_threshold: float = 0.6  # Min step score to pass

    # Self-Play Debate
    karpathy_debate_enabled: bool = True
    karpathy_debate_rounds: int = 2  # Debate rounds before verdict

    # Constitutional Review
    karpathy_constitutional_enabled: bool = True
    karpathy_constitutional_max_revisions: int = 2

    # KAIROS - Persistent Autonomous Daemon (Tier 7)
    kairos_enabled: bool = True
    kairos_idle_threshold_seconds: int = 300  # 5 minutes idle = background mode
    kairos_consolidation_interval_seconds: int = 3600  # Consolidate memory every hour when idle
    kairos_max_background_cost_per_hour: float = 1.0  # USD limit for background operations
    kairos_max_concurrent_tasks: int = 3
    kairos_enable_proactive_tasks: bool = True

    # ULTRAPLAN - Complex Planning System (Tier 7)
    ultraplan_enabled: bool = True
    ultraplan_max_session_duration_seconds: int = 1800  # 30 minutes max
    ultraplan_checkpoint_interval_seconds: int = 300  # Checkpoint every 5 minutes
    ultraplan_cost_limit_per_plan: float = 5.0  # USD
    ultraplan_quality_threshold: float = 0.8
    ultraplan_enable_cloud_offload: bool = True

    # autoDream - Memory Consolidation System (Tier 7)
    dream_system_enabled: bool = True
    dream_hours_start: str = "02:00"  # 2 AM
    dream_hours_end: str = "05:00"  # 5 AM
    dream_min_idle_minutes: int = 30  # Min idle time before dreaming
    dream_consolidation_threshold: int = 100  # Min memories before consolidation
    dream_max_memories_per_cycle: int = 500
    dream_importance_decay_rate: float = 0.1  # Per day decay for unused memories
    dream_enable_knowledge_graph: bool = True

    # Enhanced Multi-Agent Coordination (Tier 7)
    enhanced_orchestrator_enabled: bool = True
    orchestrator_max_parallel_workers: int = 10
    orchestrator_health_check_interval: int = 60  # seconds
    orchestrator_failover_threshold: int = 3  # consecutive failures
    orchestrator_enable_channels: bool = True

    # Governance (Tier 7)
    enable_human_gate: bool = True
    enable_audit_trail: bool = True
    enable_sandbox: bool = True
    enable_kill_switch: bool = True
    sandbox_timeout_seconds: int = 30
    sandbox_max_memory_mb: int = 512
    auto_approve_low_risk: bool = True

    # Vision & Multimodal
    enable_vision: bool = True
    vision_model: str = "google/gemini-flash-1.5-8b"  # Cost-effective default
    auto_screenshot_on_error: bool = True
    optimize_images_before_upload: bool = True
    use_local_ocr: bool = True  # Try local OCR before API

    # Cost Guards
    enable_cost_guards: bool = True
    cost_approval_threshold: float = 0.50  # Require approval for ops > $0.50
    daily_token_cap: int = 1_000_000  # 1M tokens per day max
    cost_warning_threshold: float = 0.75  # Warn at 75% of budget
    auto_approve_under: float = 0.10  # Auto-approve ops under $0.10

    # Thought Logging & Observability
    enable_thought_logging: bool = True
    thought_log_detail_level: int = 2  # 0=off, 1=minimal, 2=normal, 3=verbose
    log_model_selections: bool = True
    log_cost_decisions: bool = True

    # Multi-Channel Integration
    enable_discord: bool = False
    discord_webhook_url: str = ""
    enable_slack: bool = False
    slack_webhook_url: str = ""

    # Database Connectors (Zero-Copy)
    postgres_url: str = ""
    supabase_url: str = ""
    supabase_key: str = ""

    # Media Generation
    enable_media_generation: bool = True

    # Google Lyria (Music Generation)
    google_lyria_api_key: str = ""
    google_lyria_enabled: bool = False

    # MiniMax (Music/Video Generation)
    minimax_api_key: str = ""
    minimax_group_id: str = ""
    minimax_enabled: bool = False

    # ComfyUI (Image/Video/Music Generation)
    comfyui_enabled: bool = False
    comfyui_base_url: str = "http://localhost:8188"
    comfyui_cloud_api_key: str = ""  # For Comfy Cloud
    comfyui_use_cloud: bool = False
    comfyui_default_workflow: str = "default"

    # Media Generation Settings
    media_output_dir: str = str(Path.home() / ".big_homie" / "media_outputs")
    max_media_generation_time: int = 300  # 5 minutes timeout
    enable_async_media_tasks: bool = True

    # Cloudflare Integration
    cloudflare_api_token: str = ""
    cloudflare_account_id: str = ""
    cloudflare_zone_id: str = ""
    cloudflare_enabled: bool = False

    # Vercel Integration
    vercel_api_token: str = ""
    vercel_team_id: str = ""
    vercel_project_id: str = ""
    vercel_enabled: bool = False

    # Google Cloud Platform
    google_cloud_project_id: str = ""
    google_service_account_key_path: str = ""
    google_cloud_enabled: bool = False

    # Perplexity AI
    perplexity_api_key: str = ""
    perplexity_enabled: bool = False
    perplexity_model: str = "llama-3.1-sonar-large-128k-online"

    # Stripe Payments
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_enabled: bool = False

    # Coinbase Commerce
    coinbase_commerce_api_key: str = ""
    coinbase_commerce_webhook_secret: str = ""
    coinbase_commerce_enabled: bool = False

    # Base Layer 2 (Ethereum)
    base_rpc_url: str = "https://mainnet.base.org"
    base_wallet_address: str = ""
    base_wallet_private_key: str = ""
    base_enabled: bool = False

    # DraftKings API
    draftkings_api_key: str = ""
    draftkings_enabled: bool = False

    # PrizePicks API
    prizepicks_api_key: str = ""
    prizepicks_enabled: bool = False

    # ============================================================
    # REVENUE ENGINE - Financial Integrations
    # ============================================================

    # ---- Banking (Plaid) ----
    plaid_client_id: str = ""
    plaid_secret: str = ""
    plaid_env: str = "sandbox"  # sandbox | development | production
    plaid_enabled: bool = False

    # ---- Crypto Exchanges ----
    # Binance
    binance_api_key: str = ""
    binance_secret_key: str = ""
    binance_testnet: bool = True
    binance_enabled: bool = False

    # Kraken
    kraken_api_key: str = ""
    kraken_private_key: str = ""
    kraken_enabled: bool = False

    # Coinbase Advanced Trade
    coinbase_adv_api_key: str = ""
    coinbase_adv_secret: str = ""
    coinbase_adv_enabled: bool = False

    # ---- Options / Stock Brokers ----
    # Interactive Brokers (IBKR)
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 7497          # 7497=paper, 7496=live
    ibkr_client_id: int = 1
    ibkr_enabled: bool = False

    # Schwab (TD Ameritrade successor)
    schwab_client_id: str = ""
    schwab_client_secret: str = ""
    schwab_redirect_uri: str = "https://127.0.0.1"
    schwab_enabled: bool = False

    # ---- Sports Betting ----
    # FanDuel
    fanduel_api_key: str = ""
    fanduel_enabled: bool = False

    # The Odds API (aggregated betting lines)
    odds_api_key: str = ""
    odds_api_enabled: bool = False

    # ---- Job / Gig / Task Platforms ----
    # Upwork
    upwork_client_id: str = ""
    upwork_client_secret: str = ""
    upwork_enabled: bool = False

    # Fiverr
    fiverr_api_key: str = ""
    fiverr_enabled: bool = False

    # Amazon Mechanical Turk
    mturk_access_key: str = ""
    mturk_secret_key: str = ""
    mturk_sandbox: bool = True
    mturk_enabled: bool = False

    # ---- Ecommerce / SaaS ----
    # Shopify
    shopify_shop_domain: str = ""   # e.g. my-store.myshopify.com
    shopify_access_token: str = ""
    shopify_enabled: bool = False

    # WooCommerce
    woocommerce_url: str = ""
    woocommerce_consumer_key: str = ""
    woocommerce_consumer_secret: str = ""
    woocommerce_enabled: bool = False

    # Amazon Seller / SP-API
    amazon_seller_id: str = ""
    amazon_mws_auth_token: str = ""
    amazon_sp_refresh_token: str = ""
    amazon_sp_client_id: str = ""
    amazon_sp_client_secret: str = ""
    amazon_sp_enabled: bool = False

    # ---- Supply Chain / Logistics ----
    # ShipStation
    shipstation_api_key: str = ""
    shipstation_api_secret: str = ""
    shipstation_enabled: bool = False

    # EasyPost
    easypost_api_key: str = ""
    easypost_enabled: bool = False

    # ---- Call Center / Telephony ----
    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_enabled: bool = False

    # ---- MCP (Model Context Protocol) Servers ----
    mcp_server_urls: str = ""      # Comma-separated list of MCP server endpoints
    mcp_auth_tokens: str = ""      # Matching comma-separated auth tokens
    mcp_enabled: bool = False

    # ---- Revenue Engine Settings ----
    revenue_engine_enabled: bool = True
    revenue_goal_daily_usd: float = 0.0        # Target daily revenue (0 = no goal)
    revenue_goal_monthly_usd: float = 0.0      # Target monthly revenue
    revenue_auto_reinvest_pct: float = 0.0     # Auto-reinvest % of profits (0–100)
    revenue_max_single_trade_usd: float = 100.0  # Cap per automated trade / bet
    revenue_risk_level: str = "low"            # low | medium | high
    revenue_active_streams: str = ""           # Comma-sep: trading,betting,freelance,ecommerce
    revenue_report_interval_hours: int = 24    # How often to emit a revenue report

    # ---- SaaS / MaaS Deployment ----
    saas_deploy_enabled: bool = False
    saas_stripe_price_id: str = ""             # Default Stripe price for SaaS subscriptions
    saas_trial_days: int = 14
    maas_model_endpoint: str = ""             # URL of deployed model/API
    maas_api_key_header: str = "X-API-Key"   # Auth header name for MaaS endpoint

    def _normalize_path(self, path_value: str) -> Path:
        """Normalize configured filesystem paths."""
        return Path(os.path.expanduser(path_value)).resolve()

    @property
    def data_dir(self) -> Path:
        """Get data directory"""
        return self._normalize_path(self.memory_db_path).parent

    def ensure_dirs(self):
        """Ensure necessary directories exist"""
        data_dir = self.data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "logs").mkdir(exist_ok=True)
        self._normalize_path(self.vector_db_dir).mkdir(parents=True, exist_ok=True)
        (data_dir / "screenshots").mkdir(exist_ok=True)
        self._normalize_path(self.media_output_dir).mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()
settings.ensure_dirs()
