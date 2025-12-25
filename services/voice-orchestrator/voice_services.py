import abc
import time
import random

class ASRProvider(abc.ABC):
    @abc.abstractmethod
    def transcribe(self, audio_data) -> str:
        pass

class TTSProvider(abc.ABC):
    @abc.abstractmethod
    def speak(self, text: str) -> bytes:
        pass

class MockASR(ASRProvider):
    def transcribe(self, audio_data) -> str:
        # Simulate processing time
        time.sleep(0.5)
        # Return mock text based on "audio" (which we assume is just a string identifier in this prototype)
        if audio_data == "audio_sample_1":
            return "How do I reset my password?"
        elif audio_data == "audio_sample_2":
            return "I want to return an item."
        return "Hello, I need help."

class MockTTS(TTSProvider):
    def speak(self, text: str) -> bytes:
        # Simulate processing time
        time.sleep(0.5)
        # Return dummy bytes
        return b"mock_audio_bytes"

class VoiceServiceFactory:
    @staticmethod
    def get_asr(provider_name="local_whisper"):
        # In real impl, return WhisperASR() or CloudASR()
        return MockASR()

    @staticmethod
    def get_tts(provider_name="local_coqui"):
        # In real impl, return CoquiTTS() or PollyTTS()
        return MockTTS()
