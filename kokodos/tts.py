from typing import List, Optional, Tuple

import numpy as np
import requests
from scipy.io.wavfile import read as wav_read
from io import BytesIO

class Synthesizer:
    def __init__(self, voice: str = "af_bella", api_base: str = "http://localhost:8880"):
        self.voice = voice
        self.api_base = api_base
        self.session = requests.Session()
    def generate_speech_audio(self, text: str) -> np.ndarray:
        phonemes_str, tokens = self._phonemizer(text)
        audio = self.generate_audio_from_phonemes(phonemes_str)
        return audio

    def _phonemizer(self, text: str, language: str = "a") -> Tuple[str, List[int]]:
        """Get phonemes and tokens for input text using Kokoro FastAPI."""
        payload = {"text": text, "language": language}
        url = f"{self.api_base}/dev/phonemize"
        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["phonemes"], result["tokens"]
        except requests.exceptions.RequestException as e:
            print(f"Phonemizer request failed: {e}")
            raise

    def generate_audio_from_phonemes(
        self, phonemes: str, voice: Optional[str] = None, speed: float = 1.0
    ) -> Optional[np.ndarray]:
        """Generate audio from phonemes."""
        voice = voice or self.voice
        payload = {"phonemes": phonemes, "voice": voice, "speed": speed}
        url = f"{self.api_base}/dev/generate_from_phonemes"
        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            sample_rate, audio_data = self._decode_wav_bytes(response.content)
            return audio_data
        except Exception as e:
            print.error(f"Audio generation failed: {e}")
            return None
    @staticmethod
    def _decode_wav_bytes(wav_bytes: bytes) -> Tuple[int, np.ndarray]:
        """Decode WAV bytes into a NumPy array."""
        try:
            with BytesIO(wav_bytes) as wav_file:
                sample_rate, audio_data = wav_read(wav_file)
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max
            return sample_rate, audio_data
        except Exception as e:
            print.error(f"WAV decoding failed: {e}")
            raise