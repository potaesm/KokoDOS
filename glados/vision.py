import platform
import pyautogui
from PIL import ImageGrab, Image
import base64
import io
import subprocess
import time
import tkinter as tk
import keyboard
import threading

class Vision:
    def __init__(self):
        self.latest_screenshot = None
        self.screenshot_lock = threading.Lock()

    def draw_rectangle(self, root, canvas, left, top, width, height):
        """
        Updates the rectangle on the screen using a tkinter overlay.
        """
        # Clear the canvas
        canvas.delete("all")

        # Draw the rectangle
        canvas.create_rectangle(0, 0, width, height, outline="red", width=2)

        # Move the overlay window to the new position
        root.geometry(f"{width}x{height}+{left}+{top}")

        # Update the window
        root.update()

    def capture_around_cursor(self, left, top, right, bottom):
        """
        Captures a screenshot within the specified bounding box.
        Returns the screenshot as a base64-encoded string.
        """
        system = platform.system()
        if system == "Windows":
            # Use ImageGrab on Windows
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        elif system == "Linux":
            # Use scrot on Linux
            try:
                subprocess.run(["scrot", "-o", "screenshot.png"])
                screenshot = Image.open("screenshot.png").crop((left, top, right, bottom))
            except FileNotFoundError:
                raise Exception("scrot is not installed. Please install scrot to capture screenshots on Linux.")
        elif system == "Darwin":
            # Use screencapture on macOS
            try:
                subprocess.run(["screencapture", "-x", "screenshot.png"])
                screenshot = Image.open("screenshot.png").crop((left, top, right, bottom))
            except FileNotFoundError:
                raise Exception("screencapture is not available. This script requires macOS.")
        else:
            raise Exception("Unsupported operating system")

        # Convert the screenshot to base64
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def monitor_v_key(self):
        """
        Monitors the V key and handles the overlay and screenshot capture.
        """
        while True:
            if keyboard.is_pressed('v'):
                # Block the V key to prevent it from typing
                keyboard.block_key('v')

                width = 1024
                height = 768
                half_width = width // 2
                half_height = height // 2

                root = tk.Tk()
                root.overrideredirect(True)  
                root.attributes("-alpha", 0.5)  
                root.attributes("-topmost", True)

                canvas = tk.Canvas(root, bg="black", highlightthickness=0)
                canvas.pack(fill=tk.BOTH, expand=True)

                while keyboard.is_pressed('v'):
                    cursor_x, cursor_y = pyautogui.position()

                    left = cursor_x - half_width
                    top = cursor_y - half_height
                    right = cursor_x + half_width
                    bottom = cursor_y + half_height

                    screen_width, screen_height = pyautogui.size()
                    left = max(0, left)
                    top = max(0, top)
                    right = min(screen_width, right)
                    bottom = min(screen_height, bottom)

                    self.draw_rectangle(root, canvas, left, top, width, height)

                    time.sleep(0.05)

                root.destroy()

                keyboard.unblock_key('v')

                with self.screenshot_lock:
                    self.latest_screenshot = self.capture_around_cursor(left, top, right, bottom)

            time.sleep(0.1)

vision = Vision()