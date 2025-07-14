from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import logging
import os
import json
from dotenv import load_dotenv
from datetime import datetime

from models.request_models import GenerateRequest
from models.response_models import GenerateResponse, HealthResponse, ErrorResponse
from services.llm_service import OllamaService
from services.logging_service import InteractionLogger

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MiniVault API",
    description="A lightweight local REST API that simulates ModelVault's core feature: receiving a prompt and returning a generated response using Ollama.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ollama_service = OllamaService()
interaction_logger = InteractionLogger()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting MiniVault API...")
    logger.info(f"Ollama URL: {ollama_service.base_url}")
    logger.info(f"Default model: {ollama_service.default_model}")
    
    # Check Ollama availability
    if ollama_service.is_available():
        models = ollama_service.get_available_models()
        logger.info(f"Ollama is available with models: {models}")
    else:
        logger.warning("Ollama service is not available - will use fallback responses")

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to MiniVault API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    ollama_available = ollama_service.is_available()
    available_models = ollama_service.get_available_models() if ollama_available else []
    
    return HealthResponse(
        status="healthy",
        ollama_status="connected" if ollama_available else "disconnected",
        timestamp=datetime.now(),
        available_models=available_models
    )

@app.post("/generate", tags=["Generation"])
async def generate_response(request: GenerateRequest):
    """
    Generate a response for the given prompt using Ollama.
    
    This endpoint:
    1. Accepts a prompt (and optional model name and streaming preference)
    2. Sends it to Ollama for generation
    3. Returns the generated response (streamed or complete)
    4. Logs the interaction to logs/log.jsonl
    """
    try:
        logger.info(f"Generating {'streaming' if request.stream else 'complete'} response for prompt: {request.prompt[:100]}...")
        
        if request.stream:
            # Return streaming response
            def generate_stream():
                full_response = ""
                model_name = ""
                start_time = datetime.now()
                
                try:
                    for chunk in ollama_service.generate_response_stream(
                        prompt=request.prompt,
                        model=request.model
                    ):
                        model_name = chunk.get("model", "")
                        
                        # Send each token as Server-Sent Event
                        if chunk.get("token"):
                            yield f"data: {json.dumps(chunk)}\n\n"
                            full_response += chunk["token"]
                        
                        # Send final chunk when done
                        if chunk.get("done"):
                            yield f"data: {json.dumps(chunk)}\n\n"
                            
                            # Log the complete interaction
                            end_time = datetime.now()
                            duration_ms = int((end_time - start_time).total_seconds() * 1000)
                            log_data = {
                                "response": full_response,
                                "model": model_name,
                                "timestamp": end_time,
                                "duration_ms": duration_ms,
                                "success": chunk.get("success", True),
                                "streaming": True
                            }
                            if not chunk.get("success"):
                                log_data["error_reason"] = chunk.get("error_reason", "Unknown error")
                            
                            interaction_logger.log_interaction(request.prompt, log_data)
                            break
                    
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"Error in streaming generation: {e}")
                    error_chunk = {
                        "token": "",
                        "model": model_name or "error",
                        "timestamp": datetime.now().isoformat(),
                        "done": True,
                        "success": False,
                        "error": str(e)
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
        
        else:
            # Generate complete response
            response_data = ollama_service.generate_response(
                prompt=request.prompt,
                model=request.model
            )
            
            # Log the interaction
            interaction_logger.log_interaction(request.prompt, response_data)
            
            # Return the response
            return GenerateResponse(
                response=response_data["response"],
                model=response_data["model"],
                timestamp=response_data["timestamp"]
            )
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        
        # Log the error interaction
        error_data = {
            "response": f"Internal server error: {str(e)}",
            "model": "error",
            "timestamp": datetime.now(),
            "duration_ms": 0,
            "success": False,
            "error_reason": str(e)
        }
        interaction_logger.log_interaction(request.prompt, error_data)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )

@app.get("/logs/recent", tags=["Logs"])
async def get_recent_logs(limit: int = 10):
    """Get recent interaction logs."""
    try:
        logs = interaction_logger.get_recent_logs(limit=limit)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Error retrieving logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve logs: {str(e)}"
        )

@app.get("/logs/stats", tags=["Logs"])
async def get_log_stats():
    """Get interaction statistics."""
    try:
        stats = interaction_logger.get_log_stats()
        return stats
    except Exception as e:
        logger.error(f"Error retrieving log stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve log stats: {str(e)}"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            timestamp=datetime.now()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.now()
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
