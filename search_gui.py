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

    
#--------------------------------------------------#
# Ausgabe des C++-Programms wird verarbeitet
#--------------------------------------------------#

    
    def handle_output(self):
        """Wird jedes Mal aufgerufen, wenn das C++-Programm etwas auf stdout schreibt."""
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue

            # Mein C++-Programm gibt spezielle Marker aus, damit ich die Daten gut auseinanderhalten kann
            if line.startswith("FOUND:"):
                # Fundstelle – leite direkt weiter an die GUI
                self.output_received.emit(line)
            elif line.startswith("PROGRESS:"):
                # Fortschrittswert zwischen 0 und 100
                try:
                    progress = int(line.split(":")[1].strip())
                    self.progress_received.emit(progress)
                except:
                    pass
            elif line.startswith("SEARCH_FINISHED:"):
                # Am Ende kommt z.B. "SEARCH_FINISHED: 2.34 seconds using 8 threads"
                try:
                    parts = line.split(":")[1].strip().split(" seconds using ")
                    seconds = float(parts[0])
                    used_threads = int(parts[1].split()[0])
                    self.finished_signal.emit(seconds, used_threads)
                except:
                    # Falls das Parsen schiefgeht, zeig die Zeile einfach als normale Ausgabe
                    self.output_received.emit(line)
            else:
                # Alles andere (z.B. Debug-Ausgaben) zeig ich auch an
                self.output_received.emit(line)


    def handle_error(self):
            """Fehlerausgaben des C++-Programms werden hier abgefangen."""
            data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if data.strip():
                self.output_received.emit("STDERR: " + data.strip())

        def stop(self):
            """Wird aufgerufen, wenn der Benutzer abbrechen will."""
            if self.process and self.process.state() == QProcess.ProcessState.Running:
                self.process.kill()   # hartes Beenden – reicht für mein Tool


    class MainWindow(QMainWindow):
        """Das Hauptfenster der GUI."""

            def __init__(self):
            super().__init__()
            self.setWindowTitle("TextSearch")
            self.resize(1000, 700)

            self.worker = None      # wird später der SearchWorker
            self.results = []       # hier speicher ich die gefundenen Zeilen (für die Zählung)

            self.init_ui()

        def init_ui(self):
        """Baut die komplette Oberfläche zusammen."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)

        # === Suchparameter als GroupBox mit FormLayout (übersichtlich) ===
        param_group = QGroupBox("Suchparameter")
        param_layout = QFormLayout()
        param_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.word_edit = QLineEdit()
        self.word_edit.setPlaceholderText("z.B. TODO oder Fehlerbehandlung")
        self.word_edit.returnPressed.connect(self.start_search)  # Enter startet sofort

        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Ordner zum Durchsuchen...")
        self.folder_edit.setReadOnly(True)   # Benutzer soll nur über den Button auswählen

        browse_btn = QPushButton("Durchsuchen...")
        browse_btn.clicked.connect(self.browse_folder)

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(browse_btn)

        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 32)
        self.threads_spin.setValue(8)           # Standardwert
        self.threads_spin.setSuffix(" Threads")

        param_layout.addRow("Suchbegriff:", self.word_edit)
        param_layout.addRow("Ordner:", folder_layout)
        param_layout.addRow("Threads:", self.threads_spin)

        param_group.setLayout(param_layout)
        layout.addWidget(param_group)


        #--------------------------------------------------#
        # === Buttons zum Starten/Abbrechen ===
        #--------------------------------------------------#


        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Suche starten")
        self.start_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.start_btn.clicked.connect(self.start_search)

        self.stop_btn = QPushButton("Suche abbrechen")
        self.stop_btn.setEnabled(False)   # am Anfang deaktiviert
        self.stop_btn.clicked.connect(self.stop_search)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # === Fortschrittsbalken ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        # FIX: Farbe des Fortschrittsbalkens auch bei inaktivem Fenster beibehalten
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3daee9;
                width: 10px;
                margin: 0.5px;
            }
        """)






