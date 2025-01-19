"""OpenAI-based LLM service implementation"""
import json
import asyncio
from typing import Dict, Optional
from functools import lru_cache
import logging
from debate_system.moderator import InteractionObserver
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from debate_system.protocols import (
    DebateRound,
    GameMemory,
    LLMServiceProtocol,
    LLMContext,
    InferenceResult,
    LLMConfig,
    GameMoment,
    InteractionType,
    PsychologicalState
)

logger = logging.getLogger(__name__)

class LLMService(LLMServiceProtocol):
    """OpenAI-based LLM service implementation"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI()
        self._token_usage = 0
        self._cache: Dict[str, InferenceResult] = {}
        
    @lru_cache(maxsize=1000)
    def _get_cache_key(self, prompt: str, context: LLMContext) -> str:
        """Generate a cache key from prompt and relevant context"""
        # Only include stable/relevant context elements in cache key
        context_dict = {
            "game_state": context.game_state.fen,
            "affected_pieces": sorted(context.affected_pieces),
            "interaction_type": context.interaction_type.value if context.interaction_type else None
        }
        return f"{prompt}::{json.dumps(context_dict, sort_keys=True)}"
    
    async def _make_api_call(self, prompt: str, context: LLMContext) -> ChatCompletion:
        """Make the actual API call with retries"""
        for attempt in range(self.config.retry_attempts):
            try:
                response = await self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": "You are a chess piece with a unique personality, participating in a game where pieces debate their moves."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout_seconds
                )
                return response
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    logger.error(f"Failed all retry attempts for LLM API call: {str(e)}")
                    raise
                logger.warning(f"Retry {attempt + 1} after error: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _process_response(self, response: ChatCompletion) -> InferenceResult:
        """Process API response into InferenceResult"""
        content = response.choices[0].message.content
        
        # Calculate confidence based on response metadata
        # This is a simplified example - you might want more sophisticated confidence calculation
        confidence = 1.0 if response.choices[0].finish_reason == "stop" else 0.5
        
        # Track token usage
        self._token_usage += response.usage.total_tokens
        
        return InferenceResult(
            content=content,
            confidence=confidence,
            token_usage=response.usage.total_tokens,
            metadata={
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "created": response.created
            },
            cached=False
        )
    
    async def infer(self, prompt: str, context: LLMContext) -> InferenceResult:
        """Main inference method"""
        # Check cache if enabled
        if self.config.cache_enabled:
            cache_key = self._get_cache_key(prompt, context)
            if cache_key in self._cache:
                cached_result = self._cache[cache_key]
                cached_result.cached = True
                return cached_result
        
        try:
            response = await self._make_api_call(prompt, context)
            result = self._process_response(response)
            
            # Cache result if enabled
            if self.config.cache_enabled:
                cache_key = self._get_cache_key(prompt, context)
                self._cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            # Return a graceful fallback result
            return InferenceResult(
                content="I apologize, but I am unable to process this request at the moment.",
                confidence=0.0,
                token_usage=0,
                metadata={"error": str(e)},
                cached=False
            )
    
    def get_token_usage(self) -> int:
        """Get total token usage"""
        return self._token_usage
    
    def clear_cache(self) -> None:
        """Clear the inference cache"""
        self._cache.clear()
        self._get_cache_key.cache_clear()  # Clear the LRU cache

class BatchLLMService(LLMService):
    """Extension of LLMService that supports batched operations"""
    
    async def batch_infer(self, prompts: list[tuple[str, LLMContext]]) -> list[InferenceResult]:
        """Process multiple inferences in parallel"""
        if not prompts:
            return []
            
        # Split into batches
        batch_size = self.config.batch_size
        batches = [prompts[i:i + batch_size] for i in range(0, len(prompts), batch_size)]
        
        all_results = []
        for batch in batches:
            # Process each batch in parallel
            tasks = [self.infer(prompt, context) for prompt, context in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions in the batch
            processed_results = []
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch processing: {str(result)}")
                    processed_results.append(InferenceResult(
                        content="Batch processing error occurred.",
                        confidence=0.0,
                        token_usage=0,
                        metadata={"error": str(result)},
                        cached=False
                    ))
                else:
                    processed_results.append(result)
            
            all_results.extend(processed_results)
        
        return all_results 

class LLMInferenceObserver(InteractionObserver):
    def __init__(self, service: LLMService, game_memory: GameMemory, psychological_state: PsychologicalState):
        self.service = service
        self.game_memory = game_memory
        self.psychological_state = psychological_state
        
    async def on_game_moment(self, moment: GameMoment):
        """Route game moments to appropriate inference type"""
        context = LLMContext(
            game_state=moment.position,
            psychological_state=moment.impact,
            affected_pieces=moment.participants,
            interaction_type=moment.interaction_type
        )
        
        # Route to character inference for emotional/psychological events
        if moment.interaction_type in [InteractionType.TRAUMA, InteractionType.THREAT]:
            await self._handle_character_inference(moment, context)
            
        # Route to narrative inference for significant game moments
        if moment.is_significant():  # We can define what makes a moment "significant"
            await self._handle_narrative_inference(moment, context)

    async def on_relationship_change(self, piece1: str, piece2: str, change: float):
        """Route relationship changes to appropriate inference type"""
        if abs(change) > 0.3:  # Significant relationship change
            context = LLMContext(
                game_state=self.game_memory.current_position,
                affected_pieces=[piece1, piece2],
                interaction_type=InteractionType.RELATIONSHIP
            )
            await self._handle_narrative_inference(
                pieces=(piece1, piece2),
                relationship_change=change,
                context=context
            )

    async def on_debate_round(self, debate: DebateRound):
        """Route debate events to debate inference"""
        context = LLMContext(
            game_state=debate.position,
            affected_pieces=[p.piece_id for p in debate.participants],
            interaction_type=InteractionType.DEBATE
        )
        await self._handle_debate_inference(debate, context)

    # Private handlers that will eventually use our inference protocols
    async def _handle_character_inference(self, moment: GameMoment, context: LLMContext):
        """Handle character-based inference"""
        await self.service.infer(
            self._build_character_prompt(moment),
            context
        )

    async def _handle_debate_inference(self, debate: DebateRound, context: LLMContext):
        """Handle debate-based inference"""
        await self.service.infer(
            self._build_debate_prompt(debate),
            context
        )

    async def _handle_narrative_inference(self, *args, context: LLMContext):
        """Handle narrative-based inference"""
        await self.service.infer(
            self._build_narrative_prompt(*args),
            context
        )