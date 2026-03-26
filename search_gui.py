import sys
import subprocess
import os
from pathlib import Path

# PyQt6 imports – hab ich für die GUI gebraucht
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QProcess
from PyQt6.QtGui import QFont, QIcon
