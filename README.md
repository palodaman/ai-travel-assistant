# AI Travel Assistant

An intelligent travel companion powered by Google's Gemini AI that provides real-time weather updates, currency conversion, and comprehensive travel information through a beautiful, modern interface.

## Features

- **Weather Information**: Get current weather conditions for any city worldwide with location disambiguation
- **Currency Conversion**: Real-time currency exchange rates for travel budgeting
- **Wikipedia Integration**: Access comprehensive information about destinations, attractions, and cultural insights
- **Agent Loop System**: Intelligent multi-step reasoning that orchestrates tools automatically
- **Smart Context**: AI remembers conversation context for personalized assistance
- **Real-time Streaming**: See AI responses as they're generated with animated Lottie icons

## Tech Stack 

### Backend
- **Flask** - Python web framework
- **Google Gemini AI** - Advanced AI model for natural language processing
- **Redis** - Caching for API responses
- **Tool Integrations**:
  - Open-Meteo API for weather data
  - ExchangeRate API for currency conversion
  - Wikipedia API for travel information

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling

## Prerequisites 

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.10+ (for local development)
- API Keys (see Environment Setup)

## Environment Setup 

Create a `.env` file in the root directory:

```env
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key_here
EXCHANGERATE_API_KEY=your_exchangerate_api_key_here
```

### Getting API Keys:

1. **Gemini API Key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add to `.env` file

2. **ExchangeRate API Key**:
   - Visit [ExchangeRate-API](https://app.exchangerate-api.com/sign-up)
   - Sign up for free account
   - Get your API key
   - Add to `.env` file

## Quick Start with Docker 

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/ai-travel-assistant.git
cd ai-travel-assistant
```

2. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run with Docker Compose**:
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001

## Local Development Setup

### Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Create virtual environment on mac**:
```bash
python -m venv venv
source venv/bin/activate 
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the backend**:
```bash
python app.py
```

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Run the development server**:
```bash
npm run dev
```

### Redis Setup (for caching)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine
```

## Project Structure

```
ai-travel-assistant/
├── backend/
│   ├── app.py                 # Flask application entry point
│   ├── gemini_agent.py        # Gemini AI integration
│   ├── security.py            # Security and rate limiting
│   ├── cache.py               # Redis caching utilities
│   ├── schemas.py             # Pydantic schemas
│   ├── tools/                 # Tool integrations
│   │   ├── weather.py         # Weather API integration
│   │   ├── currency.py        # Currency conversion
│   │   ├── wikipedia.py       # Wikipedia search
│   │   └── utils.py           # Utility functions
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js app router
│   │   │   ├── layout.tsx    # Root layout
│   │   │   ├── page.tsx      # Home page
│   │   │   └── globals.css   # Global styles
│   │   └── components/       # React components
│   │       └── ChatInterface.tsx  # Main chat UI
│   ├── lib/
│   │   └── utils.ts          # Utility functions
│   ├── package.json          # Node dependencies
│   ├── tailwind.config.js    # Tailwind configuration
│   ├── postcss.config.js     # PostCSS configuration
│   └── Dockerfile
├── docker-compose.yml        # Docker orchestration
└── .env                      # Environment variables
```

## API Endpoints

### Backend Endpoints

- `GET /healthz` - Health check
- `POST /chat` - Main chat endpoint (SSE streaming)
- `POST /tools/weather` - Direct weather API
- `POST /tools/convert` - Direct currency conversion


### Common Issues

1. **ModuleNotFoundError in Docker**:
   - Rebuild containers: `docker-compose build --no-cache`

2. **CORS errors**:
   - Ensure frontend URL is in backend CORS settings
   - Check `FRONTEND_ORIGIN` in docker-compose.yml

3. **Port already in use**:
   - Change ports in docker-compose.yml
   - Or stop conflicting services

