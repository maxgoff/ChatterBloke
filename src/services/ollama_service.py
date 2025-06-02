"""Ollama service for LLM integration."""

import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx

from src.utils.config import get_settings


logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama LLM."""
    
    def __init__(self):
        """Initialize Ollama service."""
        self.settings = get_settings()
        self.base_url = self.settings.ollama_host
        self.default_model = self.settings.ollama_model
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(120.0)  # 2 minute timeout for LLM operations
        )
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        
    async def list_models(self) -> List[str]:
        """List available models from Ollama."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            # Return default models if Ollama is not available
            return [self.default_model, "llama2", "mistral", "codellama"]
            
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate text using Ollama."""
        model = model or self.default_model
        
        # Prepare the request
        request_data = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
            
        if max_tokens:
            request_data["options"] = {"num_predict": max_tokens}
            
        try:
            response = await self.client.post("/api/generate", json=request_data)
            response.raise_for_status()
            data = response.json()
            
            return {
                "response": data.get("response", ""),
                "model": model,
                "total_duration": data.get("total_duration", 0),
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "eval_count": data.get("eval_count", 0),
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Ollama API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Failed to generate with Ollama: {e}")
            raise Exception(f"Failed to generate text: {str(e)}")
            
    async def generate_script(
        self,
        prompt: str,
        script_type: str = "general",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a script based on prompt and type."""
        # Create a system prompt based on script type
        system_prompts = {
            "general": "You are a professional scriptwriter. Create engaging, well-structured scripts.",
            "presentation": "You are a presentation expert. Create clear, impactful presentation scripts with good pacing.",
            "video": "You are a video script specialist. Create scripts optimized for video content with visual cues.",
            "podcast": "You are a podcast scriptwriter. Create conversational, engaging audio scripts.",
            "educational": "You are an educational content creator. Create informative, clear teaching scripts.",
        }
        
        system_prompt = system_prompts.get(script_type, system_prompts["general"])
        
        # Enhance the user prompt
        enhanced_prompt = f"""Create a script based on the following request:

{prompt}

Requirements:
- Make it engaging and well-structured
- Include clear sections if appropriate
- Ensure good pacing for spoken delivery
- Make it suitable for teleprompter reading

Script:"""
        
        result = await self.generate(
            prompt=enhanced_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )
        
        return result["response"].strip()
        
    async def improve_script(
        self,
        script: str,
        instructions: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Improve an existing script based on instructions."""
        system_prompt = "You are a professional script editor. Improve scripts while maintaining their core message."
        
        prompt = f"""Please improve the following script based on these instructions:

Instructions: {instructions}

Original Script:
{script}

Improved Script:"""
        
        result = await self.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            system_prompt=system_prompt,
        )
        
        return result["response"].strip()
        
    async def check_grammar(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check grammar and suggest corrections."""
        system_prompt = "You are a grammar and style checker. Identify errors and suggest improvements."
        
        prompt = f"""Check the following text for grammar, spelling, and style issues:

{text}

Provide:
1. A list of issues found (if any)
2. The corrected version
3. Brief explanations for major changes

Format your response as:
ISSUES:
- Issue 1
- Issue 2

CORRECTED TEXT:
(the corrected version)

EXPLANATIONS:
(brief explanations if needed)"""
        
        result = await self.generate(
            prompt=prompt,
            model=model,
            temperature=0.3,  # Lower temperature for more consistent grammar checking
            system_prompt=system_prompt,
        )
        
        # Parse the response
        response_text = result["response"]
        sections = response_text.split("\n\n")
        
        issues = []
        corrected_text = text
        explanations = []
        
        current_section = ""
        for line in response_text.split("\n"):
            if line.startswith("ISSUES:"):
                current_section = "issues"
            elif line.startswith("CORRECTED TEXT:"):
                current_section = "corrected"
            elif line.startswith("EXPLANATIONS:"):
                current_section = "explanations"
            elif line.strip():
                if current_section == "issues" and line.startswith("-"):
                    issues.append(line[1:].strip())
                elif current_section == "corrected":
                    if corrected_text == text:  # First line of corrected text
                        corrected_text = line
                    else:
                        corrected_text += "\n" + line
                elif current_section == "explanations":
                    explanations.append(line)
                    
        return {
            "issues": issues,
            "corrected_text": corrected_text,
            "explanations": "\n".join(explanations),
            "has_issues": len(issues) > 0,
        }
        
    async def suggest_improvements(
        self,
        script: str,
        focus_areas: List[str] = None,
        model: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Suggest improvements for different aspects of the script."""
        if focus_areas is None:
            focus_areas = ["clarity", "engagement", "pacing", "structure"]
            
        suggestions = []
        
        for area in focus_areas:
            prompts = {
                "clarity": "How can this script be made clearer and easier to understand?",
                "engagement": "How can this script be more engaging and captivating?",
                "pacing": "How can the pacing and rhythm of this script be improved?",
                "structure": "How can the structure and organization be improved?",
                "conciseness": "How can this script be more concise without losing key information?",
                "tone": "How can the tone be adjusted to better suit the audience?",
            }
            
            if area not in prompts:
                continue
                
            prompt = f"""{prompts[area]}

Script:
{script}

Provide specific, actionable suggestions:"""
            
            try:
                result = await self.generate(
                    prompt=prompt,
                    model=model,
                    temperature=0.7,
                    system_prompt="You are a script consultant providing specific improvement suggestions.",
                )
                
                suggestions.append({
                    "area": area,
                    "suggestion": result["response"].strip(),
                })
            except Exception as e:
                logger.error(f"Failed to get suggestions for {area}: {e}")
                
        return suggestions


# Singleton instance
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """Get or create the Ollama service instance."""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service