# Parallele Dateisuche in C++

Ein kleines Tool, das ich mir  selbst gebaut habe, um in einem ganzen Ordner schnell nach einem bestimmten Wort zu suchen.  
Nutzt mehrere Threads, damit es nicht ewig dauert, wenn viele Dateien drin sind.

## Was es kann
- Rekursive Suche durch alle Dateien
- Multithreading (max. 8 Threads gleichzeitig, damit der PC nicht abstürzt)
- Zeigt die Datei, die Zeilennummer **und** die ganze Zeile mit dem Treffer an
- Funktioniert mit normalen Textdateien (.txt, .cpp, .log, .md …)

## Kompilieren
```bash
g++ -std=c++17 -pthread main.cpp -o dateisuche
