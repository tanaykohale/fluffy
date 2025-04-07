import requests
import json
import asyncio
import aiohttp

class OllamaService:
    BASE_URL = "http://localhost:11434/api"

    def __init__(self, default_model=None):
        self.default_model = default_model
        self.available_models = self.get_available_models()

    def get_available_models(self):
        try:
            response = requests.get(f"{self.BASE_URL}/tags")
            models = [model['name'] for model in response.json().get('models', [])]
            return models if models else ["No models found"]
        except Exception as e:
            print(f"Error fetching models: {e}")
            return ["Error loading models"]

    async def generate_response_async(self, model, prompt, stream=False):
        """
        Async method for generating responses
        """
        url = f"{self.BASE_URL}/generate"
        data = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": stream
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if stream:
                        return self._stream_response(response)
                    else:
                        return await response.json()
        except Exception as e:
            print(f"Error generating response: {e}")
            return None

    def _stream_response(self, response):
        """
        Generator for streaming responses
        """
        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line.decode('utf-8'))
                    if 'response' in json_response:
                        yield json_response['response']
                    
                    if json_response.get('done', False):
                        break
                except Exception as e:
                    print(f"Error parsing response: {e}")
                    break

    def generate_response(self, model, prompt, stream=False):
        """
        Synchronous wrapper for async method
        """
        return asyncio.run(self.generate_response_async(model, prompt, stream))