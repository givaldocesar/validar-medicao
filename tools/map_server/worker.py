import os, sys, subprocess
import importlib, site, zipfile
from qgis.PyQt.QtCore import QThread, pyqtSignal

class MapServerSetupWorker(QThread):
    progress_text = pyqtSignal(str)
    progress_value = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, drive_url, extract_path):
        super().__init__()
        self.drive_url = drive_url
        self.extract_path = extract_path

    def run(self):
        try:
            self.progress_text.emit("Verificando biblioteca gdown")
            self.progress_value.emit(5)

            try:
                import gdown
            except ImportError:
                self.progress_text.emit("Instalando gdown no QGIS...")
                
                python_exe = os.path.join(sys.exec_prefix, 'python.exe')
                if not os.path.exists(python_exe):
                    python_exe = os.path.join(sys.exec_prefix, 'bin', 'python3')

                subprocess.check_call([python_exe, "-m", "pip", "install", "gdown"])
                importlib.reload(site)
                import gdown

            self.progress_text.emit("gdown instalado com sucesso!")
            self.progress_value.emit(10)
            self.progress_text.emit("Verificando instalação local do MapServer...")
            self.progress_value.emit(15)

            os.makedirs(self.extract_path, exist_ok=True)
            exe_path = os.path.join(self.extract_path, "mapserv.exe")

            if os.path.exists(exe_path):
                self.progress_text.emit("MapServer encontrado!")
                self.progress_value.emit(100)
                self.finished.emit(True, "MapServer já está instalado.")
                return
        
            self.progress_text.emit("Baixando MapServer...")
            self.progress_value.emit(20)
            zip_path = os.path.join(self.extract_path, "mapserver_download.zip")
            self.progress_value.emit(25)
            gdown.download(self.drive_url, zip_path, quiet=True)
            if not os.path.exists(zip_path):
                raise Exception("Falha ao baixar o arquivo do Google Drive.")
            
            self.progress_text.emit("Extraindo arquivos...")
            self.progress_value.emit(75)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_path)
            
            os.remove(zip_path)
            self.progress_text.emit("Instalação concluída!")
            self.progress_value.emit(100)
            self.finished.emit(True, "MapServer baixado e instalado com sucesso.")

        except Exception as e:
            self.finished.emit(False, str(e))