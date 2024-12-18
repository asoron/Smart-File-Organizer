# Smart File Organizer

This project provides an automated solution for managing desktop files. It intelligently categorizes files, compresses old data, cleans the trash, and ensures efficient resource usage. Simply run the provided .exe file to begin enjoying a clutter-free workspace.

## Features

*   **Automated File Categorization:** Sorts files by extension (documents, images, videos, etc.) into designated folders.
*   **Intelligent Resource Management:** Monitors CPU and RAM usage, halting operations to prevent system overload.
*   **Old File Compression:** Archives files that haven't been accessed in a while to save disk space.
*   **Trash Cleanup:** Automatically deletes files from the trash after a set period.
*   **User-Friendly Interface:** A sleek, dark-themed interface built with PyQt5, accessible from the system tray.
*   **Robust File Search:** Quickly locate files by name or extension, supporting Turkish character variations.
*   **Customizable Settings:** Adjust resource limits, base directories, and other settings via a simple interface.
*   **Comprehensive Logging:** Records all operations for easy troubleshooting and tracking.

## How It Works

1.  **File System Monitoring:** Uses `watchdog` to track file changes.
2.  **Intelligent Categorization:** Sorts files based on their extensions.
3.  **Resource Management:** Utilizes `psutil` to monitor CPU and RAM usage.
4.  **Automated Compression:** Compresses old files using `zipfile`.
5.  **Scheduled Cleanup:** Deletes trash files after a defined period.
6.  **Intuitive UI:** Provides a user-friendly interface with PyQt5.

## Installation

1.  **Download:** Obtain the pre-built .exe file from the repository.
2.  **Run:** Execute the .exe file. No further installation is required.

## Usage

*   The application runs in the system tray.
*   Access settings, search, and exit options by right-clicking the tray icon.
*   Customize settings via the user interface.
*   Search for files using the built-in search tool.
