from typing import List, Optional, Tuple

import numpy as np
import requests
from scipy.io.wavfile import read as wav_read
from io import BytesIO

class Synthesizer:
    
    def generate_speech_audio(self, text: str) -> bytes:
        phonemes = self._phonemizer(text)
        audio = self.generate_audio_from_phonemes(phonemes)
        return audio

    def _phonemizer(self, text: str, language: str = "a") -> Tuple[str, List[int]]:
        """Get phonemes and tokens for input text using Kokoro FastAPI.

        Args:
        text: Input text to convert to phonemes
        language: Language code (defaults to "a" for American English)

        Returns:
        Tuple of (phonemes string, token list)
        """
        # Create the request payload
        payload = {"text": text, "language": language}

        # Make POST request to the phonemize endpoint
        response = requests.post("http://localhost:8880/text/phonemize", json=payload)

        # Raise exception for error status codes
        response.raise_for_status()

        # Parse the response
        result = response.json()
        return result["phonemes"]

    def generate_audio_from_phonemes(
        self, phonemes: str, voice: str = "af_bella", speed: float = 1.0
    ) -> Optional[np.ndarray]:
        """Generate audio from phonemes.

        Args:
            phonemes: Phoneme string to synthesize
            voice: Voice ID to use (defaults to af_bella)
            speed: Speed factor (defaults to 1.0)

        Returns:
            WAV audio bytes if successful, None if failed
        """
        # Create the request payload
        payload = {"phonemes": phonemes, "voice": voice, "speed": speed}
        #print("Sending payload:", payload)

        # Make POST request to generate audio
        response = requests.post(
            "http://localhost:8880/text/generate_from_phonemes", json=payload
        )

        # Raise exception for error status codes
        response.raise_for_status()

        # Decode the WAV bytes into a NumPy array
        audio_bytes = response.content
        sample_rate, audio_data = self._decode_wav_bytes(audio_bytes)

        return audio_data
    @staticmethod
    def _decode_wav_bytes(wav_bytes: bytes) -> Tuple[int, np.ndarray]:
        """Decode WAV bytes into a NumPy array.

        Args:
            wav_bytes: Raw WAV audio bytes.

        Returns:
            Tuple of (sample_rate, audio_data).
        """
        # Use BytesIO to treat the bytes as a file-like object
        with BytesIO(wav_bytes) as wav_file:
            sample_rate, audio_data = wav_read(wav_file)

        # Ensure the audio data is in the correct format (e.g., float32)
        audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max

        return sample_rate, audio_data