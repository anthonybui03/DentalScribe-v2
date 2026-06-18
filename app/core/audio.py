"""
Microphone capture using sounddevice.
Records into an in-memory buffer; raw audio is never written to disk
unless the user explicitly enables it in Settings.
"""
import io
import queue
import threading
import wave
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16_000   # Whisper expects 16 kHz
CHANNELS = 1
DTYPE = "int16"


def list_input_devices() -> list[dict]:
    """Return a list of available input devices."""
    devices = []
    for idx, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            devices.append({"index": idx, "name": dev["name"]})
    return devices


class AudioRecorder:
    """Thread-safe audio recorder that buffers frames in a queue."""

    def __init__(self, device_index: int | None = None):
        self.device_index = device_index
        self._q: queue.Queue[np.ndarray] = queue.Queue()
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self.is_recording = False

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        if status:
            print(f"[audio] stream status: {status}")
        self._q.put(indata.copy())

    def start(self) -> None:
        with self._lock:
            if self.is_recording:
                return
            self._frames.clear()
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                device=self.device_index,
                callback=self._callback,
            )
            self._stream.start()
            self.is_recording = True
            # Drain the queue into frames in a background thread.
            self._drain_thread = threading.Thread(target=self._drain, daemon=True)
            self._drain_thread.start()

    def _drain(self) -> None:
        while self.is_recording or not self._q.empty():
            try:
                chunk = self._q.get(timeout=0.1)
                self._frames.append(chunk)
            except queue.Empty:
                pass

    def get_snapshot(self) -> bytes:
        """Return WAV bytes of audio recorded so far without stopping."""
        with self._lock:
            frames = list(self._frames)
        # Also drain anything currently in the queue
        tmp = []
        while True:
            try:
                tmp.append(self._q.get_nowait())
            except queue.Empty:
                break
        frames.extend(tmp)
        if not frames:
            return b""
        audio_data = np.concatenate(frames, axis=0)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())
        return buf.getvalue()

    def stop(self) -> bytes:
        """Stop recording and return raw WAV bytes."""
        with self._lock:
            if not self.is_recording:
                return b""
            self.is_recording = False
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
        self._drain_thread.join(timeout=2)

        if not self._frames:
            return b""

        audio_data = np.concatenate(self._frames, axis=0)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # int16 = 2 bytes
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())
        return buf.getvalue()
