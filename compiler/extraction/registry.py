# pyrefly: ignore [missing-import]
from compiler.extraction.interface import ExtractionProvider
from compiler.extraction.gemini import GeminiProvider

class ProviderNotFoundError(Exception):
    pass

_PROVIDERS = {
    "gemini": GeminiProvider
}

def get_provider(name: str) -> ExtractionProvider:
    provider_cls = _PROVIDERS.get(name.lower())
    if not provider_cls:
        raise ProviderNotFoundError(f"Provider '{name}' not found.")
    return provider_cls()
