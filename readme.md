# Vibe Code Productivity App

A retro-themed desktop application for tracking tasks, study time, and weight, complete with a Pokémon Red-inspired UI and background music. This app is designed to be a fun and motivating tool to help you stay on top of your goals.

---

## Features

-   **Task Management:** Create and complete daily tasks in a simple, straightforward list.
-   **Focus Timer:** A stopwatch to track study or work sessions. Time is automatically logged by day.
-   **Weight Tracker:** Log your weight daily and view your history. Missed days are automatically back-filled with the last known weight.
-   **Statistics Dashboard:** Get insights into your productivity with stats like total hours studied, weekly averages, and total weight change.
-   **Retro UI:** A fun, pixelated interface inspired by the classic Pokémon Red game.
-   **Background Music:** Randomly plays one of the included chiptune tracks to help you vibe while you code or study.

---

## Installation and Running

Follow these instructions to run the application on your local machine for development or personal use.

### Prerequisites

-   [Python 3.8+](https://www.python.org/downloads/)
-   `pip` (Python's package installer)
-   `venv` (for creating virtual environments)
-   `git` (for cloning the repository)

### Steps

1.  **Clone the Repository**
    Open your terminal or command prompt and clone this repository to your local machine.
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Create and Activate a Virtual Environment**
    It is highly recommended to use a virtual environment to keep project dependencies isolated.

    * **On Ubuntu/macOS:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

    * **On Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install Dependencies**
    With your virtual environment activated, install all the required packages from the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application**
    You're all set! Run the main script to launch the app.
    ```bash
    python3 productivity_app.py
    ```

---

## Building the Standalone Desktop App

Follow these instructions to package the script into a single, standalone executable that can be run without installing Python or any dependencies.

### On Ubuntu / Linux

This process will create a native Linux executable and a `.desktop` file for system integration.

1.  **Install PyInstaller:**
    Make sure you are in your activated virtual environment.
    ```bash
    pip install pyinstaller
    ```

2.  **Build the Executable:**
    Run the `pyinstaller` command from the project's root directory. This command bundles your script, assets (music files), and an icon.
    ```bash
    # Note: The -i flag is ignored on Linux but is useful for cross-compilation context.
    # The icon is set via the .desktop file.
    pyinstaller --onefile --windowed \
      --add-data "music.ogg:." \
      --add-data "music.mp3:." \
      --add-data "music2.ogg:." \
      --add-data "music2.mp3:." \
      -i "icon.png" \
      productivity_app.py
    ```

3.  **Make it Globally Executable (Optional):**
    Move the generated app from the `dist/` folder to a system-wide location.
    ```bash
    sudo mv dist/productivity_app /usr/local/bin/prod-app
    ```

4.  **Create a Desktop Entry for Icons & Pinning (Optional):**
    To make the app appear in your applications menu with its icon, create a `.desktop` file.

    * First, copy the icon to a system directory:
        ```bash
        sudo cp icon.png /usr/share/pixmaps/prod-app.png
        ```

    * Next, create and edit the desktop file:
        ```bash
        nano ~/.local/share/applications/prod-app.desktop
        ```

    * Paste the following content into the file, then save and exit (`Ctrl+X`, `Y`, `Enter`):
        ```ini
        [Desktop Entry]
        Version=1.0
        Name=Prod App
        Comment=A productivity and tracking application
        Exec=/usr/local/bin/prod-app
        Icon=/usr/share/pixmaps/prod-app.png
        Terminal=false
        Type=Application
        Categories=Utility;Application;
        ```

### On Windows

This process will create a native `.exe` file that can be shared with any Windows user.

1.  **Install PyInstaller:**
    Make sure you are in your activated virtual environment.
    ```bash
    pip install pyinstaller
    ```

2.  **Build the Executable:**
    Run the `pyinstaller` command from the project's root directory. This command bundles your script, assets, and embeds the icon directly into the `.exe`.

    **Note:** Windows uses a semicolon (`;`) as the separator in the `--add-data` flag.
    ```bash
    pyinstaller --onefile --windowed ^
      --add-data "music.ogg;." ^
      --add-data "music.mp3;." ^
      --add-data "music2.ogg;." ^
      --add-data "music2.mp3;." ^
      -i "icon.png" ^
      productivity_app.py
    ```
    *(The `^` character is used to continue a command on a new line in the Windows Command Prompt. If using PowerShell, use a backtick `` ` `` instead.)*

3.  **Find Your App:**
    Your final application, **`productivity_app.exe`**, will be located in the `dist` folder. You can now run this file on any Windows computer. To share it, simply compress the `dist` folder into a `.zip` file.

    okdd