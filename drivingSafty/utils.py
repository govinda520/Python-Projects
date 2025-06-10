import time
import pygame

def is_drowsy(start_time, current_time, threshold=1.5):
    return (current_time - start_time) > threshold

def play_alert(sound_path):
    pygame.mixer.init()
    pygame.mixer.music.load(sound_path)
    pygame.mixer.music.play()

def stop_alert():
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
