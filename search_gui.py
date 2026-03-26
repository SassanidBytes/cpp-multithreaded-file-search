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



#-----------------------------------------------------------#
# Thread, der das C++-Programm startet und die Ausgabe liest
#-----------------------------------------------------------#


class SearchWorker(QThread):
    """
    Dieser Thread startet das C++-Suchprogramm und liest dessen Ausgabe.
    Ich hab's als QThread gemacht, damit die GUI nicht einfriert während der Suche.
    """

    # Signale, um Daten zurück an das Hauptfenster zu schicken
    output_received = pyqtSignal(str)          # für Fundstellen und Fehler
    progress_received = pyqtSignal(int)        # für den Fortschrittsbalken
    finished_signal = pyqtSignal(float, int)   # am Ende: Zeit und genutzte Threads

    def __init__(self, word: str, folder: str, threads: int):
        super().__init__()
        self.word = word
        self.folder = folder
        self.threads = threads
        self.process = None   # wird später das QProcess-Objekt

    def run(self):
        """Wird automatisch aufgerufen, wenn der Thread gestartet wird."""
        # Ich hab das C++-Programm unter Windows als textsearch.exe 
        if os.name == "nt":
            exe_path = "textsearch.exe"
        else:
            exe_path = "./textsearch"



        #--------------------------------------------------#
        # Prüfen, ob die ausführbare Datei überhaupt da ist
        #--------------------------------------------------#
        
        if not os.path.exists(exe_path):
            self.output_received.emit(f"FEHLER: {exe_path} nicht gefunden!")
            return

        try:
            # QProcess startet das externe Programm und liest stdout/stderr asynchron
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_output)
            self.process.readyReadStandardError.connect(self.handle_error)

            # Das C++-Programm erwartet: suchwort ordner anzahl_threads
            args = [self.word, self.folder, str(self.threads)]
            self.process.start(exe_path, args)

            # Kurz warten, ob es starten konnte
            if not self.process.waitForStarted(5000):
                self.output_received.emit("Fehler: Konnte das Suchprogramm nicht starten.")
                return

            # Jetzt warten, bis das Programm fertig ist (blockiert, aber der Thread ist ja separat)
            self.process.waitForFinished(-1)

        except Exception as e:
            self.output_received.emit(f"Fehler beim Ausführen: {e}")





