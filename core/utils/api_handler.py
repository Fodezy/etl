import time
import json
import hashlib
import logging
import random
from pathlib import Path
from typing import Callable, Any, Dict, Optional

# --- Configuration ---
logger = logging.getLogger(__name__)

CACHE_BASE_DIR = Path(__file__).resolve().parent.parent.parent / ".cache"
API_CACHE_DIR = CACHE_BASE_DIR / "api_results"
API_CACHE_DIR.mkdir(parents=True, exist_ok=True)

MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 2
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_COOLDOWN_SECONDS = 60


class CircuitBreaker:
    """A simple circuit breaker implementation to prevent hammering a failing API."""
    STATE_CLOSED = "CLOSED"
    STATE_OPEN = "OPEN"
    STATE_HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold: int, recovery_timeout: int):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = self.STATE_CLOSED
        self.failure_count = 0
        self.last_failure_time = 0

    def can_attempt(self) -> bool:
        """Determines if a request is allowed to proceed based on the circuit state."""
        if self.state == self.STATE_OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = self.STATE_HALF_OPEN
                logger.warning("Circuit Breaker state changed to HALF_OPEN. Allowing one test request.")
                return True
            logger.warning("Circuit Breaker is OPEN. Halting API call to allow service to recover.")
            return False
        return True

    def record_failure(self):
        """Records a failure and trips the breaker if the threshold is met."""
        self.failure_count += 1
        if self.state == self.STATE_HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.state = self.STATE_OPEN
            self.last_failure_time = time.time()
            logger.critical(f"Circuit Breaker TRIPPED to OPEN state for {self.recovery_timeout}s due to repeated failures.")

    def record_success(self):
        """Resets the breaker upon a successful call."""
        if self.state == self.STATE_HALF_OPEN:
            logger.info("Circuit Breaker reset to CLOSED state after successful test call.")
        self.state = self.STATE_CLOSED
        self.failure_count = 0

# --- The Main Handler Function ---

def handle_api_call(
    api_function: Callable[..., Any],
    payload: Dict[str, Any],
    circuit_breaker: CircuitBreaker,
    parser_name: str,
    item_id: str
) -> Optional[Any]:
    """
    A smart wrapper for API calls that handles caching, retries with exponential
    backoff, and a circuit breaker.
    """
    # --- UPDATED: Define cache_key and cache_file *before* the try block ---
    # This ensures cache_file is never unbound.
    try:
        payload_str = json.dumps(payload, sort_keys=True)
        cache_key = hashlib.md5(payload_str.encode('utf-8')).hexdigest()
        cache_file = API_CACHE_DIR / f"{cache_key}.json"
    except Exception as e:
        logger.error(f"[{parser_name}] Could not generate cache key for item '{item_id}': {e}", exc_info=True)
        # If we can't even generate a key, we can't safely cache. Fail this call.
        return None

    # 1. --- Persistent Caching Layer ---
    if cache_file.exists():
        try:
            logger.info(f"[{parser_name}] Cache HIT for item '{item_id}'. Loading from file.")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[{parser_name}] Cache read error for item '{item_id}': {e}", exc_info=True)

    logger.info(f"[{parser_name}] Cache MISS for item '{item_id}'. Proceeding to API call.")

    # 2. --- Circuit Breaker Check ---
    if not circuit_breaker.can_attempt():
        return None

    # 3. --- Retry Loop with Exponential Backoff ---
    for attempt in range(MAX_RETRIES):
        try:
            response = api_function(payload)
            
            circuit_breaker.record_success()
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2)
            logger.info(f"[{parser_name}] API call SUCCESS for item '{item_id}'. Result cached.")
            return response

        except Exception as e:
            logger.warning(
                f"[{parser_name}] API call FAILED for item '{item_id}' (Attempt {attempt + 1}/{MAX_RETRIES}). Error: {e}"
            )
            
            if attempt == MAX_RETRIES - 1:
                circuit_breaker.record_failure()
                logger.error(
                    f"[{parser_name}] API call PERMANENTLY FAILED for item '{item_id}' after {MAX_RETRIES} attempts.",
                )
                return None
            
            backoff_time = (INITIAL_BACKOFF_SECONDS ** attempt) + random.uniform(0, 1)
            logger.info(f"Retrying in {backoff_time:.2f} seconds...")
            time.sleep(backoff_time)
            
            # --- UPDATED: Replaced 'self' with the correct 'circuit_breaker' object ---
            if circuit_breaker.failure_count >= circuit_breaker.failure_threshold -1: # check if this next failure will trip it
                 circuit_breaker.record_failure()
                 if not circuit_breaker.can_attempt():
                     return None
    return None

# Standalone test block
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # Mock API function that sometimes fails
    def mock_api_call(payload: Dict[str, Any]) -> Dict[str, Any]:
        print(f"  ... Making mock API call with prompt: '{payload.get('prompt')}'")
        if random.random() < 0.6: # 60% chance of failure
            raise ConnectionError("Mock network error: Server unavailable")
        return {"result": f"Parsed result for: {payload.get('prompt')}"}

    print("\n" + "="*50)
    print("Running Standalone Test of API Handler")
    print("="*50 + "\n")

    test_cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10)
    
    test_prompts = [
        "1 of (A, B)",
        "1 of (A, B)", # Duplicate to test caching
        "1 of (C, D)",
        "1 of (E, F)",
        "1 of (G, H)",
    ]

    for i, prompt in enumerate(test_prompts):
        print(f"\n--- Processing Prompt #{i+1}: '{prompt}' ---")
        
        result = handle_api_call(
            api_function=mock_api_call,
            payload={"prompt": prompt},
            circuit_breaker=test_cb,
            parser_name="TEST_PARSER",
            item_id=f"TEST_{i}"
        )

        if result:
            print(f"--> FINAL RESULT: {result}")
        else:
            print("--> FINAL RESULT: None (call failed or circuit was open)")

    print("\n" + "="*50)
    print("Test Complete.")