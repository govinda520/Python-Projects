# Driver Drowsiness Detection System

A real-time driver drowsiness detection system using computer vision to monitor driver alertness and prevent accidents caused by drowsy driving.

## Features

- Real-time face and eye detection using Haar Cascade Classifiers
- Eye state monitoring (open/closed)
- Drowsiness detection based on eye closure duration
- Audio alerts when drowsiness is detected
- Visual feedback with on-screen status indicators
- Brightness-based eye state analysis
- Configurable alert thresholds

## Prerequisites

- Python 3.7 or higher
- Webcam
- Speakers (for audio alerts)

## Required Packages

Install the required packages using pip:

```bash
pip install opencv-python
pip install numpy
pip install pygame
```

## Project Structure

```
drivingSafety/
├── main.py                 # Main application file
├── utils.py               # Utility functions
├── haarcascades/          # Haar cascade classifier files
│   ├── haarcascade_frontalface_default.xml
│   └── haarcascade_eye.xml
└── sounds/                # Alert sound files
    └── alert.wav
```

## Setup Instructions

1. Clone this repository
2. Install the required packages using pip
3. Ensure your webcam is properly connected
4. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. Launch the application
2. Position yourself in front of the webcam
3. The system will automatically detect your face and eyes
4. If your eyes remain closed for more than 1.5 seconds, an alert will be triggered
5. Press 'ESC' to quit the application

## Configuration

You can adjust the following parameters in the code:

- `BRIGHTNESS_THRESHOLD`: Adjust based on your lighting conditions (default: 50)
- Drowsiness threshold: Modify the `threshold` parameter in `is_drowsy()` function (default: 1.5 seconds)

## Safety Notice

This system is designed as a supplementary safety feature and should not be relied upon as the sole means of preventing drowsy driving. Always ensure you are well-rested before driving and take regular breaks during long journeys.

## License

This project is open source and available under the MIT License.
