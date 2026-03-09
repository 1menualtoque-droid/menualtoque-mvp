from google.auth.transport import requests
from google.oauth2 import id_token


class GoogleVerifierImpl:
    def __init__(self, client_id: str):
        self.client_id = client_id

    async def verify(self, idt: str) -> dict:
        # google API is sync; safe to run in a threadpool if needed
        payload = id_token.verify_oauth2_token(idt, requests.Request(), self.client_id)
        # Will raise on invalid
        return payload
