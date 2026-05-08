<div align="center">

# Music Production Ai MCP

**Music Production AI MCP Server**

[![PyPI](https://img.shields.io/pypi/v/meok-music-production-ai-mcp)](https://pypi.org/project/meok-music-production-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Music Production AI MCP Server
Audio and music tools powered by MEOK AI Labs.

## Tools

| Tool | Description |
|------|-------------|
| `generate_chord_progression` | Generate a chord progression in a given key and style. |
| `detect_tempo` | Detect tempo (BPM) from beat timestamps. |
| `find_key` | Detect the musical key from a set of notes. |
| `analyze_lyrics` | Analyze song lyrics for structure, rhyme scheme, syllable count, and themes. |
| `mixing_recommendations` | Get mixing and mastering recommendations for a multitrack session. |

## Installation

```bash
pip install meok-music-production-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "music-production-ai": {
      "command": "python",
      "args": ["-m", "meok_music_production_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 5 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
