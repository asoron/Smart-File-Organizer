# main.py
import os
import sys
import json
from pathlib import Path
import unicodedata
import subprocess

from PyQt5.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QMenu, 
                            QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                            QSpinBox, QPushButton, QLabel, QFileDialog, 
                            QListWidget, QHBoxLayout, QDialog, QGraphicsDropShadowEffect,
                            QDialogButtonBox)
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt

from config import Config
from file_manager import FileManager, FileWatcher
from watchdog.observers import Observer

class DarkPalette:
    @staticmethod
    def setup(app):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(dark_palette)
        app.setStyleSheet("""
            QWidget {
                background-color: #353535;
                color: white;
                font-size: 12px;
            }
            QLineEdit, QListWidget {
                background-color: #252525;
                border: 1px solid #505050;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #505050;
                border: none;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #606060;
            }
        """)

class SearchDialog(QDialog):
    def __init__(self, base_dir, parent=None):
        super().__init__(parent)
        self.base_dir = base_dir
        self.setWindowTitle('Dosya Arama')
        self.setGeometry(300, 300, 600, 500)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout()
        
        # Arama input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Dosya adı veya uzantı ara...')
        self.search_input.textChanged.connect(self.perform_search)
        layout.addWidget(self.search_input)
        
        # Sonuç listesi
        self.result_list = QListWidget()
        self.result_list.itemDoubleClicked.connect(self.open_file)
        layout.addWidget(self.result_list)
        
        # Sonuç sayısı etiketi
        self.result_count_label = QLabel('Toplam Sonuç: 0')
        layout.addWidget(self.result_count_label)
        
        # Buton kutusu - sadece Kapat butonu
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.hide)  # hide yerine close
        layout.addWidget(button_box)
        
        self.setLayout(layout)



    def _get_turkish_variations(self, text):
        """Verilen metin için tüm varyasyonları ve normalize edilmiş versiyonları oluşturur"""
        variations = set()
        
        # Normalize edilmiş ve çeşitli varyasyonlar
        variations.add(text.lower())
        
        # Türkçe karakter eşleşmeleri ve dönüşümleri
        tr_chars_map = {
            'i': ['i', 'ı', 'İ', 'I'],
            'ı': ['i', 'ı', 'İ', 'I'],
            'İ': ['i', 'ı', 'İ', 'I'],
            'I': ['i', 'ı', 'İ', 'I'],
            'ğ': ['g', 'ğ'],
            'g': ['g', 'ğ'],
            'ü': ['u', 'ü'],
            'u': ['u', 'ü'],
            'ş': ['s', 'ş'],
            's': ['s', 'ş'],
            'ö': ['o', 'ö'],
            'o': ['o', 'ö'],
            'ç': ['c', 'ç'],
            'c': ['c', 'ç']
        }

        # Tüm olası karakter kombinasyonlarını oluştur
        def generate_variations(current_text, index):
            if index == len(current_text):
                variations.add(current_text.lower())
                return
            
            char = current_text[index]
            # Mevcut karakterin tüm olası varyasyonlarını dene
            for replacement in tr_chars_map.get(char, [char]):
                new_text = current_text[:index] + replacement + current_text[index+1:]
                generate_variations(new_text, index + 1)

        generate_variations(text, 0)
        
        # Normalize edilmiş versiyonları da ekle
        normalized_variations = set()
        for variation in variations:
            # Aksanları kaldır ve küçük harfe çevir
            normalized = unicodedata.normalize('NFKD', variation).encode('ascii', 'ignore').decode('utf-8').lower()
            normalized_variations.add(normalized)
        
        variations.update(normalized_variations)
        
        return variations
    def perform_search(self, text):
        self.result_list.clear()
        if not text:
            self.result_count_label.setText('Toplam Sonuç: 0')
            return
        
        # Normalize arama metni
        normalized_search_text = unicodedata.normalize('NFKD', text.lower())
        normalized_search_text = ''.join(
            char for char in normalized_search_text 
            if not unicodedata.combining(char)
        )
        
        results = self._search_files(self.base_dir, normalized_search_text)
        
        for file_path in results:
            self.result_list.addItem(str(file_path))
        
        self.result_count_label.setText(f'Toplam Sonuç: {len(results)}')

    def _search_files(self, directory, search_term):
        results = []
        
        # Arama teriminin tüm varyasyonlarını al
        search_variations = self._get_turkish_variations(search_term)
        
        for item in Path(directory).rglob('*'):
            if item.is_file():
                file_name = item.name
                
                # Dosya adının tüm varyasyonlarını al
                file_variations = self._get_turkish_variations(file_name)
                
                # Herhangi bir arama varyasyonu dosya varyasyonlarında varsa ekle
                if any(
                    any(search_var in file_var or file_var in search_var 
                        for file_var in file_variations) 
                    for search_var in search_variations
                ):
                    results.append(item)
        
        return results
  
    def open_file(self, item):
        file_path = item.text()
        try:
            subprocess.Popen(f'explorer "{file_path}"')
        except Exception as e:
            print(f"Dosya açma hatası: {e}")
            
    def closeEvent(self, event):
        # Pencereyi gizle, uygulamayı kapatma
        event.ignore()
        self.hide()
class SettingsWindow(QMainWindow):
    def __init__(self, config, file_manager):
        super().__init__()
        self.config = config
        self.file_manager = file_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Dosya Organizatörü Ayarları')
        self.setGeometry(300, 300, 600, 500)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create form layout for settings
        form_layout = QFormLayout()

        # Resource Limits
        self.cpu_limit = QSpinBox()
        self.cpu_limit.setRange(0, 100)
        self.cpu_limit.setValue(self.config.RESOURCE_LIMITS['MAX_CPU'])
        form_layout.addRow('Maks CPU Kullanımı (%)', self.cpu_limit)

        self.ram_limit = QSpinBox()
        self.ram_limit.setRange(0, 100)
        self.ram_limit.setValue(self.config.RESOURCE_LIMITS['MAX_RAM'])
        form_layout.addRow('Maks RAM Kullanımı (%)', self.ram_limit)

        # Base Directories
        self.base_dirs = {}
        for key, path in self.config.BASE_DIRS.items():
            row_layout = QHBoxLayout()
            path_label = QLineEdit(str(path))
            path_label.setReadOnly(True)
            browse_btn = QPushButton('Gözat')
            browse_btn.clicked.connect(lambda checked, k=key: self.browse_directory(k))
            
            row_layout.addWidget(path_label)
            row_layout.addWidget(browse_btn)
            form_layout.addRow(f'{key} Dizini:', row_layout)
            self.base_dirs[key] = path_label

        layout.addLayout(form_layout)

        # Button Box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

    def browse_directory(self, key):
        dir_path = QFileDialog.getExistingDirectory(self, f'{key} Dizini Seç')
        if dir_path:
            self.base_dirs[key].setText(dir_path)

    def save_settings(self):
        # Update resource limits
        self.config.RESOURCE_LIMITS['MAX_CPU'] = self.cpu_limit.value()
        self.config.RESOURCE_LIMITS['MAX_RAM'] = self.ram_limit.value()

        # Update base directories
        for key, widget in self.base_dirs.items():
            self.config.BASE_DIRS[key] = Path(widget.text())

        # Save to file
        self.save_config_to_file()
        
        # Recreate directories with new paths
        self.file_manager.create_directories()
        
        # Hide window
        self.hide()

    def save_config_to_file(self):
        config_data = {
            'RESOURCE_LIMITS': self.config.RESOURCE_LIMITS,
            'BASE_DIRS': {k: str(v) for k, v in self.config.BASE_DIRS.items()}
        }
        
        config_file = Path.home() / '.file_organizer_config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=4)

    def closeEvent(self, event):
        # Hide window instead of closing when X button is clicked
        event.ignore()
        self.hide()

class FileOrganizerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        DarkPalette.setup(self.app)  # Dark mode uygula
        
        self.config = Config()
        self.file_manager = FileManager(self.config)
        self.observer = Observer()
        
        # Icon path için düzenleme
        icon_path = self.get_resource_path('icon.png')
        
        # Setup tray icon
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path))
        self.create_tray_menu()
        self.tray_icon.show()

        # Create settings window instance
        self.settings_window = SettingsWindow(self.config, self.file_manager)

        # Setup file watcher
        self.setup_file_watcher()

    def get_resource_path(self, relative_path):
        """ PyInstaller ile paketlendiğinde doğru dosya yolunu alır """
        try:
            # PyInstaller tarafından oluşturulan geçici klasör
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def create_tray_menu(self):
        menu = QMenu()
        
        settings_action = menu.addAction('Ayarlar')
        settings_action.triggered.connect(self.show_settings)
        
        search_action = menu.addAction('Dosya Ara')
        search_action.triggered.connect(self.show_search_dialog)
        
        exit_action = menu.addAction('Çıkış')
        exit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(menu)

    def show_search_dialog(self):
        search_dialog = SearchDialog(self.config.BASE_DIRS['FILES'])
        search_dialog.exec_()

    def show_settings(self):
        self.settings_window.show()

    def setup_file_watcher(self):
        self.observer.schedule(
            FileWatcher(self.file_manager),
            str(self.config.BASE_DIRS['FILES']),
            recursive=False
        )
        self.observer.start()

    def quit_app(self):
        self.observer.stop()
        self.observer.join()
        self.app.quit()

    def run(self):
        self.file_manager.categorize_files_in_directory()
        return self.app.exec_()

def main():
    app = FileOrganizerApp()
    sys.exit(app.run())

if __name__ == '__main__':
    main()
