# MiniVault API

A lightweight local REST API that simulates ModelVault's core feature: receiving a prompt and returning a generated response using Ollama for local LLM integration.

## 🚀 Quick Setup

### Prerequisites
- **Python 3.8+** and **Ollama** installed
- Install Ollama: Visit [ollama.ai](https://ollama.ai) → Start service: `ollama serve` → Pull model: `ollama pull llama2`

### Setup Steps
```bash
# 1. Clone and navigate
git clone <repository-url>
cd minivault-api

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the API
python app.py
```

**API available at:** `http://localhost:8000`

## 🎯 Design Choices & Tradeoffs

**Key Decisions:**
- **Local Ollama over Cloud APIs**: Prioritized privacy, offline capability, and no API costs over cloud convenience
- **Sync over Async**: Chose simplicity for demo purposes; async would improve concurrent request performance
- **JSONL file logging over Database**: Simpler setup and no external dependencies; database would scale better for production

## 🚀 Features

- **REST API** with POST `/generate` endpoint
- **Token-by-Token Streaming** for real-time response generation
- **Local LLM Integration** using Ollama
- **Comprehensive Logging** to `logs/log.jsonl`
- **Health Monitoring** with `/health` endpoint
- **Graceful Fallbacks** when Ollama is unavailable
- **Interactive CLI Tool** for easy testing
- **Automatic API Documentation** at `/docs`
- **Full Test Suite** with pytest
- **Postman Collection** for comprehensive API testing

## 📖 API Documentation

### Core Endpoint

#### POST `/generate`
Generate a response for a given prompt with optional streaming.

**Non-Streaming Request:**
```json
{
  "prompt": "Explain quantum computing in simple terms",
  "model": "llama2",  // optional
  "stream": false     // optional, defaults to false
}
```

**Non-Streaming Response:**
```json
{
  "response": "Quantum computing is a revolutionary technology...",
  "model": "llama2",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Streaming Request:**
```json
{
  "prompt": "Write a short story about AI",
  "model": "llama2",  // optional
  "stream": true      // enables token-by-token streaming
}
```

**Streaming Response:**
Server-Sent Events format with real-time token delivery:
```
data: {"token": "Once", "model": "llama2", "timestamp": "...", "done": false, "success": true}

data: {"token": " upon", "model": "llama2", "timestamp": "...", "done": false, "success": true}

data: {"token": " a", "model": "llama2", "timestamp": "...", "done": false, "success": true}

...

data: {"token": "", "model": "llama2", "timestamp": "...", "done": true, "success": true, "duration_ms": 1500, "full_response": "Once upon a time..."}

data: [DONE]
```

### Additional Endpoints

- **GET `/`** - API information
- **GET `/health`** - Health check and Ollama status
- **GET `/logs/recent?limit=10`** - Recent interaction logs
- **GET `/logs/stats`** - Interaction statistics
- **GET `/docs`** - Interactive API documentation

## 🧪 Testing

### Using the CLI Tool

The project includes a comprehensive CLI testing tool:

```bash
# Run full test suite
python cli_test.py

# Interactive mode
python cli_test.py --interactive

# Test specific functionality
python cli_test.py --health
python cli_test.py --prompt "Hello, world!"
python cli_test.py --logs
python cli_test.py --stats
```

### Using Postman Collection

Import the included Postman collection for comprehensive API testing:

1. **Import Collection**: Open Postman → Import → Select `MiniVault_API.postman_collection.json`
2. **Set Environment**: The collection uses `{{base_url}}` variable (defaults to `http://localhost:8000`)
3. **Test Categories**:
   - **Health & Info**: Basic API information and health checks
   - **Text Generation**: Both streaming and non-streaming examples
   - **Logging & Analytics**: Log retrieval and statistics
   - **Error Testing**: Validation and error handling tests
   - **Performance Testing**: Response time and load testing

**Key Features:**
- Pre-configured requests for all endpoints
- Streaming and non-streaming examples
- Automatic response validation tests
- Environment variables for easy configuration
- Performance timing tests

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Generate non-streaming response
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is artificial intelligence?", "stream": false}'

# Generate streaming response
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a haiku about programming", "stream": true}'

# Get recent logs
curl http://localhost:8000/logs/recent?limit=5
```

### Running Unit Tests

```bash
pytest tests/ -v
```

## 📁 Project Structure

```
minivault-api/
├── app.py                                    # Main FastAPI application
├── models/
│   ├── request_models.py                     # Pydantic request models
│   └── response_models.py                    # Pydantic response models
├── services/
│   ├── llm_service.py                        # Ollama integration service
│   └── logging_service.py                    # Interaction logging service
├── tests/
│   └── test_api.py                           # Comprehensive test suite
├── logs/
│   └── log.jsonl                             # Interaction logs (auto-created)
├── cli_test.py                               # CLI testing tool
├── MiniVault_API.postman_collection.json     # Postman collection for API testing
├── requirements.txt                          # Python dependencies
├── .env.example                             # Environment variables template
└── README.md                                # This file
```

## 🔧 Configuration

Environment variables (optional, with defaults):

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=30

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

## 📊 Logging

All interactions are logged to `logs/log.jsonl` in JSON Lines format:

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "prompt": "What is machine learning?",
  "response": "Machine learning is a subset of artificial intelligence...",
  "model": "llama2",
  "duration_ms": 1500,
  "success": true
}
```

## 🛡️ Error Handling

The API includes comprehensive error handling:

- **Ollama Unavailable**: Falls back to contextual stub responses
- **Model Not Found**: Automatically uses available models
- **Request Timeout**: Configurable timeout with fallback
- **Validation Errors**: Clear error messages for invalid requests
- **Server Errors**: Graceful error responses with logging

## 🚦 Health Monitoring

The `/health` endpoint provides:
- API status
- Ollama connection status
- Available models list
- Timestamp

## 🔄 Fallback Behavior

When Ollama is unavailable, the API provides intelligent fallback responses based on prompt content:

- Maintains API contract
- Logs fallback usage
- Provides helpful error context
- Continues to function for testing

## 🎯 Usage Examples

### Basic Usage
```python
import requests

response = requests.post("http://localhost:8000/generate", json={
    "prompt": "Explain the concept of recursion"
})
print(response.json()["response"])
```

### With Custom Model
```python
response = requests.post("http://localhost:8000/generate", json={
    "prompt": "Write a Python function to calculate fibonacci",
    "model": "codellama"
})
```

### Streaming Response
```python
import requests
import json

response = requests.post("http://localhost:8000/generate", json={
    "prompt": "Write a short story about a robot learning to paint",
    "stream": True
}, stream=True)

print("Streaming response:")
for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data_str = line[6:]  # Remove 'data: ' prefix
            if data_str == '[DONE]':
                break
            try:
                chunk = json.loads(data_str)
                if chunk.get('token'):
                    print(chunk['token'], end='', flush=True)
                elif chunk.get('done'):
                    print(f"\n\nCompleted in {chunk.get('duration_ms', 0)}ms")
            except json.JSONDecodeError:
                continue
```

### Async Streaming (using aiohttp)
```python
import aiohttp
import asyncio
import json

async def stream_response():
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/generate",
            json={
                "prompt": "Explain machine learning in detail",
                "stream": True
            }
        ) as response:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data_str = line[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data_str)
                        if chunk.get('token'):
                            print(chunk['token'], end='', flush=True)
                    except json.JSONDecodeError:
                        continue

# Run the async function
asyncio.run(stream_response())
```

## 🔍 Troubleshooting

### Common Issues

1. **"Ollama service unavailable"**
   - Ensure Ollama is running: `ollama serve`
   - Check if models are available: `ollama list`

2. **"No models available"**
   - Pull a model: `ollama pull llama2`
   - Verify model exists: `ollama list`

3. **Port already in use**
   - Change port in `.env`: `API_PORT=8001`
   - Or kill existing process: `lsof -ti:8000 | xargs kill`

4. **Import errors**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

### Logs and Debugging

- Check application logs in terminal output
- Review interaction logs in `logs/log.jsonl`
- Use `/logs/recent` endpoint for recent activity
- Enable debug logging: `LOG_LEVEL=DEBUG`

## 🚀 Future Enhancements

Potential improvements for production use:

- **Authentication**: API key or JWT-based auth
- **Rate Limiting**: Request throttling
- **Model Management**: Dynamic model loading/unloading
- **Metrics**: Prometheus/Grafana integration
- **Caching**: Response caching for common prompts
- **Database**: Persistent storage for logs and analytics
- **WebSocket Support**: Alternative to Server-Sent Events for streaming
- **Async Processing**: Full async/await implementation for better concurrency
- **Response Templates**: Configurable response formatting
- **Multi-model Support**: Parallel requests to multiple models

## 📝 Architecture Notes

### Design Decisions

1. **Modular Architecture**: Separate services for LLM and logging
2. **Graceful Degradation**: Fallback responses when Ollama unavailable
3. **Type Safety**: Full Pydantic validation for requests/responses
4. **Observability**: Comprehensive logging and health checks
5. **Developer Experience**: Auto-docs, CLI tools, clear error messages

### Trade-offs

- **Local vs Cloud**: Chose local Ollama for privacy and offline capability
- **Sync vs Async**: Used sync requests for simplicity (async could improve performance)
- **File vs Database**: Used JSONL files for simplicity (database would scale better)
- **Fallback Strategy**: Chose contextual responses over generic errors

## 📄 License

This project is created as a take-home assignment for ModelVault.

---

**Happy coding! 🎉**

For questions or issues, please refer to the troubleshooting section or check the logs.
