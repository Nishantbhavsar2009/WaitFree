import os
import json
import logging
from typing import Dict, Any, List
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("waitfree.gemini")

class GeminiClient:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables. Gemini calls will fail.")
        genai.configure(api_key=api_key)
        # We use gemini-1.5-flash as the fast, lightweight model for daily task breakdowns
        self.model_name = "gemini-1.5-flash"

    def decompose_task(self, task_name: str, duration_minutes: int = None) -> Dict[str, Any]:
        """
        Decomposes a daunting task into a list of 3-7 sub-2-minute steps.
        """
        duration_context = ""
        if duration_minutes:
            duration_context = f"The user has a hard deadline or event in {duration_minutes} minutes, so focus only on high-impact steps they can finish in this window to break their freeze."

        system_instruction = (
            "You are an expert ADHD coach and productivity specialist. Your goal is to help users overcome 'waiting mode' "
            "and severe task inertia/start resistance. You do this by breaking down a large, daunting task into exactly "
            "3 to 7 sequential steps.\n\n"
            "CRITICAL RULES FOR STEPS:\n"
            "1. Each step MUST be a physical, micro-action that takes less than 2 minutes (estimated_seconds must be <= 120).\n"
            "2. Steps must have extremely low cognitive load. Never use vague terms like 'organize', 'plan', or 'write'. Use specific physical cues (e.g. 'Open Google Docs and create a blank document named Cover Letter', 'Pick up exactly 3 items off the floor and put them on your bed').\n"
            "3. The steps must be sequential. Performing the first step should make the second step feel natural.\n"
            "4. Provide a supportive, brief explanation (one sentence) for each step that explains WHY it helps or HOW to do it easily to reduce starting friction.\n"
            f"{duration_context}"
        )

        prompt = (
            f"Break down this task: '{task_name}'\n\n"
            "Return a JSON object with this exact structure:\n"
            "{\n"
            '  "original_task": "Name of the task",\n'
            '  "steps": [\n'
            "    {\n"
            '      "title": "Actionable sub-2-minute title",\n'
            '      "estimated_seconds": 90,\n'
            '      "explanation": "Supportive sentence."\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        try:
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_instruction
            )
            
            # Use structured output configuration
            generation_config = {
                "response_mime_type": "application/json",
                "temperature": 0.2,
            }
            
            logger.info(f"Sending task decomposition request for: {task_name}")
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            response_text = response.text.strip()
            # Parse the JSON response
            data = json.loads(response_text)
            
            # Validate and clean output to ensure safety limits
            if "steps" not in data or not isinstance(data["steps"], list):
                raise ValueError("Response missing steps array")
                
            clean_steps = []
            for step in data["steps"][:7]: # Limit to 7 steps max
                title = step.get("title", "Micro task")
                estimated_seconds = step.get("estimated_seconds", 90)
                # Hard limit to 2 minutes
                if not isinstance(estimated_seconds, int) or estimated_seconds > 120 or estimated_seconds <= 0:
                    estimated_seconds = 90
                
                explanation = step.get("explanation", "Just take the first action.")
                clean_steps.append({
                    "title": title,
                    "estimated_seconds": estimated_seconds,
                    "explanation": explanation
                })
                
            return {
                "original_task": data.get("original_task", task_name),
                "steps": clean_steps
            }

        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            # Fallback static steps in case of API issues
            return {
                "original_task": task_name,
                "steps": [
                    {
                        "title": f"Open your workspace or get ready to start {task_name}",
                        "estimated_seconds": 60,
                        "explanation": "Preparing your physical environment is the easiest way to break inertia."
                    },
                    {
                        "title": "Do the absolute smallest action related to the task for 60 seconds",
                        "estimated_seconds": 60,
                        "explanation": "Just set a timer for 1 minute and do any action. No pressure to finish."
                    },
                    {
                        "title": "Check in with yourself and decide if you want to keep going",
                        "estimated_seconds": 30,
                        "explanation": "Often, starting is the hardest part. You have already broken the freeze!"
                    }
                ]
            }
