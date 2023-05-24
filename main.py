"""ainodes-engine main"""
import glob
#!/usr/bin/env python3

import sys
import os


import subprocess
import platform
import argparse
from types import SimpleNamespace

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QSplashScreen
from qtpy import QtCore, QtQuick, QtWidgets
from qtpy.QtQuick import QSGRendererInterface
from qtpy.QtCore import QCoreApplication
from qtpy import QtGui
from qtpy.QtWidgets import QApplication

subprocess.check_call(["pip", "install", "tqdm"])
from tqdm import tqdm

from ainodes_frontend import singleton as gs

import ainodes_frontend.qss.nodeeditor_dark_resources
from ainodes_frontend.base.settings import save_settings, load_settings
from ainodes_frontend.node_engine.utils import loadStylesheets

# Set environment variable QT_API to use PySide6
os.environ["QT_API"] = "pyside6"
# Install Triton if running on Linux
if "Linux" in platform.platform():
    print(platform.platform())
    subprocess.check_call(["pip", "install", "triton==2.0.0"])
if "Linux" in platform.platform():
    gs.qss = "ainodes_frontend/qss/nodeeditor-dark-linux.qss"
else:
    gs.qss = "ainodes_frontend/qss/nodeeditor-dark.qss"


def update_all_nodes_req():
    top_folder = "./custom_nodes"
    folders = [folder for folder in os.listdir(top_folder) if os.path.isdir(os.path.join(top_folder, folder))]

    for folder in tqdm(folders, desc="Folders"):
        repository = f"{top_folder}/{folder}"
        # command = f"git -C {repository} stash && git -C {repository} pull && pip install -r {repository}/requirements.txt"
        command = f"git -C {repository} pull && pip install -r {repository}/requirements.txt"

        print("RUNNING COMMAND", command)

        with tqdm(total=100, desc=f"Updating {folder}") as pbar:
            result = subprocess.run(command, shell=True, stdout=None, stderr=None,
                                    universal_newlines=True)
            pbar.update(50)  # Indicate that git pull is 50% complete
            pbar.set_description(f"Installing {folder}'s requirements")
            pbar.update(50)  # Indicate that requirements installation is 50% complete

def import_nodes_from_directory(directory):
    if "ainodes_backend" not in directory and "backend" not in directory:
        node_files = glob.glob(os.path.join(directory, "*.py"))
        for node_file in node_files:
            f = os.path.basename(node_file)
            if f != "__init__.py" and "_node" in f:
                module_name = os.path.basename(node_file)[:-3].replace('/', '.')
                dir = directory.replace('/', '.')
                dir = dir.replace('\\', '.').lstrip('.')
                exec(f"from {dir} import {module_name}")

def import_nodes_from_subdirectories(directory):
    print("Importing from", directory)
    if "ainodes_backend" not in directory and "backend" not in directory:

                #if return_code != 0:
                #    error_output = process.stderr.read().strip()
                #    raise subprocess.CalledProcessError(return_code, command, output=error_output)

        for subdir in os.listdir(directory):
            subdir_path = os.path.join(directory, subdir)
            if os.path.isdir(subdir_path) and subdir != "base":
                import_nodes_from_directory(subdir_path)

# Initialize global variables
gs.obj = {}
gs.values = {}
gs.current = {}
gs.nodes = {}
gs.system = SimpleNamespace()
gs.busy = False
gs.models = {}
gs.token = ""
gs.use_deforum_loss = None
gs.highlight_sockets = True
gs.loaded_sd = ""
gs.current = {}
gs.loaded_vae = ""
gs.logging = True
gs.debug = None
gs.hovered = None
gs.loaded_loras = []
gs.metas = "output/metas"
gs.system.textual_inversion_dir = "models/embeddings"
gs.error_stack = []
gs.should_run = True

try:
    import xformers
    gs.system.xformer = True
except:
    gs.system.xformer = False

gs.current["sd_model"] = None
gs.current["inpaint_model"] = None
gs.loaded_vae = ""





# Parse command line arguments
parser = argparse.ArgumentParser()
#Local Huggingface Hub Cache
parser.add_argument("--local_hf", action="store_true")
parser.add_argument("--skip_base_nodes", action="store_true")
parser.add_argument("--light", action="store_true")
parser.add_argument("--skip_update", action="store_true")
parser.add_argument("--update", action="store_true", default=False)
parser.add_argument("--torch2", action="store_true")
parser.add_argument("--no_console", action="store_true")
parser.add_argument("--highdpi", action="store_true")
parser.add_argument("--forcewindowupdate", action="store_true")
args = parser.parse_args()
gs.args = args

# Set environment variables for Hugging Face cache if not using local cache
if not args.local_hf:
    print("Using HF Cache in app dir")
    os.makedirs("hf_cache", exist_ok=True)
    os.environ["HF_HOME"] = "hf_cache"

if args.highdpi:
# Set up high-quality QSurfaceFormat object with OpenGL 3.3 and 8x antialiasing
    qs_format = QtGui.QSurfaceFormat()
    qs_format.setVersion(3, 3)
    qs_format.setSamples(8)
    qs_format.setProfile(QtGui.QSurfaceFormat.CoreProfile)
    QtGui.QSurfaceFormat.setDefaultFormat(qs_format)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    QtQuick.QQuickWindow.setGraphicsApi(QSGRendererInterface.OpenGLRhi)
def eventListener(*args, **kwargs):
    print("EVENT")



def check_repo_update(folder_path):
    repo_path = folder_path
    try:
        # Run 'git fetch' to update the remote-tracking branches
        subprocess.check_output(['git', '-C', repo_path, 'fetch'])

        # Get the commit hash of the remote 'origin/master' branch
        remote_commit_hash = subprocess.check_output(
            ['git', '-C', repo_path, 'ls-remote', '--quiet', '--refs', 'origin',
             'refs/heads/main']).decode().strip().split()[0]

        # Get the commit hash of the local branch
        local_commit_hash = subprocess.check_output(['git', '-C', repo_path, 'rev-parse', 'HEAD']).decode().strip().split()[0]

        if local_commit_hash != remote_commit_hash:
            return True
        else:
            return None
    except subprocess.CalledProcessError as e:
        print(e)
        return None
# make app
app = QApplication(sys.argv)
splash_pix = QPixmap("ainodes_frontend/qss/icon.ico")  # Replace "splash.png" with the path to your splash screen image
splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
splash.show()


load_settings()
base_folder = 'custom_nodes'
if args.update:
    update_all_nodes_req()

for folder in os.listdir(base_folder):
    folder_path = os.path.join(base_folder, folder)
    if "__pycache__" not in folder_path and "_nodes" in folder_path:
        if os.path.isdir(folder_path):
            import_nodes_from_subdirectories(folder_path)

if __name__ == "__main__":
    # Create and display the splash screen
    # Enable automatic updates for the entire application
    if args.highdpi:
        app.setAttribute(Qt.AA_EnableHighDpiScaling)

    QCoreApplication.instance().aboutToQuit.connect(eventListener)
    app.setApplicationName("aiNodes - Engine")
    from ainodes_frontend.base import CalculatorWindow
    # Create and show the main window
    wnd = CalculatorWindow(app)
    wnd.stylesheet_filename = os.path.join(os.path.dirname(__file__), gs.qss)
    loadStylesheets(
        os.path.join(os.path.dirname(__file__), gs.qss),
        wnd.stylesheet_filename
    )
    if not args.skip_base_nodes:
        wnd.node_packages.list_widget.setCurrentRow(0)
        if not os.path.isdir('custom_nodes/ainodes_engine_base_nodes'):
            wnd.node_packages.download_repository()
    wnd.setWindowIconText("aiNodes - Engine")
    icon = QtGui.QIcon("ainodes_frontend/qss/icon.ico")
    wnd.setWindowIcon(icon)
    app.setWindowIcon(icon)
    wnd.show()
    wnd.nodesListWidget.addMyItems()
    wnd.onFileNew()
    if args.torch2 == True:
        from custom_nodes.ainodes_engine_base_nodes.ainodes_backend.sd_optimizations.sd_hijack import apply_optimizations
        apply_optimizations()
    if args.forcewindowupdate:
        # Create a timer to trigger the update every second
        timer = QtCore.QTimer()
        timer.timeout.connect(wnd.update)
        timer.start(1000)  # 1000 milliseconds = 1 second
    splash.finish(wnd)

    sys.exit(app.exec())
