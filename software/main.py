#!/usr/bin/env python3
"""
Blind Assistant - Object Detection with Voice Output and Navigation
Works on Windows, Linux, macOS, and Raspberry Pi
Includes left/right navigation commands based on object position
"""

import cv2
import time
import subprocess
import sys
import os
from ultralytics import YOLO
from collections import deque

# ==================== CONFIGURATION ====================
MODEL_PATH = "best_final_14.pt"
CONFIDENCE_THRESHOLD = 0.5
CAMERA_ID = 0
ANNOUNCEMENT_COOLDOWN = 3  # Seconds between announcements
NAVIGATION_COOLDOWN = 2  # Seconds between navigation commands
# =======================================================

class BlindAssistant:
    def __init__(self):
        print("="*50)
        print("BLIND ASSISTANCE SYSTEM WITH NAVIGATION")
        print("="*50)
        
        # Initialize voice with queue
        self.init_voice()
        self.speech_queue = deque()
        self.is_speaking = False
        
        # Load model
        self.load_model()
        
        # Initialize camera
        self.init_camera()
        
        # State tracking
        self.last_announce = 0
        self.last_navigation = 0
        self.last_status = 0
        self.frame_count = 0
        
        # Start voice queue processor
        self.start_voice_processor()
        
        # Test voice
        self.speak("System ready. Starting camera with navigation.")
        print("\nâœ… SYSTEM RUNNING")
        print("Press Ctrl+C to stop\n")
    
    def init_voice(self):
        """Initialize voice for different platforms"""
        self.voice_method = None
        self.engine = None
        
        # Detect platform
        if sys.platform == "win32":
            self.voice_method = "powershell"
            print("âœ… Using Windows PowerShell speech")
            
        elif sys.platform == "linux":
            try:
                subprocess.run(['which', 'espeak'], capture_output=True, check=True)
                self.voice_method = "espeak"
                print("âœ… Using eSpeak speech")
            except:
                try:
                    import pyttsx3
                    self.engine = pyttsx3.init()
                    self.engine.setProperty('rate', 80)
                    self.engine.setProperty('volume', 1.0)
                    self.voice_method = "pyttsx3"
                    print("âœ… Using pyttsx3 speech")
                except:
                    self.voice_method = "print"
                    print("âš ï¸ No voice output - using console only")
        
        elif sys.platform == "darwin":
            self.voice_method = "say"
            print("âœ… Using macOS speech")
        
        else:
            self.voice_method = "print"
            print("âš ï¸ Unknown platform - using console only")
    
    def start_voice_processor(self):
        """Start background thread for voice queue"""
        import threading
        def process_queue():
            while True:
                if self.speech_queue and not self.is_speaking:
                    text = self.speech_queue.popleft()
                    self.is_speaking = True
                    self._speak_now(text)
                    self.is_speaking = False
                time.sleep(0.1)
        
        thread = threading.Thread(target=process_queue, daemon=True)
        thread.start()
    
    def speak(self, text):
        """Add speech to queue (non-blocking)"""
        if text and text not in self.speech_queue:
            self.speech_queue.append(text)
            print(f"ðŸ”Š {text}")
    
    def _speak_now(self, text):
        """Actually speak the text"""
        try:
            if self.voice_method == "powershell":
                text = text.replace("'", "`'").replace('"', '`"')
                cmd = f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{text}\')"'
                subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            
            elif self.voice_method == "espeak":
                subprocess.run(['espeak', text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            
            elif self.voice_method == "say":
                subprocess.run(['say', text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            
            elif self.voice_method == "pyttsx3":
                self.engine.say(text)
                self.engine.runAndWait()
            
        except Exception as e:
            print(f"Speech error: {e}")
    
    def load_model(self):
        """Load YOLO model"""
        print("Loading model...")
        
        if not os.path.exists(MODEL_PATH):
            print(f"âŒ Model file '{MODEL_PATH}' not found!")
            sys.exit(1)
        
        try:
            self.model = YOLO(MODEL_PATH)
            
            if hasattr(self.model, 'names'):
                self.class_names = self.model.names
            else:
                self.class_names = {
                    0: "Chair", 1: "Door", 2: "Person", 3: "Table", 4: "bathtub",
                    5: "shower", 6: "sink", 7: "toilet", 8: "stairs", 9: "glassdoor",
                    10: "sofa", 11: "crawling_baby", 12: "plant", 13: "wall", 14: "bed"
                }
            
            print(f"âœ… Model loaded! Can detect {len(self.class_names)} objects")
            print("\nDetectable objects:")
            for idx, name in self.class_names.items():
                print(f"  {idx}: {name}")
            print()
            
        except Exception as e:
            print(f"âŒ Error loading model: {e}")
            sys.exit(1)
    
    def init_camera(self):
        """Initialize camera"""
        print(f"Opening camera (ID: {CAMERA_ID})...")
        
        if sys.platform == "linux":
            self.cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_V4L2)
        else:
            self.cap = cv2.VideoCapture(CAMERA_ID)
        
        if not self.cap.isOpened():
            print("âŒ Cannot open camera!")
            sys.exit(1)
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("âœ… Camera ready")
    
    def get_object_position(self, bbox, frame_width):
        """
        Determine object position and return direction command
        Returns: (direction, normalized_position)
        """
        x1, y1, x2, y2 = bbox
        obj_center_x = (x1 + x2) / 2
        frame_center = frame_width / 2
        
        # Calculate normalized position (-1 to 1)
        normalized_pos = (obj_center_x - frame_center) / (frame_width / 2)
        
        # Determine direction with threshold
        if normalized_pos < -0.25:  # Left side
            return "left", normalized_pos
        elif normalized_pos > 0.25:  # Right side
            return "right", normalized_pos
        else:  # Center
            return "center", normalized_pos
    
    def get_navigation_command(self, obj_name, direction, size_ratio):
        """
        Generate navigation command based on object position and size
        """
        # Determine distance
        if size_ratio > 0.15:
            distance = "very close"
            urgency = "immediately"
        elif size_ratio > 0.08:
            distance = "close"
            urgency = "soon"
        elif size_ratio > 0.03:
            distance = "ahead"
            urgency = "shortly"
        else:
            distance = "in the distance"
            urgency = "when you reach it"
        
        # Special danger objects
        danger_objects = ['stairs', 'wall', 'crawling_baby']
        
        if obj_name.lower() in danger_objects:
            if direction == "left":
                return f"DANGER! {obj_name} on your left! Turn right immediately!"
            elif direction == "right":
                return f"DANGER! {obj_name} on your right! Turn left immediately!"
            else:
                return f"DANGER! {obj_name} directly ahead! Stop immediately!"
        
        # Regular navigation
        if direction == "left":
            return f"{obj_name} on your left {distance}. Turn right {urgency}."
        elif direction == "right":
            return f"{obj_name} on your right {distance}. Turn left {urgency}."
        else:
            if size_ratio > 0.1:
                return f"{obj_name} directly ahead and close! Move left or right to avoid."
            else:
                return f"{obj_name} ahead {distance}. Prepare to move left or right."
    
    def get_priority_message(self, objects):
        """Generate priority-based message"""
        objects_lower = [obj.lower() for obj in objects]
        
        if 'stairs' in objects_lower:
            return "DANGER! Stairs detected! Stop immediately!"
        elif 'wall' in objects_lower:
            return "DANGER! Wall ahead! Turn left or right!"
        elif 'crawling_baby' in objects_lower:
            return "CAUTION! Baby on floor! Look down carefully!"
        elif 'person' in objects_lower:
            return "Person detected nearby, say excuse me if passing"
        elif 'bathtub' in objects_lower or 'shower' in objects_lower:
            return "Bathroom fixture ahead, be careful of wet floor"
        elif len(objects) == 1:
            return f"{objects[0]} detected"
        else:
            return f"Multiple objects: {', '.join(objects[:3])}"
    
    def draw_navigation_overlay(self, frame, detections):
        """Draw navigation arrows and info on frame"""
        h, w = frame.shape[:2]
        
        # Draw center line
        cv2.line(frame, (w//2, 0), (w//2, h), (255, 255, 0), 1)
        
        # Draw zones
        zone_width = w // 3
        cv2.rectangle(frame, (0, 0), (zone_width, h), (0, 0, 255), 2)  # Left zone
        cv2.rectangle(frame, (w - zone_width, 0), (w, h), (0, 0, 255), 2)  # Right zone
        
        # Add zone labels
        cv2.putText(frame, "LEFT ZONE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(frame, "CENTER", (w//2-40, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        cv2.putText(frame, "RIGHT ZONE", (w-120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # Show navigation for closest object
        if detections:
            closest = detections[0]  # Already sorted by size
            direction, pos = closest['direction'], closest['norm_pos']
            
            if direction == "left":
                cv2.arrowedLine(frame, (w//4, h//2), (w//2, h//2), (0, 0, 255), 3)
                cv2.putText(frame, "TURN RIGHT", (w//4-50, h//2-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            elif direction == "right":
                cv2.arrowedLine(frame, (3*w//4, h//2), (w//2, h//2), (0, 0, 255), 3)
                cv2.putText(frame, "TURN LEFT", (3*w//4-40, h//2-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "MOVE LEFT OR RIGHT", (w//2-100, h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        return frame
    
    def run(self):
        """Main detection loop with navigation"""
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Camera error, reconnecting...")
                    time.sleep(1)
                    continue
                
                self.frame_count += 1
                frame_height, frame_width = frame.shape[:2]
                
                # Process every 2nd frame
                if self.frame_count % 2 == 0:
                    # Run detection
                    results = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
                    
                    # Extract detected objects with position info
                    detected_objects = []
                    if results[0].boxes is not None:
                        for box in results[0].boxes:
                            cls = int(box.cls[0])
                            conf = float(box.conf[0])
                            name = self.class_names.get(cls, "object")
                            bbox = box.xyxy[0].tolist()
                            
                            # Calculate object size
                            x1, y1, x2, y2 = bbox
                            obj_size = (x2 - x1) * (y2 - y1)
                            frame_area = frame_width * frame_height
                            size_ratio = obj_size / frame_area
                            
                            # Get position and direction
                            direction, norm_pos = self.get_object_position(bbox, frame_width)
                            
                            detected_objects.append({
                                'name': name,
                                'confidence': conf,
                                'size_ratio': size_ratio,
                                'direction': direction,
                                'norm_pos': norm_pos,
                                'bbox': bbox
                            })
                    
                    # Sort by size (largest/closest first)
                    detected_objects.sort(key=lambda x: x['size_ratio'], reverse=True)
                    
                    current_time = time.time()
                    
                    # Generate navigation command from closest object
                    if detected_objects and (current_time - self.last_navigation) >= NAVIGATION_COOLDOWN:
                        closest = detected_objects[0]
                        nav_command = self.get_navigation_command(
                            closest['name'],
                            closest['direction'],
                            closest['size_ratio']
                        )
                        
                        # Speak navigation command
                        self.speak(nav_command)
                        self.last_navigation = current_time
                        
                        # Console output with direction
                        direction_symbol = "â¬…ï¸" if closest['direction'] == "left" else "âž¡ï¸" if closest['direction'] == "right" else "â¬†ï¸"
                        print(f"ðŸ§­ {direction_symbol} {closest['name']}: {closest['direction'].upper()} (Size: {closest['size_ratio']:.2f})")
                    
                    # General announcements (less frequent)
                    unique_objects = list(set([d['name'] for d in detected_objects]))
                    
                    if unique_objects and (current_time - self.last_announce) >= ANNOUNCEMENT_COOLDOWN * 2:
                        message = self.get_priority_message(unique_objects)
                        if "DANGER" in message:  # Only speak danger messages separately
                            self.speak(message)
                        self.last_announce = current_time
                        print(f"ðŸ“Š Detected: {', '.join(unique_objects)}")
                    
                    # Periodic path clear message
                    elif not unique_objects and (current_time - self.last_status) >= 15:
                        self.speak("Path is clear. Continue walking.")
                        self.last_status = current_time
                    
                    # Draw navigation overlay on frame
                    frame = self.draw_navigation_overlay(frame, detected_objects)
                
                # Show the frame (optional - can be disabled on headless)
                if self.frame_count % 2 == 0:
                    cv2.imshow('Blind Assistant - Navigation', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Small delay
                time.sleep(0.03)
                
        except KeyboardInterrupt:
            print("\n\nðŸ›‘ Stopping system...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.speak("System stopped. Take care.")
        print("\nâœ… System stopped")

# ==================== MAIN ====================
if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("âŒ Python 3.8 or higher is required!")
        sys.exit(1)
    
    # Install missing packages if needed
    def install_package(package):
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    # Check for required packages
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Ultralytics not found. Installing...")
        install_package("ultralytics")
        from ultralytics import YOLO
    
    try:
        import cv2
    except ImportError:
        print("OpenCV not found. Installing...")
        install_package("opencv-python")
        import cv2
    
    # Run the assistant
    assistant = BlindAssistant()
    assistant.run()
