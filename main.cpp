#include <iostream>
#include <filesystem>
#include <fstream>
#include <vector>
#include <thread>
#include <mutex>
#include <string>  // für std::string und std::getline

namespace fs = std::filesystem;
std::mutex coutMutex;

// Funktion durchsucht eine Datei nach einem Wort
void searchInFile(const fs::path& file, const std::string& word)
{
    std::ifstream inFile(file);
    if (!inFile.is_open()) {
        return;
    }
    std::string line;
    int lineNumber = 0;
    while (std::getline(inFile, line))
    {
        lineNumber++;
        if (line.find(word) != std::string::npos)
        {
            std::lock_guard<std::mutex> lock(coutMutex);
            std::cout << "Found in: " << file
                << " line " << lineNumber
                << ": " << line << std::endl;
        }
    }
}

int main(int argc, char* argv[])
{
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " <word> <folderpath>" << std::endl;
        return 1;
    }

    std::string word = argv[1];
    fs::path folder = argv[2];

    if (!fs::exists(folder) || !fs::is_directory(folder)) {
        std::cerr << "Ordner existiert nicht oder ist kein Verzeichnis: " << folder << std::endl;
        return 1;
    }

    std::vector<fs::path> files;
    for (const auto& entry : fs::recursive_directory_iterator(folder)) {
        if (entry.is_regular_file()) {
            files.push_back(entry.path());
        }
    }

    std::vector<std::thread> threads;
    const int MAX_THREADS = 8;  // nicht zu viele gleichzeitig

    for (const auto& file : files) {
        threads.emplace_back(searchInFile, file, word);

        if (threads.size() >= MAX_THREADS) {
            threads.front().join();
            threads.erase(threads.begin());
        }
    }

    // restliche Threads warten
    for (auto& t : threads) {
        t.join();
    }

    std::cout << "Search finished." << std::endl;
    return 0;
}
