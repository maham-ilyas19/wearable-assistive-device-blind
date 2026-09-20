# wearable-assistive-device-blind
An IoT and Computer Vision-based wearable assistive device designed to aid visually impaired individuals with navigation and obstacle detection, sensor fusion, and audio feedback.

## 📌 Project Overview
Navigating unfamiliar environments poses significant safety risks for visually impaired individuals. This project combines embedded hardware sensors and computer vision to detect indoor and outdoor obstacles, measure distances, and provide real-time tactile/auditory feedback to the user.

## ✨ Key Features
- **Real-Time Obstacle Detection:** Identifies objects, stairs, and hazards in the path.
- **Distance Estimation:** Measures proximity using ultrasonic/LiDAR sensors.
- **Auditory/Haptic Alerts:** Delivers spatial sound or vibration feedback to guide the user.
- **Compact & Wearable Form Factor:** Lightweight hardware integration designed for daily wear.

## 🛠️ Tech Stack & Hardware Components

### Hardware
- **Microcontroller / Single Board Computer:** Raspberry Pi / ESP32 / Arduino
- **Sensors:** Ultrasonic sensors, Camera module, IMU (Gyr/Accel)
- **Feedback:** Haptic vibration motors / Buzzer / Bluetooth earpiece
- **Power:** Rechargeable Li-Ion battery pack

### Software & Libraries
- **Language:** Python
- **Libraries:** OpenCV, NumPy, TensorFlow Lite / PyTorch (for lightweight object detection)

## 🚀 Getting Started

### Prerequisites
Ensure you have Python 3.8+ installed along with the required libraries:
pip install opencv-python numpy
