import os, threading, traceback, re
from http.server import ThreadingHTTPServer
from osgeo import gdal
from qgis.core import QgsApplication, Qgis, QgsProject, QgsRasterLayer, QgsSettings, QgsMessageLog
from qgis.PyQt.QtWidgets import QProgressDialog
from ..utils import *
from .worker import *
from .map_handler import *
from .create_layer import *
from .create_map_config import *
from .layers_dialog import *

class IniciarMapServer:
    def __init__(self, iface):
        self.iface = iface

    def configUI(self):
        self.progress_dialog = QProgressDialog("Iniciando verificação...", "Cancelar", 0, 100, self.iface.mainWindow())
        self.progress_dialog.setWindowTitle("Configurando Servidor WMS")
        self.progress_dialog.setModal(True)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.resize(500, 100)
        self.progress_dialog.show()

    def create_map_conf(self):
        conf_path = os.path.join(self.mapserver_dir, "mapserv.conf")
        proj_lib, gdal_data = get_global_proj_gdal()

        gdal_driver_path = self.mapserver_dir.replace("\\", "/")

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

    def create_map_file(self, img_dir, map_file):
        self.iface.messageBar().pushMessage("WMS", "Lendo imagens no servidor SRV061SR...", level=Qgis.Info)

        layers = []
        layer_blocks = ""

        if not os.path.exists(img_dir):
           raise Exception(f"Diretório não encontrado no servidor: {img_dir}")

        months_dir = [directory for directory in os.listdir(img_dir) if os.path.isdir(os.path.join(img_dir, directory))]

        # CRIA AS CAMADAS
        for month in months_dir:
            month_path = os.path.join(img_dir, month)
            month_images = []

            for root, _, files in os.walk(month_path):
                for file in files:
                    if file.lower().endswith(('.ecw', '.tif')):
                        month_images.append(os.path.join(root, file).replace("\\", "/"))
            
            if month_images:
                regex = re.search(r'\d{4}', month)
                year = regex.group() if regex else "Outros"

                clean_name = month.replace(" ", "_")
                clean_title = month.replace("_", " ").title()
                vrt_path = os.path.join(month_path, f"mosaic_{clean_name}.vrt").replace("\\", "/")
                vrt_options = gdal.BuildVRTOptions(resolution="highest")
                gdal.BuildVRT(vrt_path, month_images, options=vrt_options)

                layers.append((clean_name, clean_title, year))
                layer_blocks += create_layer(clean_name, vrt_path, clean_title, year)

        # CRIA O MAP CONFIG
        map_content = create_map_config(self.mapserver_dir, layer_blocks)
        with open(map_file, "w", encoding="utf-8") as file:
            file.write(map_content)
        
        return layers

    def start_server(self):
        port = 8080
       
        def run_server():
            os.chdir(self.mapserver_dir)
            try:
                proj_lib, gdal_data = get_global_proj_gdal()
                MapHandler = create_map_handler(self.mapserver_dir, proj_lib, gdal_data)
                server =ThreadingHTTPServer(('localhost', port), MapHandler)
                server.mapserver_dir_path = self.mapserver_dir
                server.proj_lib, server.gdal_data = get_global_proj_gdal()
                server.serve_forever()
            except OSError:
                pass
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()

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

        self.iface.messageBar().pushMessage("WMS", "Conexão criada! Escolha o mês desejado na lista e clique em 'Conectar'.", level=Qgis.Success)
    
    def load_layers(self, layers):
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        years_dict = {}

        for name, title, year in layers:
            uri = (
                f"crs=EPSG:31983&format=image/png&layers={name}&styles=&"
                f"url=http://localhost:8080/?map=AEROLEVANTAMENTOS&"
                f"ignoreGetMapURI=1&ignoreGetFeatureInfoURI=1&version=1.1.1"
            )

            wms_layer = QgsRasterLayer(uri, title, "wms")

            if wms_layer.isValid():
                legend = f"Ortofotos {year}"
                
                # CRIA O GRUPO OU PESCA
                if year not in years_dict:
                    group = root.findGroup(legend)
                    if group:
                        years_dict[year] = group
                    else:
                        years_dict[year] = root.addGroup(legend)
                    
                #VERIFICA SE A CAMADA JÁ TÁ LÁ
                for node in  years_dict[year].children():
                    if node.name() == title:
                        project.removeMapLayer(node.layerId())

                project.addMapLayer(wms_layer, False)
                years_dict[year].addLayer(wms_layer)
        
        self.iface.messageBar().pushMessage("Base de Aerolevantamentos", "Mosaicos carregados e organizados com sucesso!", level=Qgis.Success)

    def init_setup(self):
        self.configUI()

        self.mapserver_dir = os.path.join(QgsApplication.qgisSettingsDirPath(), 'mapserver_local')
        drive_url = 'https://drive.google.com/file/d/1nTtZFGyugutxh7vV2dXkZppDlebNmxgh/view?usp=sharing'

        self.worker =  MapServerSetupWorker(drive_url, self.mapserver_dir)
        self.worker.progress_text.connect(self.progress_dialog.setLabelText)
        self.worker.progress_value.connect(self.progress_dialog.setValue)
        self.worker.finished.connect(self.setup_finished)
        self.progress_dialog.canceled.connect(self.worker.terminate)
        self.worker.start()
    
    def setup_finished(self, success, message):
        try:
            if(success):
                self.iface.messageBar().pushMessage("Map Server Local", message, level=Qgis.Success)

                img_dir = r"\\srv061sr\IMAGENS DRONE\__MAP_SERVER\ORTOFOTOS"
                map_file = os.path.join(self.mapserver_dir, "config.map").replace("\\", '/')
                
                self.create_map_conf()
                layers = self.create_map_file(img_dir, map_file)
                self.start_server()
                self.create_wms_connection()

                dialog = LayersDialog(layers)
                if dialog.exec_():
                    layers = dialog.get_layers()
                    if layers:
                        self.load_layers(layers)
                    else:
                        self.iface.messageBar().pushMessage("Base de Aerolevantamento", "Nenhum camada foi selecionada.", level=Qgis.Warning)

            else:
                self.iface.messageBar().pushMessage("Error", f"Problema {message}", level=Qgis.Critical)
        
        except Exception as e:
            complete_error = traceback.format_exc()
            self.iface.messageBar().pushMessage("Erro Oculto", f"O plugin travou: {str(e)}", level=Qgis.Critical)
            QgsMessageLog.logMessage(complete_error, "WMS Local", Qgis.Critical)