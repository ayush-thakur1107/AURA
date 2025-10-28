# 🌌 AURA : Offline AI Vision Assistant

> “Where your gestures meet AI intuition.”

AURA is an **offline AI-powered gesture and vision-based assistant** built with **Python**, **Mediapipe**, and **YOLOv8**.  
It detects hand gestures in real-time and performs automated actions — all while recognizing real-world objects using computer vision.  
Designed to be futuristic yet lightweight, AURA+ redefines how humans interact with machines.

---

## 🧠 Overview

AURA enables **natural human-computer interaction** through camera input.  
It combines gesture control and object detection into one intelligent, offline system.

**Modes:**
- 💤 **Passive Mode:** Gesture-based quick controls (e.g., open app, take screenshot).
- 🚀 **Active Mode:** Full AI engagement — detects both gestures and objects with voice feedback.

---

## ⚙️ Features

- ✋ **Gesture Recognition** using Mediapipe  
- 🎯 **Object Detection** via YOLOv8 (pre-trained model)  
- 🧩 **Offline Processing** — No internet or cloud dependency  
- 🔊 **Voice Feedback** powered by Pyttsx3  
- 🪶 **Lightweight and Modular** Python architecture  
- 💻 **Cross-Platform:** Works on Windows, Linux, macOS  

---

## 🧩 Project Structure
```

AURA/
│
├── main.py                     # Main execution file
├── gestures/
│   ├── gesture_controller.py   # Handles gesture recognition and mapping
│
├── vision/
│   ├── yolo_detector.py        # YOLOv8-based object detection
│   ├── model/                  # YOLO weights (e.g., yolov8n.pt)
│
├── utils/
│   ├── voice_feedback.py       # Voice responses (optional)
│   ├── hud_overlay.py          # On-screen info display (optional)
│
├── assets/                     # Icons, sounds, visual elements
│
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation

````

---

## 🧠 How It Works

1. **Camera Activation:** Captures video frames using OpenCV.  
2. **Gesture Detection:** Mediapipe analyzes hand landmarks and classifies gestures.  
3. **Action Mapping:** Each gesture is linked to a system function or mode switch.  
4. **Object Detection:** YOLOv8 identifies real-world objects from live feed.  
5. **Voice Feedback:** AURA+ announces gestures or detected items via offline TTS.  
6. **Mode Control:** Gestures like *open palm* toggle between passive and active modes.

---

## 🧰 Tech Stack

| Component | Technology |
|------------|-------------|
| Gesture Recognition | Mediapipe |
| Object Detection | YOLOv8 (Ultralytics) |
| Programming Language | Python 3.x |
| Frameworks | OpenCV, PyTorch |
| Voice System | Pyttsx3 |
| Interface | CLI + OpenCV HUD |

---

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ayush-thakur1107/AURA.git
cd AURA
````

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python main.py
```

---

## 🧠 Future Enhancements

* Integrate face recognition for personalized mode switching
* Add emotion detection (using CNN models)
* Build a GUI dashboard using PyQt
* Enable offline speech recognition (for two-way conversation)

---


## 🧾 License

This project is licensed under the MIT License — free to use, modify, and build upon with credit.

---

## 👨‍💻 Author

**Ayush Thakur**
AI & Computer Vision Enthusiast
GitHub: [@ayush-thakur1107](https://github.com/ayush-thakur1107)
Project: [AURA](https://github.com/ayush-thakur1107/AURA)

---

> “AURA isn’t just a project — it’s a glimpse into the touchless future.”


