# file_manager.py
import os
import shutil
import zipfile
from datetime import datetime, timedelta
import psutil
from pathlib import Path
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import Config

class FileManager:
    def __init__(self, config):
        self.config = config
        self.create_directories() 
        self.setup_logging()  

    def create_directories(self):
        for key, path in self.config.BASE_DIRS.items():
            if key == 'LOG':
                path.parent.mkdir(parents=True, exist_ok=True)
                continue
            
            path.mkdir(parents=True, exist_ok=True)
        
        for category in self.config.FILE_CATEGORIES:
            (self.config.BASE_DIRS['FILES'] / category).mkdir(exist_ok=True)

    def setup_logging(self):
      log_file = self.config.BASE_DIRS['LOG']
      
      log_file.parent.mkdir(parents=True, exist_ok=True)
      
      logging.basicConfig(
          filename=str(log_file),
          level=logging.INFO,
          format='%(asctime)s - %(levelname)s: %(message)s',
          filemode='a'  
      )

      # Log dosyasının boyutunu sınırla (opsiyonel)
      try:
          max_log_size = 10 * 1024 * 1024  # 10 MB
          if log_file.exists() and log_file.stat().st_size > max_log_size:
              # Log dosyasını yedekle
              backup_log = log_file.with_name(f'FileOrganizer_Log_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
              log_file.rename(backup_log)
      except Exception as e:
          print(f"Log dosyası yönetimi hatası: {e}")

    def can_perform_io(self):
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        return (cpu_usage < self.config.RESOURCE_LIMITS['MAX_CPU'] and 
                ram_usage < self.config.RESOURCE_LIMITS['MAX_RAM'])

    def categorize_files_in_directory(self, directory=None):
        """
        Belirli bir dizindeki tüm dosyaları kategorilere ayırır.
        Eğer dizin belirtilmezse, Files klasörünü kullanır.
        """
        if directory is None:
            directory = self.config.BASE_DIRS['FILES']
        
        directory = Path(directory)
        
        files_to_categorize = [
            f for f in directory.iterdir() 
            if f.is_file() 
            and f.parent.name not in self.config.FILE_CATEGORIES
            and f.name != 'FileOrganizer_Log.txt'  # Exclude log file
        ]
        
        for file in files_to_categorize:
            try:
                self.move_to_category(str(file))
            except Exception as e:
                logging.error(f"Kategorilendirme hatası: {file} - {e}")

    def move_to_category(self, file_path):
        try:
            file = Path(file_path)
            
            # Skip log file
            if file.name == 'FileOrganizer_Log.txt':
                return
                
            file_ext = file.suffix[1:].lower() if file.suffix else ''
            
            category = self.config.EXTENSION_MAP.get(file_ext, 'Others')
            
            dest_dir = self.config.BASE_DIRS['FILES'] / category
            
            dest_path = dest_dir / self._unique_filename(dest_dir, file.name)
            
            shutil.move(str(file), str(dest_path))
            logging.info(f"Moved {file.name} to {category}")
        except Exception as e:
            logging.error(f"Category move error for {file_path}: {e}")
            self.move_to_trash(file_path)

    def move_to_trash(self, file_path):
        try:
            file = Path(file_path)
            dest_path = self.config.BASE_DIRS['TRASH'] / self._unique_filename(
                self.config.BASE_DIRS['TRASH'], file.name
            )
            shutil.move(str(file), str(dest_path))
            logging.info(f"Moved to trash: {file.name}")
        except Exception as e:
            logging.error(f"Trash move error: {e}")

    def _unique_filename(self, directory, filename):
        path = directory / filename
        counter = 1
        while path.exists():
            name, ext = path.stem, path.suffix
            path = directory / f"{name}_{counter}{ext}"
            counter += 1
        return path.name

    def compress_old_files(self, days_threshold=30):
      try:
          old_dir = self.config.BASE_DIRS['OLD']
          current_time = datetime.now()

          existing_rars = list(old_dir.glob('*.rar'))
          
          files_to_compress = [
              f for f in old_dir.iterdir() 
              if f.is_file() 
              and (current_time - datetime.fromtimestamp(f.stat().st_mtime)).days > days_threshold 
              and f not in existing_rars
          ]

          if not files_to_compress:
              logging.info("No files to compress in Old folder.")
              return

          if existing_rars:
              latest_rar = max(existing_rars, key=lambda x: x.stat().st_mtime)
          else:
              latest_rar = old_dir / f'Archived_{current_time.strftime("%Y%m%d_%H%M%S")}.rar'

          winrar_path = r"C:\Program Files\WinRAR\WinRAR.exe"  # Kendi WinRAR yolunuzu ekleyin
          
          with zipfile.ZipFile(latest_rar, 'a') as zipf:
              for file in files_to_compress:
                  try:
                      zipf.write(file, arcname=file.name)
                      file.unlink()  # Orijinal dosyayı sil
                      logging.info(f"Compressed and removed: {file.name}")
                  except Exception as e:
                      logging.error(f"Error compressing {file.name}: {e}")

          logging.info(f"Compression completed. Archive: {latest_rar}")

      except Exception as e:
          logging.error(f"Compression error: {e}")

    def clean_trash(self):
        trash_path = self.config.BASE_DIRS['TRASH']
        now = datetime.now()
        
        for file in trash_path.iterdir():
            if now - datetime.fromtimestamp(file.stat().st_mtime) > timedelta(days=1):
                try:
                    file.unlink() if file.is_file() else shutil.rmtree(file)
                except Exception as e:
                    logging.error(f"Trash cleanup error: {e}")

class FileWatcher(FileSystemEventHandler):
    def __init__(self, file_manager):
        self.file_manager = file_manager

    def on_created(self, event):
        if not event.is_directory:
            self.file_manager.move_to_category(event.src_path)

def main():
    config = Config()
    file_manager = FileManager(config)
    
    file_manager.categorize_files_in_directory()
    
    file_manager.compress_old_files()
    file_manager.clean_trash()

    observer = Observer()
    observer.schedule(
        FileWatcher(file_manager), 
        str(config.BASE_DIRS['FILES']), 
        recursive=False
    )
    
    try:
        observer.start()
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    main()