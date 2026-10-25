import os
import uuid
import datetime
# pyrefly: ignore [missing-import]
from compiler.extraction.interface import ExtractionProvider, ExtractionPackage, ProviderResponse

class GeminiProvider:
    def extract(self, extraction_input: ExtractionPackage) -> ProviderResponse:
        execution_id = uuid.uuid4().hex
        executed_at = datetime.datetime.utcnow().isoformat()
        
        prompt = f"""
{extraction_input.extraction_instructions}

RESEARCH CONTEXT:
"""
        for doc in extraction_input.documents:
            prompt += f"\n{doc.numbered_content}\n"
            
        response = ProviderResponse(
            provider="gemini",
            model="gemini-2.5-pro",
            execution_id=execution_id,
            executed_at=executed_at,
            status="PROVIDER_EXECUTION_FAILED"
        )
        
        if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
            response.status = "EXTRACTION_NOT_AVAILABLE"
            response.warnings.append("API key not found. Gemini execution blocked.")
            return response
            
        try:
            from google import genai
            from google.genai import types
            from compiler.validation.models import InvestigationBrief
            
            client = genai.Client()
            api_response = client.models.generate_content(
                model=response.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=InvestigationBrief,
                    temperature=0.0
                ),
            )
            response.raw_response = api_response.text
            response.status = "SUCCESS"
            return response
        except Exception as e:
            response.status = "PROVIDER_EXECUTION_FAILED"
            response.warnings.append(str(e))
            return response
