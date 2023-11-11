# Rule34 Downloader

- This Python script is a Rule34 posts downloader, enabling users to download images from the Rule34 website based on specified tags. It offers both a command-line interface and a graphical user interface (GUI) using tkinter.

### Features:

- Command-Line Interface (CLI): Users can provide tags, destination folder, download limit, and choose whether to exclude videos using command-line arguments.
- Graphical User Interface (GUI): For users who prefer a visual interface, the script provides a simple GUI using tkinter. Users can input tags, set the destination folder, specify the download limit, and choose whether to exclude videos.
- Error Handling: The script includes error handling for various scenarios, such as failed API requests or issues with creating the destination folder.
Usage:

- CLI: Users can run the script from the command line, providing necessary arguments such as tags, destination, limit, and flags for excluding videos or using the GUI.
Example: python script.py --tags catgirl nekomimi --destination downloads --limit 50 --no-videos

- GUI: Users can run the script with the --gui flag to launch the graphical user interface.

---

### Dependencies:

- The script utilizes the rule34 Python library for interacting with the Rule34 API. Other dependencies include requests, argparse, logging, pathlib, timeit, colorama, and tkinter for the GUI.

---

### Sources:
[Script based on](https://github.com/Kyomuru/Rule34-Downloader/blob/master/main.py)
[Rule34 Library for Python](https://pypi.org/project/rule34/)
