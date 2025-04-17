import asyncio
from dataclasses import dataclass
from typing import TypeVar, Callable, Awaitable, Any

T = TypeVar('T')

class RetryableError(Exception):
    """Base exception for errors that can be retried"""
    pass

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    initial_delay: float = 1.0
    max_delay: float = 60.0
    max_retries: int = 5
    backoff_factor: float = 2.0

class RetryHandler:
    """Handles retry logic for async operations"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    async def execute_with_retry(
        self, 
        operation: Callable[[], Awaitable[T]],
        on_retry: Callable[[int, float, Exception], Awaitable[None]] = None
    ) -> T:
        """
        Execute an async operation with retry logic
        
        Args:
            operation: The async operation to execute
            on_retry: Optional callback called before each retry attempt
            
        Returns:
            The result of the operation if successful
            
        Raises:
            RetryableError: If all retry attempts fail
        """
        retries = 0
        delay = self.config.initial_delay
        last_error = None
        
        while retries < self.config.max_retries:
            try:
                return await operation()
            except RetryableError as e:
                last_error = e
                retries += 1
                
                if on_retry:
                    await on_retry(retries, delay, e)
                
                if retries < self.config.max_retries:
                    await asyncio.sleep(delay)
                    delay = min(delay * self.config.backoff_factor, 
                              self.config.max_delay)
        
        raise RetryableError(
            f"Operation failed after {retries} retries. Last error: {str(last_error)}"
        ) 