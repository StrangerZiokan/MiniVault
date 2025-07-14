from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    """Request model for the /generate endpoint."""
    
    prompt: str = Field(
        ...,
        description="The input prompt to generate a response for",
        min_length=1,
        max_length=10000,
        examples=["What is the capital of France?"]
    )
    
    model: Optional[str] = Field(
        None,
        description="Optional model name to use for generation",
        examples=["llama2"]
    )
    
    stream: Optional[bool] = Field(
        False,
        description="Whether to stream the response token-by-token",
        examples=[True, False]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "prompt": "Explain quantum computing in simple terms",
                "stream": False
            }]
        }
    }
