# Music Production AI MCP

> Audio and music tools - chord progressions, tempo detection, key finding, lyric analysis, mixing recommendations

Built by **MEOK AI Labs** | [meok.ai](https://meok.ai)

## Features

| Tool | Description |
|------|-------------|
| `generate_chord_progression` | See tool docstring for details |
| `detect_tempo` | See tool docstring for details |
| `find_key` | See tool docstring for details |
| `analyze_lyrics` | See tool docstring for details |
| `mixing_recommendations` | See tool docstring for details |

## Installation

```bash
pip install mcp
```

## Usage

### As an MCP Server

```bash
python server.py
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "music-production-ai-mcp": {
      "command": "python",
      "args": ["/path/to/music-production-ai-mcp/server.py"]
    }
  }
}
```

## Rate Limits

Free tier includes **30-50 calls per tool per day**. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with FastMCP by MEOK AI Labs
