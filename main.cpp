#include <iostream>
#include <filesystem>
#include <fstream>
#include <vector>
#include <thread>
#include <mutex>
#include <string>
#include <algorithm>
#include <cctype>
#include <atomic>
#include <chrono>

namespace fs = std::filesystem;

std::mutex coutMutex;
std::atomic<int> filesProcessed{ 0 };
int totalFiles = 0;

// Nur Textdateien durchsuchen
bool is_text_file(const fs::path& p)
{
    std::string ext = p.extension().string();
    if (ext.empty()) return false;

    // In Kleinbuchstaben umwandeln
    std::transform(ext.begin(), ext.end(), ext.begin(),
        [](unsigned char c) { return std::tolower(c); });

    static const std::vector<std::string> text_ext = {
        ".txt", ".cpp", ".h", ".hpp", ".c", ".cxx", ".cc",
        ".cs", ".py", ".java", ".js", ".ts", ".jsx", ".tsx",
        ".html", ".htm", ".css", ".xml", ".json", ".md",
        ".log", ".csv", ".ini", ".cfg", ".yml", ".yaml"
    };

    for (const auto& e : text_ext) {
        if (ext == e) return true;
    }
    return false;
}

// Sichere Suchfunktion in einer Datei
void searchInFile(const fs::path& file, const std::string& word)
{
    try {
        std::ifstream inFile(file);
        if (!inFile.is_open()) {
            return;
        }

        std::string line;
        int lineNumber = 0;

        while (std::getline(inFile, line))
        {
            ++lineNumber;
            if (line.find(word) != std::string::npos)
            {
                // Spezielles Format: FOUND: Pfad|Zeile|Text
                std::cout << "FOUND: " << file.string() << "|" << lineNumber << "|" << line << std::endl;
            }
        }

        // Fortschritt aktualisieren
        int processed = ++filesProcessed;
        if (totalFiles > 0) {
            std::cout << "PROGRESS: " << (processed * 100 / totalFiles) << std::endl;
        }
    }
    catch (const std::exception& e) {
        // Nur im Debug-Modus Fehler ausgeben
#ifdef _DEBUG
        std::lock_guard<std::mutex> lock(coutMutex);
        std::cerr << "Error reading " << file.string() << ": " << e.what() << std::endl;
#endif
    }
}

int main(int argc, char* argv[])
{
    auto start = std::chrono::steady_clock::now();

    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " <word> <folderpath> <threads>" << std::endl;
        return 1;
    }

    std::string word = argv[1];
    fs::path folder = argv[2];
    int maxThreads = std::stoi(argv[3]);

    // Thread-Anzahl begrenzen
    if (maxThreads < 1) maxThreads = 1;
    if (maxThreads > 32) maxThreads = 32;

    if (!fs::exists(folder) || !fs::is_directory(folder)) {
        std::cerr << "Ordner existiert nicht oder ist kein Verzeichnis: " << folder << std::endl;
        return 1;
    }

    std::vector<fs::path> files;

    std::cout << "Sammle Dateien... (nur Textdateien)" << std::endl;

    try {
        for (const auto& entry : fs::recursive_directory_iterator(
            folder,
            fs::directory_options::skip_permission_denied))
        {
            if (entry.is_regular_file() && is_text_file(entry.path())) {
                files.push_back(entry.path());
            }
        }
    }
    catch (const fs::filesystem_error& e) {
        std::cerr << "Hinweis: Konnte einige Ordner nicht betreten: " << e.path1() << std::endl;
    }
    catch (const std::exception& e) {
        std::cerr << "Fehler beim Sammeln der Dateien: " << e.what() << std::endl;
        return 1;
    }

    totalFiles = files.size();
    filesProcessed = 0;

    std::cout << "gefundene Textdateien: " << files.size() << std::endl;

    // Threads mit der angegebenen Anzahl starten
    std::vector<std::thread> threads;

    size_t fileIndex = 0;

    while (fileIndex < files.size()) {
        // Neue Threads starten bis zum Maximum
        while (threads.size() < maxThreads && fileIndex < files.size()) {
            threads.emplace_back(searchInFile, std::cref(files[fileIndex]), std::cref(word));
            fileIndex++;
        }

        // Prüfen ob ein Thread fertig ist
        for (auto& t : threads) {
            if (t.joinable()) {
                t.join();
                // Thread aus vector entfernen
                std::vector<std::thread> newThreads;
                for (auto& remaining : threads) {
                    if (remaining.get_id() != t.get_id()) {
                        newThreads.push_back(std::move(remaining));
                    }
                }
                threads = std::move(newThreads);
                break;
            }
        }
    }

    // Alle restlichen Threads warten
    for (auto& t : threads) {
        if (t.joinable()) {
            t.join();
        }
    }

    auto end = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    std::cout << "\nSEARCH_FINISHED: " << (duration / 1000.0) << " seconds using " << maxThreads << " threads." << std::endl;

    return 0;
}
