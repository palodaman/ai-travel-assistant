# AI Travel Assistant

An intelligent travel companion powered by Google's Gemini AI that provides real-time weather updates, currency conversion, and comprehensive travel information through a beautiful, modern interface.

## Features

- **Weather Information**: Get current weather conditions for any city worldwide with location disambiguation
- **Currency Conversion**: Real-time currency exchange rates for travel budgeting
- **Wikipedia Integration**: Access comprehensive information about destinations, attractions, and cultural insights
- **Agent Loop System**: Intelligent multi-step reasoning that orchestrates tools automatically with authentic thinking display
- **Smart Context**: AI remembers conversation context for personalized assistance
- **Real-time Streaming**: See AI responses as they're generated with animated Lottie icons
- **Transparent Reasoning**: Watch the AI's actual thought process as it analyzes your query
- **Nginx Gateway**: Production-ready reverse proxy architecture for all services
- **Docker Orchestration**: Complete containerized setup with automatic service discovery

## Tech Stack

### Backend
- **Flask** - Python web framework
- **Google Gemini AI** - Advanced AI model for natural language processing
- **Redis** - Caching for API responses
- **Nginx** - Reverse proxy and API gateway
- **Tool Integrations**:
  - Open-Meteo API for weather data
  - ExchangeRate API for currency conversion
  - Wikipedia API for travel information

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
### Infrastructure
- **Docker & Docker Compose** - Container orchestration
- **Nginx** - Load balancing and reverse proxy
- **Redis** - In-memory caching

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

3. **Build and run with Docker Compose**:
```bash
docker-compose up --build
```

4. **Access the application**:
- Frontend: http://localhost:3000
- API Gateway (Nginx): http://localhost:8080
- Backend (Direct): http://localhost:5001 (for development only)

**Note**: The frontend communicates with the backend through Nginx on port 8080, which provides reverse proxy capabilities and can be configured for load balancing.

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
│   ├── agent_loop.py          # Agent loop with authentic reasoning
│   ├── security.py            # Security and rate limiting
│   ├── cache.py               # Redis caching utilities
│   ├── schemas.py             # Pydantic schemas
│   ├── tools/                 # Tool integrations
│   │   ├── __init__.py        # Tools module init
│   │   ├── weather.py         # Weather API integration (Open-Meteo)
│   │   ├── currency.py        # Currency conversion (ExchangeRate API)
│   │   ├── wikipedia.py       # Wikipedia search integration
│   │   └── utils.py           # Utility functions
│   ├── nginx/                 # Nginx reverse proxy configuration
│   │   ├── nginx.conf         # Nginx configuration file
│   │   ├── Dockerfile         # Nginx container configuration
│   │   └── html/              # Static HTML files for testing
│   │       └── test.html      # Test page
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Backend container configuration
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js app router
│   │   │   ├── layout.tsx    # Root layout with dark mode
│   │   │   ├── page.tsx      # Home page
│   │   │   └── globals.css   # Global styles with Tailwind
│   │   ├── components/       # React components
│   │   │   └── ChatInterface.tsx  # Chat UI with thinking display
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

The AI Travel Assistant uses an intelligent agent loop system with authentic reasoning display:

### How It Works
1. **ChooseToolResult**: Analyzes the user query with genuine thinking process
2. **Reasoning Display**: Shows actual AI thought process, not generic messages
3. **Tool Execution**: Executes the chosen tool (weather, currency, wikipedia)
4. **Context Accumulation**: Builds up a comprehensive context with all results
5. **Loop Continue/Stop**: Repeats until all necessary information is gathered
6. **Synthesis**: Creates a natural response from the accumulated context

### Example Flow
User: "What's the weather in Paris and how much is 100 EUR in USD?"

```
1. Agent thinks: "I need to check the weather in Paris to answer their travel question"
   → Calls weather(Paris) → Gets temperature, conditions

2. Agent thinks: "Now I need to convert EUR to USD for their budget planning"
   → Calls currency(100, EUR, USD) → Gets conversion rate

3. Agent thinks: "I have the weather and currency data they requested"
   → Calls STOP → Synthesizes natural response
```

### Thinking Display
Users can see the AI's actual reasoning process:
- "Checking current weather conditions in Paris for trip planning"
- "Converting currency to help with budget calculations"
- "Looking up tourist attractions they mentioned"

### Benefits
- **Intelligent Orchestration**: Automatically determines which tools to use
- **Complete Context**: Gathers all information before responding
- **Transparent Reasoning**: Shows genuine AI thought process, not generic messages
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

4. **Frontend not using Nginx gateway**:
   - Rebuild frontend with correct env: `docker-compose build frontend`
   - Ensure `NEXT_PUBLIC_BACKEND_URL` is set at build time
   - Check that requests go to port 8080, not 5001

