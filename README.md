# JustTrack MDVR API Documentation

This repository contains API documentation for the JustTrack MDVR system, including authentication, live video streaming, GPS tracking, video query, and download services.

---

## 📡 Available APIs

### 🔹 Login API
Authenticate user and obtain session ID (`jsession`) required for all other APIs.

---

### 🔹 Live Video API
Access real-time video streaming using device ID and session token.

---

### 🔹 Device Status (GPS)
Fetch real-time GPS location, speed, and device status information.

---

### 🔹 Query Video API
Retrieve recorded video files based on date, time, and channel.

---

### 🔹 Cross-Day Video API
Query video files across multiple days (supported only for 1078 devices).

---

### 🔹 Download Video API
Download video files using segment or full download methods.

---

## 🔐 Authentication Flow

1. Call **Login API**
2. Get `jsession`
3. Use `jsession` in all API requests

---


---

## ⚠️ Important Notes

- `jsession` is mandatory for most APIs  
- Session expires — re-login if needed  
- Channel indexing starts from `0`  
- Time values are in seconds (0–86399)  
- Some APIs are device-specific (e.g., 1078 protocol)  

---

## 🚀 Usage

Use these APIs for:
- Fleet tracking systems  
- Video surveillance  
- IoT device monitoring  
- MDVR integrations  

---
