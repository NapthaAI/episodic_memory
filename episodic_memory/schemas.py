from pydantic import BaseModel, Field
from typing import Union, Dict, Any, List, Optional

class InputSchema(BaseModel):
    func_name: str
    func_input_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]], str]] = None

class CognitiveStep(BaseModel):
    """
    A single step stored *inside* an EpisodicMemoryObject.
    """
    step_type: str = Field(..., description="Type of cognitive step (e.g., 'perception')")
    content: Dict[str, Any] = Field(..., description="Content of the step")

class EpisodicMemoryObject(BaseModel):
    """
    An entire 'episode' of task execution. 
    It aggregates multiple steps (CognitiveStep),
    plus optional fields like total_reward, strategy_update, etc.
    """
    memory_id: str = None
    agent_id: str
    task_query: str
    cognitive_steps: List[CognitiveStep] = Field(default_factory=list)
    total_reward: Optional[float] = None
    strategy_update: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    created_at: str = None
    metadata: Optional[Dict[str, Any]] = None
    similarity: Optional[float] = None