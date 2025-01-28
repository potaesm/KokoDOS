import cv2
import base64
import threading
import queue
import time
from loguru import logger

class VideoProcessor:
    def __init__(self, capture_fps=10, preview_fps=10):
        self.frames_queue = queue.Queue()
        self.recording = False
        self.cap = cv2.VideoCapture(0)
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 448) # This is more of a request to the driver. In most cases the webcam will still be capturing at its set resolution. Change the resolution in the driver/camera software to a res closest to 448x448. Resizing here would add latency.
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 448)
        self.cap.set(cv2.CAP_PROP_FPS, capture_fps)
        
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        logger.info(f"Camera running at {actual_fps} FPS. Setting capture to {capture_fps} FPS and preview to {preview_fps} FPS.")
        
        self.capture_interval = 1.0 / capture_fps
        self.preview_interval = 1.0 / preview_fps

        self.lock = threading.Lock()
        self.current_frames = []
        self.preview_queue = queue.Queue(maxsize=1)
        self.preview_active = True

        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()

        self.preview_thread = threading.Thread(target=self.preview_loop, daemon=True)
        self.preview_thread.start()

    def capture_loop(self):
        while True:
            start_time = time.time()
            
            ret, frame = self.cap.read()
            if not ret or frame is None:
                continue

            try:
                if self.preview_queue.full():
                    self.preview_queue.get_nowait()
                self.preview_queue.put_nowait(frame.copy())
            except queue.Empty:
                pass
            
            if self.recording:
                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                base64_frame = base64.b64encode(buffer).decode('utf-8')
                with self.lock:
                    self.current_frames.append(base64_frame)

            elapsed = time.time() - start_time
            sleep_time = max(0, self.capture_interval - elapsed)
            time.sleep(sleep_time)

    def preview_loop(self):
        while self.preview_active:
            loop_start = time.time()
            
            try:
                frame = self.preview_queue.get_nowait()
                cv2.imshow('Webcam Preview', frame)
            except queue.Empty:
                pass
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.preview_active = False
                break
                
            elapsed = time.time() - loop_start
            sleep_time = max(0, self.preview_interval - elapsed)
            time.sleep(sleep_time)

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
                    self.frames_queue.put(self.current_frames)
                    self.current_frames = []

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
        self.preview_thread.join(timeout=1)
        self.capture_thread.join(timeout=1)
        self.cap.release()
        cv2.destroyAllWindows()