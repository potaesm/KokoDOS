import cv2
import base64
import threading
import queue
import time
from loguru import logger

class VideoProcessor:
    def __init__(self):
        self.frames_queue = queue.Queue()
        self.recording = False
        self.cap = cv2.VideoCapture(0)
        self.lock = threading.Lock()
        self.current_frames = []
        self.preview_lock = threading.Lock()
        self.last_frame = None
        self.preview_active = True

        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()

        self.preview_thread = threading.Thread(target=self.preview_loop, daemon=True)
        self.preview_thread.start()

    def capture_loop(self):
        while True:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                with self.preview_lock:
                    self.last_frame = frame.copy()

                if self.recording:
                    # Process frame for LLM
                    resized_frame = cv2.resize(frame, (448, 448))
                    _, buffer = cv2.imencode('.jpg', resized_frame)
                    base64_frame = base64.b64encode(buffer).decode('utf-8')
                    with self.lock:
                        self.current_frames.append(base64_frame)
                else:
                    with self.lock:
                        if self.current_frames:
                            self.frames_queue.put(self.current_frames.copy())
                            logger.debug(f"Queued {len(self.current_frames)} frames")
                            self.current_frames.clear()
            
            time.sleep(0.05)

    def preview_loop(self):
        while self.preview_active:
            with self.preview_lock:
                frame = self.last_frame.copy() if self.last_frame is not None else None

            if frame is not None:
                try:
                    cv2.putText(frame, "LIVE", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.imshow('Webcam Preview', frame)
                except Exception as e:
                    logger.error(f"Preview error: {e}")
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.preview_active = False
                break
            
            time.sleep(0.05)
        
        cv2.destroyAllWindows()

    def start_recording(self):
        if not self.recording:
            self.recording = True
            logger.debug("Started recording")

    def stop_recording(self):
        if self.recording:
            self.recording = False
            logger.debug("Stopped recording")
            with self.lock:
                if self.current_frames:
                    self.frames_queue.put(self.current_frames.copy())
                    self.current_frames.clear()

    def get_frames(self):
        try:
            frames = self.frames_queue.get(timeout=0.5)
            logger.debug(f"Retrieved {len(frames)} video frames from queue")
            return frames
        except queue.Empty:
            logger.warning("No video frames available in queue")
            return []

    def cleanup(self):
        self.preview_active = False
        self.capture_thread.join(timeout=1)
        self.preview_thread.join(timeout=1)
        self.cap.release()
        cv2.destroyAllWindows()