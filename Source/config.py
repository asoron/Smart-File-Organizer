# config.py
import os
from pathlib import Path

class Config:
    def __init__(self):
        # Dinamik path tanımları
        self.HOME_PATH = Path.home()
        self.DESKTOP_PATH = self.HOME_PATH / 'Desktop'
        
        # Ana dizinler
        self.BASE_DIRS = {
            'OLD': self.DESKTOP_PATH / 'Old',
            'TRASH': self.DESKTOP_PATH / 'Trash', 
            'FILES': self.DESKTOP_PATH / 'Files',
            'LOG': self.DESKTOP_PATH / 'Files' / 'FileOrganizer_Log.txt' 
        }

        # Kaynak limitleri
        self.RESOURCE_LIMITS = {
            'MAX_CPU': 50,
            'MAX_RAM': 70
        }

        # Dosya kategorileri ve uzantıları
        self.FILE_CATEGORIES = {
            "Setups": ["exe", "msi"],
            "Documents": ["pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls", "txt"],
            "Images": ["jpg", "jpeg", "png", "gif", "bmp", "tiff"],
            "Videos": ["mp4", "mkv", "avi", "mov", "flv", "wmv", "3gp"],
            "Music": ["mp3", "wav", "flac", "aac", "ogg", "wma"],
            "Compressed": ["zip", "rar", "7z", "tar", "gz", "iso"],
            "Others": []
        }

        self.EXTENSION_MAP = {
            ext: category 
            for category, extensions in self.FILE_CATEGORIES.items() 
            for ext in extensions
        }