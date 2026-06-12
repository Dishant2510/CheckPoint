# CheckPoint 

CheckPoint is a production-grade, universal PC game save backup and restore manager. Built for power users, collectors, and gamers who want to ensure their progress is never lost.
Installable .exe file -  https://drive.google.com/drive/folders/1AgrJfbw6mvv2tMUZtDTbWxiKHo1B91A6?usp=drive_link

##  Features

- **Automatic Backups**: Detects when you finish playing a game and saves your progress instantly.
- **Universal Support**: Works with Steam, Epic Games, emulators, and local installations.
- **Save Detection Engine**: Heuristic and signature-based scanning for 50+ popular titles.
- **Snapshot Management**: Keep multiple versions of your saves and roll back any time.
- **Storage Analytics**: Beautiful dashboard showing how much space your backups are using.
- **Modern UI**: Polished "Dark Gaming" aesthetic built with CustomTkinter.
- **Safe Delete Flow**: Warns you to backup saves before uninstalling games.

##  Tech Stack

- **Languge**: Python 3.12+
- **UI Framework**: CustomTkinter
- **Database**: SQLite (Thread-safe WAL mode)
- **Monitoring**: psutil & watchdog
- **Processing**: zipfile (Deflate compression)

##  Getting Started

### Prerequisites

- Python 3.12 or higher.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Dishant2510/checkpoint.git
   cd checkpoint
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

##  Packaging & Installer Setup

### 1. Compile the Executable (EXE)

To bundle the Python application into a standalone folder:

```bash
pip install pyinstaller
pyinstaller checkpoint.spec
```

The output files will be compiled into the `dist/CheckPoint/` directory.



### 2. Generate the Installer (Windows Setup)

We use **Inno Setup** (the industry standard for Windows installers) to package the application folder into a single setup wizard.

1. Download and install [Inno Setup](https://jrsoftware.org/isdl.php).
2. Open Inno Setup and open the `installer.iss` file located in the root of the project.
3. Press **Ctrl + F9** (or go to `Build > Compile` in the menu).
4. Once compiling is complete, you will find the standalone installer `CheckPointSetup.exe` inside the `installer_dist/` directory.

This installer will:
* Install the files in `C:\Program Files\CheckPoint`
* Create Start Menu and Desktop shortcuts (optional)
* Create a registry-based Windows uninstaller so users can uninstall it cleanly via Settings / Control Panel.

##  Architecture

The project follows a modular layered architecture:

- `app/ui`: CustomTkinter screens and reusable components.
- `app/services`: Core business logic for backups, restores, and storage.
- `app/database`: Persistence layer using SQLite Repository pattern.
- `app/monitoring`: Background process and file system trackers.
- `app/utils`: Configuration, logging, and OS path resolution.
- `data`: Game signatures and default configurations.

##  License

This project is licensed under the MIT License.
