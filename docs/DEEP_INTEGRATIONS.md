# Big Homie - Deep Integrations Guide

This guide covers all deep integrations available in Big Homie for Cloudflare, Vercel, Google Cloud, Perplexity, Stripe, Coinbase Commerce, Base Layer 2, DraftKings, and PrizePicks.

---

## 🎯 Overview

Big Homie now includes comprehensive integrations with major platforms across:
- **Cloud Infrastructure**: Cloudflare, Vercel, Google Cloud Platform
- **AI & Search**: Perplexity AI
- **Payments**: Stripe, Coinbase Commerce
- **Blockchain**: Base Layer 2 (Ethereum)
- **Sports Data**: DraftKings, PrizePicks

All integrations are accessible through the MCP (Model Context Protocol) tool system, allowing agents to autonomously interact with these services.

---

## 🔧 Configuration

### 1. Environment Variables

Add the following to your `.env` file:

```bash
# Cloudflare
CLOUDFLARE_API_TOKEN=your_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_ZONE_ID=your_zone_id
CLOUDFLARE_ENABLED=true

# Vercel
VERCEL_API_TOKEN=your_token_here
VERCEL_TEAM_ID=your_team_id
VERCEL_PROJECT_ID=your_project_id
VERCEL_ENABLED=true

# Google Cloud Platform
GOOGLE_CLOUD_PROJECT_ID=your_project_id
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=/path/to/service-account-key.json
GOOGLE_CLOUD_ENABLED=true

# Perplexity AI
PERPLEXITY_API_KEY=your_api_key
PERPLEXITY_ENABLED=true
PERPLEXITY_MODEL=llama-3.1-sonar-large-128k-online

# Stripe
STRIPE_API_KEY=your_secret_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret
STRIPE_ENABLED=true

# Coinbase Commerce
COINBASE_COMMERCE_API_KEY=your_api_key
COINBASE_COMMERCE_WEBHOOK_SECRET=your_webhook_secret
COINBASE_COMMERCE_ENABLED=true

# Base Layer 2
BASE_RPC_URL=https://mainnet.base.org
BASE_WALLET_ADDRESS=your_wallet_address
BASE_WALLET_PRIVATE_KEY=your_private_key  # Keep secure!
BASE_ENABLED=true

# DraftKings
DRAFTKINGS_API_KEY=your_api_key
DRAFTKINGS_ENABLED=true

# PrizePicks
PRIZEPICKS_API_KEY=your_api_key
PRIZEPICKS_ENABLED=true
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `cloudflare>=2.11.0` - Cloudflare API client
- `stripe>=5.5.0` - Stripe payment processing
- `web3>=6.0.0` - Ethereum/Base L2 blockchain
- `google-cloud-storage>=2.10.0` - Google Cloud Storage
- `google-cloud-bigquery>=3.11.0` - Google BigQuery

---

## 📚 Integration Details

### Cloudflare Integration

**Capabilities:**
- Deploy and manage Workers (serverless functions)
- KV namespace operations (key-value storage)
- R2 bucket operations (object storage)
- DNS record management
- Cache purging

**Available Tools:**
- `cloudflare_deploy_worker` - Deploy a Worker script
- `cloudflare_kv_write` - Write to KV storage
- `cloudflare_kv_read` - Read from KV storage

**Example Usage:**

```python
from llm_gateway import llm

# Deploy a Worker
response = await llm.complete_with_tools(
    messages=[{
        "role": "user",
        "content": """
        Deploy a Cloudflare Worker that responds with 'Hello World'.
        Name it 'hello-world-worker'.
        """
    }],
    max_tool_rounds=5
)
```

**Use Cases:**
- Deploy edge functions for low-latency APIs
- Store configuration in KV for global access
- Manage DNS records programmatically
- Purge CDN cache after deployments

---

### Vercel Integration

**Capabilities:**
- Create and manage deployments
- Environment variable management
- Deployment logs retrieval
- Project listing

**Available Tools:**
- `vercel_deploy` - Deploy a project
- `vercel_list_deployments` - List recent deployments

**Example Usage:**

```python
from llm_gateway import llm

# Deploy a Next.js app
response = await llm.complete_with_tools(
    messages=[{
        "role": "user",
        "content": """
        Deploy a simple Next.js landing page to Vercel.
        Include an index.js file with a React component.
        """
    }],
    max_tool_rounds=5
)
```

**Use Cases:**
- Automated deployments from CI/CD
- Preview deployments for testing
- Environment configuration automation
- Deployment monitoring and rollbacks

---

### Google Cloud Platform Integration

**Capabilities:**
- Cloud Storage (bucket operations, file uploads/downloads)
- BigQuery (SQL queries, dataset management)
- Complements existing Google Lyria (music generation)

**Available Tools:**
- `gcs_upload_file` - Upload to Cloud Storage
- `bigquery_query` - Execute BigQuery SQL

**Example Usage:**

```python
from llm_gateway import llm

# Run a BigQuery analysis
response = await llm.complete_with_tools(
    messages=[{
        "role": "user",
        "content": """
        Query BigQuery to get the top 10 products by sales
        from the dataset 'analytics.sales'.
        """
    }],
    max_tool_rounds=5
)
```

**Use Cases:**
- Data analytics and reporting
- Large-scale data processing
- File storage and distribution
- Integration with other Google services

---

### Perplexity AI Integration

**Capabilities:**
- Advanced AI search with citations
- Real-time information retrieval
- Multi-step reasoning searches
- Domain-specific research

**Available Tools:**
- `perplexity_search` - Search with Perplexity AI

**Example Usage:**

```python
from llm_gateway import llm

# Research using Perplexity
response = await llm.complete_with_tools(
    messages=[{
        "role": "user",
        "content": """
        Use Perplexity to research the latest developments
        in quantum computing for AI applications.
        """
    }],
    max_tool_rounds=5
)
```

**Use Cases:**
- Real-time research with citations
- Current events and news gathering
- Technical documentation lookup
- Competitive intelligence

---

### Stripe Integration

**Capabilities:**
- Customer management
- Payment intent creation and processing
- Subscription management
- Invoice handling

**Available Tools:**
- `stripe_create_customer` - Create a customer
- `stripe_create_payment_intent` - Create payment intent (requires confirmation)

**Example Usage:**

```python
from mcp_integration import mcp

# Create a customer
result = await mcp.execute_tool(
    "stripe_create_customer",
    {
        "email": "customer@example.com",
        "name": "John Doe"
    },
    context={"confirmed": True}
)
```

**Security Notes:**
- All financial operations require explicit confirmation
- Transactions are logged for audit trails
- Test mode recommended for development
- Use webhooks for payment status updates

**Use Cases:**
- E-commerce payment processing
- Subscription billing automation
- Invoice generation
- Customer account management

---

### Coinbase Commerce Integration

**Capabilities:**
- Cryptocurrency charge creation (BTC, ETH, USDC, etc.)
- Charge status monitoring
- Payment tracking
- Multi-currency support

**Available Tools:**
- `coinbase_create_charge` - Create a crypto charge (requires confirmation)

**Example Usage:**

```python
from mcp_integration import mcp

# Create a cryptocurrency charge
result = await mcp.execute_tool(
    "coinbase_create_charge",
    {
        "name": "Product Purchase",
        "description": "Premium subscription",
        "amount": "99.99",
        "currency": "USD"
    },
    context={"confirmed": True}
)
```

**Security Notes:**
- All transactions require explicit confirmation
- Supports multiple cryptocurrencies
- Webhook integration for payment confirmation
- Test mode available

**Use Cases:**
- Accept crypto payments
- International transactions
- Lower fee alternatives to credit cards
- Decentralized payment processing

---

### Base Layer 2 Integration

**Capabilities:**
- Wallet balance queries
- ETH transaction sending
- Gas price estimation
- Transaction monitoring
- Smart contract interactions

**Available Tools:**
- `base_get_balance` - Get ETH balance
- `base_send_transaction` - Send ETH (requires confirmation)

**Example Usage:**

```python
from mcp_integration import mcp

# Check balance
result = await mcp.execute_tool(
    "base_get_balance",
    {"address": "0x..."}
)

# Send ETH (requires confirmation)
result = await mcp.execute_tool(
    "base_send_transaction",
    {
        "to_address": "0x...",
        "amount_eth": 0.01
    },
    context={"confirmed": True}
)
```

**Security Notes:**
- Store private keys securely (e.g., a secrets manager or encrypted vault); do not store them in plain text in environment files
- All transactions require explicit confirmation
- Gas estimation provided before sending
- Transaction simulation recommended
- Use testnet for development

**Use Cases:**
- DeFi interactions
- NFT minting and transfers
- Smart contract deployment
- Token transfers
- On-chain data storage

---

### DraftKings Integration

**Capabilities:**
- Sports odds retrieval
- Contest listings
- Player statistics
- Live scoring data

**Available Tools:**
- `draftkings_get_odds` - Get sports odds (read-only)

**Example Usage:**

```python
from llm_gateway import llm

# Get NBA odds
response = await llm.complete_with_tools(
    messages=[{
        "role": "user",
        "content": """
        Get current NBA odds from DraftKings
        for tonight's games.
        """
    }],
    max_tool_rounds=5
)
```

**Important Notes:**
- **READ-ONLY**: No betting functionality
- Data for analysis and research only
- Respects responsible gaming guidelines

**Use Cases:**
- Sports analytics
- Odds comparison
- Player performance analysis
- Market research

---

### PrizePicks Integration

**Capabilities:**
- Player projection retrieval
- Contest data access
- Historical performance data
- Lineup analysis

**Available Tools:**
- `prizepicks_get_projections` - Get player projections (read-only)

**Example Usage:**

```python
from llm_gateway import llm

# Get NBA projections
response = await llm.complete_with_tools(
    messages=[{
        "role": "user",
        "content": """
        Get NBA player projections from PrizePicks
        and analyze the top 5 most favorable picks.
        """
    }],
    max_tool_rounds=5
)
```

**Important Notes:**
- **READ-ONLY**: No entry submission functionality
- Data for analysis and research only
- Educational purposes

**Use Cases:**
- Fantasy sports research
- Player performance analysis
- Projection modeling
- Statistical analysis

---

## 🔒 Security Best Practices

### API Key Management
- Store all keys in `.env` file (never commit to git)
- Use environment-specific keys (dev, staging, prod)
- Rotate keys regularly
- Monitor API usage for anomalies

### Financial Operations
- **Always** require explicit user confirmation
- Implement spending limits
- Log all transactions
- Use test/sandbox modes for development
- Verify webhook signatures

### Blockchain Operations
- Store private keys securely (e.g., a secrets manager or encrypted vault); do not store them in plain text in environment files
- Use hardware wallets for production
- Simulate transactions before executing
- Set gas price limits
- Monitor for suspicious activity

### Rate Limiting
- Respect API rate limits
- Implement exponential backoff
- Queue requests when necessary
- Monitor quota usage

---

## 📊 Cost Tracking

All integrations report costs through Big Homie's shared cost guard interface:

```python
from llm_gateway import llm
from cost_guards import cost_guard

# Use the shared cost guard interface exposed by Big Homie.
# Refer to cost_guard for the available budget enforcement
# and cost reporting helpers in your environment.
print(cost_guard)
```

**Budget Controls:**
- Set daily/monthly limits per integration
- Alerts at configurable thresholds
- Automatic shutdown when limits reached
- Cost estimation before expensive operations

---

## 🧪 Testing

### Using Test/Sandbox Modes

Most integrations support test modes:

```bash
# Stripe test mode
STRIPE_API_KEY=sk_test_...

# Base L2 testnet
BASE_RPC_URL=https://goerli.base.org

# Coinbase Commerce sandbox
COINBASE_COMMERCE_API_KEY=test_...
```

### Health Checks

All integrations include health check methods:

```python
from integrations import registry

# Check all integrations
health = await registry.health_check_all()
for name, status in health.items():
    print(f"{name}: {'✓' if status else '✗'}")
```

---

## 🎓 Usage Examples

### Example 1: Deploy Full-Stack App

```python
from llm_gateway import llm

response = await llm.complete_with_tools(
    messages=[{
        "role": "user",
        "content": """
        1. Deploy a Cloudflare Worker for the API backend
        2. Deploy the frontend to Vercel
        3. Set up Stripe for payments
        4. Configure DNS on Cloudflare
        """
    }],
    max_tool_rounds=20
)
```

### Example 2: Research & Data Analysis

```python
from llm_gateway import llm

response = await llm.complete_with_tools(
    messages=[{
        "role": "user",
        "content": """
        1. Use Perplexity to research AI market trends
        2. Store findings in Google Cloud Storage
        3. Run BigQuery analysis on historical data
        4. Generate summary report
        """
    }],
    max_tool_rounds=15
)
```

### Example 3: Crypto Payment Flow

```python
from llm_gateway import llm

response = await llm.complete_with_tools(
    messages=[{
        "role": "user",
        "content": """
        1. Create Coinbase Commerce charge for $100
        2. Monitor payment status
        3. On confirmation, record in database
        4. Send confirmation email
        """
    }],
    max_tool_rounds=10
)
```

### Example 4: Sports Analytics

```python
from llm_gateway import llm

response = await llm.complete_with_tools(
    messages=[{
        "role": "user",
        "content": """
        1. Get NBA odds from DraftKings
        2. Get player projections from PrizePicks
        3. Analyze discrepancies
        4. Generate betting strategy recommendations
        """
    }],
    max_tool_rounds=10
)
```

---

## 🚀 Advanced Usage

### Custom Agent Profiles

Create specialized agents for each integration:

```python
from agent_profiles import profile_manager

# DevOps Agent (Cloudflare + Vercel)
devops_agent = profile_manager.create_profile(
    name="DevOps Agent",
    role="Infrastructure management and deployment",
    system_prompt="You are an expert DevOps engineer...",
    tools_enabled=[
        "cloudflare_deploy_worker",
        "vercel_deploy",
        "cloudflare_kv_write"
    ]
)

# Financial Agent (Stripe + Coinbase)
financial_agent = profile_manager.create_profile(
    name="Financial Agent",
    role="Payment processing and financial operations",
    tools_enabled=[
        "stripe_create_customer",
        "stripe_create_payment_intent",
        "coinbase_create_charge"
    ]
)

# Analytics Agent (Perplexity + Google Cloud)
analytics_agent = profile_manager.create_profile(
    name="Analytics Agent",
    role="Research and data analysis",
    tools_enabled=[
        "perplexity_search",
        "bigquery_query",
        "gcs_upload_file"
    ]
)
```

### Workflow Automation

Combine multiple integrations in workflows:

```python
from sub_agents import orchestrator

result = await orchestrator.execute_task_with_sub_agents(
    task="""
    Complete e-commerce launch:
    1. Deploy API to Cloudflare Workers
    2. Deploy storefront to Vercel
    3. Set up Stripe payment processing
    4. Configure Coinbase Commerce for crypto
    5. Run analytics queries on BigQuery
    6. Generate launch report
    """,
    parallel=True
)
```

---

## 📖 API Reference

### Integration Registry

```python
from integrations import registry, IntegrationType

# Register custom integration
registry.register("my_service", my_integration, IntegrationType.CLOUD)

# Get integration
service = registry.get("my_service")

# Check status
status = registry.get_status("my_service")

# List all integrations
all_integrations = registry.list_integrations()
```

### Direct Integration Usage

```python
# Cloudflare
from integrations.cloudflare_integration import cloudflare
result = await cloudflare.deploy_worker(...)

# Vercel
from integrations.vercel_integration import vercel
result = await vercel.create_deployment(...)

# Stripe
from integrations.stripe_integration import stripe
result = await stripe.create_customer(...)

# Perplexity
from integrations.perplexity_integration import perplexity
result = await perplexity.search(...)

# Coinbase Commerce
from integrations.coinbase_commerce_integration import coinbase_commerce
result = await coinbase_commerce.create_charge(...)

# Base L2
from integrations.base_l2_integration import base_l2
result = await base_l2.get_balance(...)

# DraftKings
from integrations.draftkings_integration import draftkings
result = await draftkings.get_odds(...)

# PrizePicks
from integrations.prizepicks_integration import prizepicks
result = await prizepicks.get_projections(...)

# Google Cloud
from integrations.google_cloud_integration import google_cloud
result = await google_cloud.bigquery_query(...)
```

---

## 🤝 Contributing

To add new integrations:

1. Create integration module in `integrations/`
2. Implement health_check method
3. Add configuration to `config.py`
4. Register tools in `mcp_integration.py`
5. Update this documentation
6. Add tests

---

## 📝 License

See main LICENSE file

---

**Big Homie** - Deeply integrated with the platforms you use. 🏠
