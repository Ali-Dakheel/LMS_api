"""
Spaced Repetition System (SRS) - SM-2 Algorithm
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def calculate_srs_interval(
    ease_factor: float,
    interval: int,
    repetitions: int,
    quality: int
) -> Dict[str, Any]:
    """
    Calculate next SRS interval using SM-2 algorithm.
    
    Args:
        ease_factor: Current ease factor (1.3 - 2.5)
        interval: Current interval in days
        repetitions: Number of consecutive correct reviews
        quality: Review quality (0-5)
            0: Complete blackout
            1: Incorrect, but remembered
            2: Incorrect, easy to recall
            3: Correct, with difficulty
            4: Correct, with hesitation
            5: Perfect recall
    
    Returns:
        dict: {
            'ease_factor': float,
            'interval': int,
            'repetitions': int
        }
    """
    # If quality < 3, reset repetitions
    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        # Correct answer
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(interval * ease_factor)
        
        repetitions += 1
    
    # Update ease factor
    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    
    # Ensure ease factor stays within bounds
    if ease_factor < 1.3:
        ease_factor = 1.3
    elif ease_factor > 2.5:
        ease_factor = 2.5
    
    return {
        'ease_factor': round(ease_factor, 2),
        'interval': interval,
        'repetitions': repetitions
    }