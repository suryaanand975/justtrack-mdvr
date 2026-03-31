# JustTrack MDVR

JustTrack MDVR is a high-performance server designed for real-time communication with MDVR (Mobile Digital Video Recorder) devices. It processes hex-based protocol data, manages device communication, and ensures reliable data exchange.

---

## 🚀 Features

- Real-time socket communication with MDVR devices  
- Hex protocol parsing and checksum validation  
- Terminal registration and authentication handling  
- Heartbeat monitoring and device status tracking  
- GPS/telemetry data processing  
- Multimedia (image) data reconstruction and storage  
- Multi-threaded client handling for scalability  
- Structured logging for debugging and monitoring  

---

## 🏗️ Architecture

- **Socket Server** → Handles incoming device connections  
- **Message Processor** → Parses and routes protocol messages  
- **Data Handlers** → Process GPS, heartbeat, and media data  
- **Media Handler** → Reconstructs and stores images  
- **Logger** → Tracks system activity  

---

📡 Supported Message Types
0100 → Terminal Registration
0102 → Authentication
0002 → Heartbeat
0200 → Location Data
0704 → Bulk Data
0801 → Multimedia Upload
0900 → Custom Data
git clone https://github.com/your-username/justtrack-mdvr.git
cd justtrack-mdvr
python main.py
