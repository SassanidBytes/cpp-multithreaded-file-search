# Parallele Dateisuche in C++

Ein kleines Tool, das ich mir selbst gebaut habe, um in einem ganzen Ordner schnell nach einem bestimmten Wort zu suchen.  
Nutzt mehrere Threads, damit es nicht ewig dauert, wenn viele Dateien drin sind.

## Was es kann

- **Rekursive Suche** – durchsucht alle Dateien in einem Ordner und allen Unterordnern  
- **Multithreading** – verwendet bis zu 8 Threads gleichzeitig, damit der PC nicht abstürzt und die Suche flott läuft  
- **Klare Ausgabe** – zeigt bei jedem Treffer den Dateipfad, die Zeilennummer und den Inhalt der betreffenden Zeile an  
- **Unterstützte Dateien** – funktioniert mit allen normalen Textdateien (`.txt`, `.cpp`, `.log`, `.md`, `.json` usw.)  
- **Spezielle Marker** – die Ausgabe ist so formatiert, dass sie von meiner Python‑GUI (PyQt6) einfach weiterverarbeitet werden kann (z.B. `FOUND:`, `PROGRESS:`, `SEARCH_FINISHED:`)

## Kompilieren

Einfach in der Konsole folgenden Befehl eingeben:

```bash
g++ -std=c++17 -pthread main.cpp -o dateisuche


