# Big Homie 🏠

**The Agent That Works** - Your AI-powered multi-domain autonomous agent with a beautiful desktop UI.

![Big Homie](logo.png)

## Features

### 🎯 Multi-Domain Expertise
- **Finance & Trading** - Alpaca integration, portfolio analysis, market research
- **Software Development** - Code generation, debugging, refactoring with GitHub Copilot
- **Deep Research** - Multi-source analysis, report generation, fact-checking
- **Marketing & Content** - SEO optimization, content generation, campaign analysis
- **Web Automation** - Browser automation, scraping, testing with Playwright
- **Data Analysis** - Statistical analysis, visualization, insights

### 🧠 Advanced AI Capabilities
- **Multi-Provider LLM Support**
  - Anthropic Claude (Opus, Sonnet, Haiku)
  - OpenAI GPT-4 & GPT-3.5
  - OpenRouter (access to 100+ models)
  - Local models via Ollama
  - GitHub Copilot integration

- **Three-Layer Memory System**
  - Session Memory: Immediate conversation context
  - Long-term Memory: Facts, preferences, learned patterns
  - Skills Memory: Reusable workflows that improve over time

- **Self-Improving Agent**
  - Automatically creates skills from successful workflows
  - Learns user preferences and adapts communication style
  - Improves efficiency through repeated use

### 💰 Cost Optimization
- Real-time cost tracking per request
- Smart model routing (use cheapest suitable model)
- Cost alerts and session budgets
- Detailed cost breakdown by task

### 🎨 Modern Desktop UI
- Cross-platform (Windows, macOS, Linux)
- Dark theme optimized for long sessions
- Real-time chat interface
- Task history and analytics
- Skills management dashboard
- Settings and configuration panel

## Installation

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/tap919/Big-Homie.git
cd Big-Homie
```

2. **Set up environment**
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run Big Homie**
```bash
python main.py
```

### Building Executable

#### Windows
```bash
build.bat
# Executable will be in dist/BigHomie.exe
```

#### macOS / Linux
```bash
./build.sh
# Executable will be in dist/BigHomie or dist/BigHomie.app
```

## Configuration

### Required API Keys

At minimum, you need ONE of these:
- **Anthropic API Key** (recommended) - Get at: https://console.anthropic.com/
- **OpenAI API Key** - Get at: https://platform.openai.com/
- **OpenRouter API Key** - Get at: https://openrouter.ai/

### Optional Integrations

- **GitHub Copilot** - For enhanced coding capabilities
- **Ollama** - For local, offline AI (free, privacy-focused)
- **Alpaca** - For finance/trading features
- **SerpAPI** - For enhanced web search

### Configuration File

Edit `.env` to customize:
```bash
# LLM Provider Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-v1-...

# Model Selection
DEFAULT_MODEL=claude-sonnet-4-5
REASONING_MODEL=claude-opus-4-5
FAST_MODEL=claude-haiku
CODING_MODEL=gpt-4

# Agent Behavior
MAX_ITERATIONS=25
TEMPERATURE=0.7
MAX_TOKENS=4096

# Cost Controls
TRACK_COSTS=true
COST_ALERT_THRESHOLD=10.0
```

## Usage

### Basic Chat
1. Launch Big Homie
2. Type your question or task in the input field
3. Press Enter or click "Send"
4. Big Homie will process and respond

### Example Queries

**Finance**
```
Analyze NVDA stock performance over the last 30 days
```

**Coding**
```
Write a Python script to scrape product prices from an e-commerce site
```

**Research**
```
Research the latest developments in quantum computing and create a summary
```

**Marketing**
```
Generate 5 Instagram post ideas for a sustainable fashion brand
```

**Web Automation**
```
Navigate to tradingview.com and extract TSLA chart data
```

### Advanced Features

#### Skills Management
1. Go to "Skills" tab
2. View all learned workflows
3. Big Homie automatically creates skills from successful tasks
4. Skills improve with each use

#### History & Analytics
1. Go to "History" tab
2. View all past tasks with costs and durations
3. Export history to JSON for analysis

#### Cost Tracking
- Real-time cost display in header
- Alert when session cost exceeds threshold
- Detailed breakdown per task
- Reset counter anytime via Tools menu

## Architecture

### Core Components

```
Big-Homie/
├── main.py              # GUI application (PyQt6)
├── llm_gateway.py       # Multi-provider LLM interface
├── memory.py            # Three-layer memory system
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env                 # API keys and settings (create from .env.example)
└── logo.png            # Application logo
```

### Technology Stack

- **GUI**: PyQt6 (cross-platform desktop UI)
- **LLM Integration**: Anthropic SDK, OpenAI SDK, httpx
- **Memory**: SQLite with JSON storage
- **Configuration**: Pydantic with dotenv
- **Logging**: Loguru
- **Build**: PyInstaller (standalone executables)

## Development

### Running in Development Mode

```bash
# With debug logging
DEBUG=true python main.py
```

### Adding New Tools

1. Create tool module in `tools/` directory
2. Register in tool registry
3. Add tool description for LLM

### Adding New Models

Edit `llm_gateway.py` to add new providers:
```python
elif provider == Provider.NEW_PROVIDER:
    return await self._new_provider_complete(...)
```

## Troubleshooting

### "No API key configured"
- Make sure `.env` file exists with at least one valid API key
- Copy `.env.example` to `.env` and fill in your keys

### GUI doesn't start
- Install PyQt6: `pip install PyQt6`
- Check Python version (requires 3.9+)

### High API costs
- Adjust `COST_ALERT_THRESHOLD` in `.env`
- Use cheaper models (haiku, gpt-3.5-turbo)
- Enable Ollama for free local inference

### Building executable fails
- Install PyInstaller: `pip install pyinstaller`
- Make sure all dependencies are installed
- Try running from clean virtual environment

## Comparison to Other Agents

| Feature | Big Homie | OpenClaw | Hermes |
|---------|-----------|----------|--------|
| Desktop UI | ✅ Native | ❌ Web only | ❌ CLI only |
| Multi-Provider | ✅ 4+ providers | ❌ Single | ✅ Multiple |
| Cost Tracking | ✅ Real-time | ❌ No | ❌ No |
| Self-Learning | ✅ Skills system | ✅ Plugins | ✅ Skills |
| Offline Mode | ✅ Ollama | ❌ No | ✅ Local |
| Windows EXE | ✅ Yes | ❌ No | ❌ No |
| Memory System | ✅ 3-layer | ✅ Vector | ✅ Persistent |

## Roadmap

- [ ] MCP (Model Context Protocol) server integration
- [ ] Browser automation with Playwright
- [ ] Voice interface (TTS/STT)
- [ ] Mobile apps (iOS/Android)
- [ ] Multi-agent swarm coordination
- [ ] Plugin marketplace
- [ ] Cloud sync for memory
- [ ] Team collaboration features

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file

## Support

- GitHub Issues: https://github.com/tap919/Big-Homie/issues
- Documentation: Coming soon
- Discord: Coming soon

## Credits

Built with cutting-edge open source technology:
- Anthropic Claude
- OpenAI GPT
- PyQt6
- LangGraph concepts
- CrewAI patterns
- Hermes Agent inspiration

---

**Big Homie** - Because your AI agent should work as hard as you do. 🚀
