#!/bin/bash
set -e

echo ""
echo "🎬 AI Content Pipeline — Setup Script"
echo "======================================"
echo ""

# 1. Check Docker
if ! command -v docker &> /dev/null; then
  echo "❌ Docker not found. Please install Docker Desktop first."
  exit 1
fi

# 2. Create .env if not exists
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "✅ .env created from .env.example"
  echo "⚠️  EDIT .env with your actual credentials before running!"
  echo ""
  echo "   Required:"
  echo "   - ANTHROPIC_API_KEY=sk-ant-..."
  echo "   - TWITTER_USERNAME=your_twitter_username"
  echo "   - TWITTER_PASSWORD=your_twitter_password"
  echo ""
else
  echo "✅ .env already exists"
fi

# 3. Build
echo "🔨 Building Docker images..."
docker compose build

echo ""
echo "✅ Build complete! Next steps:"
echo ""
echo "  1. Edit .env with your credentials"
echo "  2. Run:  make up"
echo "  3. Run:  make migrate"
echo "  4. Run:  make seed"
echo "  5. Open: http://localhost:3000"
echo ""
echo "📚 Full command list: make (or cat Makefile)"
