# Sentinel Lock

> Intelligent workstation security through automatic presence detection.

## Overview

Sentinel Lock is an open-source desktop security application that automatically locks a workstation when the authorized user is no longer actively using the computer.

The project is designed to improve workstation security by combining idle detection with optional presence-awareness technologies such as webcam detection, Bluetooth proximity, and face recognition.

## Features

### Current

* Automatic workstation locking after user inactivity
* Keyboard activity monitoring
* Mouse activity monitoring
* Configurable idle timeout
* Lightweight background execution
* Windows startup support

### Planned

* Webcam-based user presence detection
* Face recognition
* Bluetooth phone proximity detection
* Wi-Fi device presence detection
* Smart confidence scoring to reduce false locks
* System tray application
* Notification before locking
* Event logging
* Multi-monitor support
* Cross-platform support

## Roadmap

### Phase 1 — Core Security

* Idle detection engine
* Automatic workstation locking
* Configuration system
* Logging

### Phase 2 — Presence Detection

* Webcam monitoring
* Human presence detection
* Face recognition
* Smart lock decisions

### Phase 3 — Device Awareness

* Bluetooth proximity
* Wi-Fi presence
* Trusted devices
* Adaptive security

### Phase 4 — Desktop Experience

* System tray integration
* Settings interface
* Notification system
* Startup manager

### Phase 5 — Enterprise

* Security policies
* Centralized configuration
* Audit logs
* Cross-platform support

## Technology Stack

* Python
* Windows API
* OpenCV
* PyWin32
* Pynput
* Psutil

## Project Structure

```text
sentinel-lock/
│
├── src/
├── config/
├── assets/
├── tests/
├── docs/
├── requirements.txt
├── LICENSE
└── README.md
```

## Use Cases

* Personal workstation security
* Office environments
* Shared computers
* Research laboratories
* Development workstations
* Educational institutions

## Goals

* Lightweight
* Privacy-first
* Easy to configure
* Open source
* Reliable automatic locking
* Minimal resource usage

## Contributing

Contributions are welcome. Bug reports, feature requests, documentation improvements, and pull requests are appreciated.

## License

This project is licensed under the MIT License.
