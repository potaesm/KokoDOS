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
from pynput.mouse import Listener as MouseListener

class Vision:
    def __init__(self):
        self.latest_screenshot = None
        self.screenshot_lock = threading.Lock()
        self.size = 448  # Initial size of the overlay (width and height)
        self.min_size = 448  # Minimum size
        self.max_size = 1344  # Maximum size
        self.root = None  # Tkinter root window
        self.canvas = None  # Tkinter canvas for drawing the overlay
        self.mouse_listener = None  # Mouse listener for scroll events
        self.v_pressed = False  # Flag to track if 'V' is pressed

    def draw_rectangle(self, left, top, width, height):
        """
        Updates the rectangle on the screen using a tkinter overlay.
        """
        if self.canvas:
            self.canvas.delete("all")
            self.canvas.create_rectangle(0, 0, width, height, outline="red", width=2)

            font_size = min(width, height) // 32
            self.canvas.create_text(
                width // 2,
                height // 2,
                text="Share with KokoDOS 👁️",
                font=("Arial", font_size, "bold"), 
                fill="red",
                anchor="center"
            )

            self.root.geometry(f"{width}x{height}+{left}+{top}")

            self.root.update()
    def capture_around_cursor(self, left, top, right, bottom):
        """
        Captures a screenshot within the specified bounding box.
        Returns the screenshot as a base64-encoded string.
        """
        # Capture the screenshot based on the OS
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

        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def on_scroll(self, x, y, dx, dy):
        """
        Handles mouse scroll events to resize the overlay.
        """
        if self.v_pressed:
            if dy > 0:
                self.size = min(self.size + 32, self.max_size)
            elif dy < 0:
                self.size = max(self.size - 32, self.min_size)

    # def save_latest_screenshot(self, filename="screenshot.png"):
    #     """
    #     Saves the latest screenshot as a PNG file. Debug only.
    #     """
    #     if self.latest_screenshot:
    #         try:
    #             screenshot_data = base64.b64decode(self.latest_screenshot)
    #             image = Image.open(io.BytesIO(screenshot_data))
    #             image.save(filename, format="PNG")
    #             print(f"Screenshot saved as {filename}")
    #         except Exception as e:
    #             print(f"Failed to save screenshot: {e}")
    #     else:
    #         print("No screenshot available to save.")
            
    def monitor_v_key(self):
        """
        Monitors the V key and handles the overlay and screenshot capture.
        """
        while True:
            if keyboard.is_pressed('v') and not self.v_pressed:
                self.v_pressed = True
                keyboard.block_key('v')

                self.mouse_listener = MouseListener(on_scroll=self.on_scroll)
                self.mouse_listener.start()

                self.root = tk.Tk()
                self.root.overrideredirect(True)  
                self.root.attributes("-alpha", 0.5)  
                self.root.attributes("-topmost", True)  

                self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
                self.canvas.pack(fill=tk.BOTH, expand=True)

                while self.v_pressed:
                    cursor_x, cursor_y = pyautogui.position()

                    half_size = self.size // 2
                    left = cursor_x - half_size
                    top = cursor_y - half_size
                    right = cursor_x + half_size
                    bottom = cursor_y + half_size

                    screen_width, screen_height = pyautogui.size()
                    left = max(0, min(left, screen_width - self.size))  # Prevent going beyond left and right
                    top = max(0, min(top, screen_height - self.size))   # Prevent going beyond top and bottom
                    right = left + self.size
                    bottom = top + self.size

                    self.draw_rectangle(left, top, self.size, self.size)

                    time.sleep(0.05)

                    if not keyboard.is_pressed('v'):
                        self.v_pressed = False

                self.root.destroy()
                self.root = None
                self.canvas = None

                if self.mouse_listener:
                    self.mouse_listener.stop()
                    self.mouse_listener = None

                keyboard.unblock_key('v')

                with self.screenshot_lock:
                    self.latest_screenshot = self.capture_around_cursor(left, top, right, bottom)
                    #self.save_latest_screenshot()
            time.sleep(0.1)

vision = Vision()