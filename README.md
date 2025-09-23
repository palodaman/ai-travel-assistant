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
│   ├── gemini_agent.py        # Gemini AI integration with streaming
│   ├── agent_loop.py          # Agent loop system with ChooseToolResult
│   ├── security.py            # Security and rate limiting
│   ├── cache.py               # Redis caching utilities
│   ├── schemas.py             # Pydantic schemas
│   ├── tools/                 # Tool integrations
│   │   ├── __init__.py        # Tools module init
│   │   ├── weather.py         # Weather API integration (Open-Meteo)
│   │   ├── currency.py        # Currency conversion (ExchangeRate API)
│   │   ├── wikipedia.py       # Wikipedia search integration
│   │   └── utils.py           # Utility functions
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Backend container configuration
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js app router
│   │   │   ├── layout.tsx    # Root layout with dark mode
│   │   │   ├── page.tsx      # Home page
│   │   │   └── globals.css   # Global styles with Tailwind
│   │   ├── components/       # React components
│   │   │   └── ChatInterface.tsx  # Main chat UI with Lottie animations
│   │   └── lottie/           # Lottie animation files
│   │       ├── plane.json    # Animated plane icon
│   │       ├── rpa.json      # Bot avatar animation
│   │       └── user.json     # User avatar animation
│   ├── lib/
│   │   └── utils.ts          # Utility functions (cn helper)
│   ├── package.json          # Node dependencies
│   ├── tailwind.config.js    # Tailwind CSS configuration
│   ├── postcss.config.js     # PostCSS configuration
│   ├── next.config.ts        # Next.js configuration
│   └── Dockerfile             # Frontend container configuration
├── docker-compose.yml        # Docker orchestration
├── .env                      # Environment variables (create from .env.example)
├── .env.example              # Example environment variables
└── README.md                 # Project documentation
```

## API Endpoints

### Backend Endpoints

- `GET /healthz` - Health check
- `POST /chat` - Main chat endpoint (SSE streaming with agent loop)
- `POST /tools/weather` - Direct weather API
- `POST /tools/convert` - Direct currency conversion

## Agent Loop System

The AI Travel Assistant uses an intelligent agent loop system that:

### How It Works
1. **ChooseToolResult**: Analyzes the user query and decides which tool to call next
2. **Tool Execution**: Executes the chosen tool (weather, currency, wikipedia)
3. **Context Accumulation**: Builds up a comprehensive context with all results
4. **Loop Continue/Stop**: Repeats until all necessary information is gathered
5. **Synthesis**: Creates a natural response from the accumulated context

### Example Flow
User: "What's the weather in Paris and how much is 100 EUR in USD?"

```
1. Agent analyzes query → Decides to call weather tool
2. Calls weather(Paris) → Gets temperature, conditions
3. Analyzes remaining needs → Decides to call currency tool
4. Calls currency(100, EUR, USD) → Gets conversion rate
5. All info gathered → Calls STOP
6. Synthesizes natural response with all information
```

### Benefits
- **Intelligent Orchestration**: Automatically determines which tools to use
- **Complete Context**: Gathers all information before responding
- **Reasoning Trace**: Each tool call includes why it was needed
- **No Redundancy**: Avoids unnecessary repeated tool calls

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError in Docker**:
   - Rebuild containers: `docker-compose build --no-cache`

2. **CORS errors**:
   - Ensure frontend URL is in backend CORS settings
   - Check `FRONTEND_ORIGIN` in docker-compose.yml

3. **Port already in use**:
   - Change ports in docker-compose.yml
   - Or stop conflicting services

