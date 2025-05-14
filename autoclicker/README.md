# Advanced Auto Clicker

A Python-based auto clicker application that allows you to automate mouse clicks and keyboard actions at multiple locations with customizable delays and repeat counts.

## Features

- Set multiple locations for actions
- Choose from different actions:
  - Left click
  - Right click
  - Up arrow key
  - Down arrow key
  - Enter key
- Customize delay time for each action
- Set number of repetitions (including infinite)
- Real-time status updates
- Start/Stop functionality

## Requirements

- Python 3.6 or higher
- Required packages (install using `pip install -r requirements.txt`):
  - pyautogui
  - keyboard

## Installation

1. Clone or download this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:

   ```
   python autoclicker.py
   ```

2. Set up the locations:

   - Enter the number of locations you want to set
   - Click "Set Locations" to create the location entries
   - For each location:
     - Select the desired action from the dropdown
     - Set the delay time in seconds
     - Click "Set Location" and then click at the desired position on your screen

3. Configure the repeat count:

   - Enter the number of times you want the sequence to repeat
   - Use 0 for infinite repetition

4. Start/Stop:
   - Click "Start" to begin the automation
   - Click "Stop" to halt the automation at any time

## Notes

- The application runs in a separate thread to keep the UI responsive
- You can stop the automation at any time using the Stop button
- Make sure to set at least one location before starting
- The status label shows the current state of the automation
