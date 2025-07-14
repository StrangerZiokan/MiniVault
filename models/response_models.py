from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GenerateResponse(BaseModel):
    """Response model for the /generate endpoint."""
    
    response: str = Field(
        ...,
        description="The generated response text",
        examples=["The capital of France is Paris."]
    )
    
    model: str = Field(
        ...,
        description="The model used for generation",
        examples=["llama2"]
    )
    
    timestamp: datetime = Field(
        ...,
        description="When the response was generated"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "response": "Quantum computing is a revolutionary technology that uses quantum mechanics principles to process information in ways that classical computers cannot.",
                "model": "llama2",
                "timestamp": "2024-01-15T10:30:00Z"
            }]
        }
    }


class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""
    
    status: str = Field(
        ...,
        description="API health status",
        examples=["healthy"]
    )
    
    ollama_status: str = Field(
        ...,
        description="Ollama service status",
        examples=["connected"]
    )
    
    timestamp: datetime = Field(
        ...,
        description="Health check timestamp"
    )
    
    available_models: Optional[List[str]] = Field(
        None,
        description="List of available Ollama models",
        examples=[["llama2", "codellama"]]
    )


class ErrorResponse(BaseModel):
    """Response model for error cases."""
    
    error: str = Field(
        ...,
        description="Error message",
        examples=["Ollama service is not available"]
    )
    
    detail: Optional[str] = Field(
        None,
        description="Additional error details",
        examples=["Connection refused to localhost:11434"]
    )
    
    timestamp: datetime = Field(
        ...,
        description="Error timestamp"
    )
