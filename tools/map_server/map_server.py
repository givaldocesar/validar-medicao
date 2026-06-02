import os, threading, traceback, re, time
from http.server import ThreadingHTTPServer
from osgeo import gdal
from qgis.core import QgsApplication, Qgis, QgsProject, QgsRasterLayer, QgsSettings, QgsMessageLog
from qgis.PyQt.QtWidgets import QProgressDialog
from qgis.PyQt.QtCore import QTimer
from ..utils import *
from .worker import *
from .map_handler import *
from .create_layer import *
from .create_map_config import *
from .layers_dialog import *

MESSAGE_TITLE = "Servidor de Aerolevantamentos"

class MapServer:
    def __init__(self, iface, tr):
        self.iface = iface
        self.directory = os.path.join(QgsApplication.qgisSettingsDirPath(), 'mapserver_local')
        self.server = None
        self.server_thread = None
        self.tr = tr

    def configUI(self):
        self.progress_dialog = QProgressDialog("Iniciando verificação...", "Cancelar", 0, 100, self.iface.mainWindow())
        self.progress_dialog.setWindowTitle("Configurando Servidor WMS")
        self.progress_dialog.setModal(True)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.resize(500, 100)
        self.progress_dialog.show()

    def create_map_conf(self):
        conf_path = os.path.join(self.directory, "mapserv.conf")
        proj_lib, gdal_data = get_global_proj_gdal()

        gdal_driver_path = self.directory.replace("\\", "/")

        conf_content = f"""CONFIG
    ENV
        MS_MAP_PATTERN ".*"
        PROJ_LIB "{proj_lib}"
        PROJ_DATA "{proj_lib}"
        GDAL_DATA "{gdal_data}"
        GDAL_DRIVER_PATH "{gdal_driver_path}"
    END
    MAPS
        AEROLEVANTAMENTOS "config.map" 
    END
END
"""
        with open(conf_path, "w", encoding="utf-8") as f:
                f.write(conf_content)
        
        os.environ['MAPSERVER_CONFIG_FILE'] = conf_path

    def create_map_file(self, configs, map_file):
        self.iface.messageBar().pushMessage(MESSAGE_TITLE, "Lendo arquivos nos diretórios selecionados...", level=Qgis.Info)

        layers = []
        layer_blocks = ""

        for product_type, product_dir in configs.items():
            if not product_dir or not os.path.exists(product_dir):
                self.iface.messageBar().pushMessage(MESSAGE_TITLE, 
                    f"{product_type}: O diretório '{product_dir}' é inválido ou não existe.", level=Qgis.Warning )
                continue

            sub_directories = [directory for directory in os.listdir(product_dir) if os.path.isdir(os.path.join(product_dir, directory))]

            # CRIA AS CAMADAS
            for sub_directory in sub_directories:
                path = os.path.join(product_dir, sub_directory)
                images = []

                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(('.ecw', '.tif')):
                           images.append(os.path.join(root, file).replace("\\", "/"))
                
                if images:
                    regex = re.search(r'\d{4}', sub_directory)
                    year = regex.group() if regex else "Outros"

                    group_name = f"{product_type} {year}"
                    clean_title = f"{product_type} - {sub_directory.replace("_", " ").title()}"
                    clean_name = f"{product_type.replace(" ", "_")}_{sub_directory.replace(" ", "_")}"
                    
                    vrt_path = os.path.join(path, f"mosaic_{clean_name}.vrt").replace("\\", "/")
                    vrt_options = gdal.BuildVRTOptions(resolution="highest")
                    gdal.BuildVRT(vrt_path, images, options=vrt_options)

                    layers.append((clean_name, clean_title, group_name))
                    layer_blocks += create_layer(clean_name, vrt_path, clean_title, year, product_type)

        if layer_blocks:
            # CRIA O MAP CONFIG
            map_content = create_map_config(self.directory, layer_blocks)
            with open(map_file, "w", encoding="utf-8") as file:
                file.write(map_content)
        
        return layers

    def start(self):
        if self.server is not None:
            self.iface.messageBar().pushMessage(MESSAGE_TITLE, "O Servidor já está em execução!")
            return
        
        port = 8080
        proj_lib, gdal_data = get_global_proj_gdal()

        try:
            MapHandler = create_map_handler(self.directory, proj_lib, gdal_data)
            self.server = ThreadingHTTPServer(('localhost', port), MapHandler)
            
            def run_server():
                try:
                    self.server.serve_forever()
                except:
                    pass
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            self.iface.messageBar().pushMessage(MESSAGE_TITLE, "Servidor INICIADO com sucesso!", level=Qgis.Success)

        except OSError:
            self.iface.messageBar().pushMessage("Erro de Rede", f"A porta {port} está bloqueada ou em uso.", level=Qgis.Critical)
    
    def stop(self):
        if self.server:
            def shutdown():
                self.server.shutdown()
                self.server.server_close()
                self.server = None
                self.server_thread = None

            thread_shutdown = threading.Thread(target=shutdown)
            thread_shutdown.start()
            
            self.iface.messageBar().pushMessage(MESSAGE_TITLE, "Servidor PARADO!", level=Qgis.Warning)
        else:
            self.iface.messageBar().pushMessage(MESSAGE_TITLE, "O servidor já encontra-se desligado.", level=Qgis.Info)
       
    def reboot(self):
        self.stop()
        
        def restart():
            self.start()
            self.iface.messageBar().pushMessage(MESSAGE_TITLE, "Servidor REINICIADO com sucesso!", level=Qgis.Success)
        
        QTimer.singleShot(1000, restart)

    def create_wms_connection(self):
        url = f"http://localhost:8080/mapserv.exe?map=AEROLEVANTAMENTOS"
        connection = "Aerolevantamentos (CODEVASF)"
        
        settings = QgsSettings()
        settings.setValue(f"qgis/connections-wms/{connection}/url", url)
        settings.setValue(f"qgis/connections-wms/{connection}/ignoreGetMapURI", False)
        settings.setValue(f"qgis/connections-wms/{connection}/ignoreGetFeatureInfoURI", False)
        settings.setValue(f"qgis/connections-wms/{connection}/version", "1.1.1")
        settings.sync()
        self.iface.reloadConnections()
        self.iface.messageBar().pushMessage(MESSAGE_TITLE, "Conexão criada! Escolha o mês desejado na lista e clique em 'Conectar'.", level=Qgis.Success)
    
    def load_layers(self, layers):
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        groups_dict = {}

        for name, title, group_name in layers:
            uri = (
                f"crs=EPSG:31983&format=image/png&layers={name}&styles=&"
                f"url=http://localhost:8080/?map=AEROLEVANTAMENTOS&"
                f"ignoreGetMapURI=1&ignoreGetFeatureInfoURI=1&version=1.1.1"
            )

            wms_layer = QgsRasterLayer(uri, title, "wms")

            if wms_layer.isValid():
                legend = group_name
                
                # CRIA O GRUPO OU PESCA
                if legend not in groups_dict:
                    group = root.findGroup(legend)
                    if group:
                        groups_dict[legend] = group
                    else:
                        groups_dict[legend] = root.addGroup(legend)
                    
                #VERIFICA SE A CAMADA JÁ TÁ LÁ
                for node in  groups_dict[legend].children():
                    if node.name() == title:
                        project.removeMapLayer(node.layerId())

                project.addMapLayer(wms_layer, False)
                groups_dict[legend].addLayer(wms_layer)
        
        self.iface.messageBar().pushMessage(MESSAGE_TITLE, "Mosaicos carregados e organizados com sucesso!", level=Qgis.Success)

    def init_setup(self):
        self.configUI() 
        drive_url = 'https://drive.google.com/file/d/1nTtZFGyugutxh7vV2dXkZppDlebNmxgh/view?usp=sharing'

        self.worker =  MapServerSetupWorker(drive_url, self.directory)
        self.worker.progress_text.connect(self.progress_dialog.setLabelText)
        self.worker.progress_value.connect(self.progress_dialog.setValue)
        self.worker.finished.connect(self.setup_finished)
        self.progress_dialog.canceled.connect(self.worker.terminate)
        self.worker.start()
    
    def setup_finished(self, success, message):
        try:
            if(success):
                self.iface.messageBar().pushMessage(MESSAGE_TITLE, message, level=Qgis.Success)

                #Settings
                settings = QgsSettings()
                configs = {
                    self.tr("ORTOFOTOS"): settings.value("validar_medicao/dir_orto", ""),
                    "MDT": settings.value("validar_medicao/dir_mdt", ""),
                    "MDS": settings.value("validar_medicao/dir_mds", ""),
                    self.tr("CURVASD DE NIVEL"): settings.value("validar_medicao/dir_contours", "")
                }
                
                map_file = os.path.join(self.directory, "config.map").replace("\\", '/')
                
                self.create_map_conf()
                layers = self.create_map_file(configs, map_file)
                self.start()
                self.create_wms_connection()

                if layers:
                    dialog = LayersDialog(layers)
                    if dialog.exec_():
                        layers = dialog.get_layers()
                        if layers:
                            self.load_layers(layers)
                        else:
                            self.iface.messageBar().pushMessage(MESSAGE_TITLE, "Nenhum camada foi selecionada.", level=Qgis.Warning)
                else:
                    self.iface.messageBar().pushMessage(MESSAGE_TITLE, f"Error: {message}", level=Qgis.Critical)

            else:
                self.iface.messageBar().pushMessage("Error", f"Problema {message}", level=Qgis.Critical)
        
        except Exception as e:
            complete_error = traceback.format_exc()
            self.iface.messageBar().pushMessage("Erro Oculto", f"O plugin travou: {str(e)}", level=Qgis.Critical)
            QgsMessageLog.logMessage(complete_error, "WMS Local", Qgis.Critical)