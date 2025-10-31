import os, processing
from qgis.gui import QgsMapToolEmitPoint
from qgis.core import Qgis, QgsProject, QgsRasterLayer
from qgis.PyQt.QtWidgets import QFileDialog, QApplication
from qgis.PyQt.QtCore import Qt, QDir 
from .utils import printMessage


class CriarRasterVirtual(QgsMapToolEmitPoint):
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super().__init__(self.canvas)
    

    def criar(self):
        dir_img = QFileDialog.getExistingDirectory(None, "Selecione a pasta que contém as ORTOFOTOS", "")
        if not dir_img:
            printMessage(self.iface, "Nenhum diretorio foi selecionado.")
            QgsMapToolEmitPoint.deactivate(self)
            return
    
        dir_obj = QDir(dir_img)
        dir_obj.setNameFilters(["*.tif", "*.tiff"])
        dir_obj.setFilter(QDir.Files | QDir.NoDotAndDotDot)

        tif_files = [os.path.join(dir_img, f) for f in dir_obj.entryList()]
        if not tif_files:
            printMessage(self.iface, "Nenhum arquivo .tif ou .tiff encontrado no diretório selecionado.", push=True, level=Qgis.MessageLevel.Critical)
            QgsMapToolEmitPoint.deactivate(self)
            return
        
        dir_name = os.path.basename(dir_img)
        output = os.path.join(dir_img, f"{dir_name}_mosaico.vrt")
        printMessage(self.iface,  "Criando Raster Virtual...", level=Qgis.Info, push=True)

        parameters = {
            'INPUT': tif_files,
            'RESOLUTION': 0,            # 0 = Média (Average)
            'PROJ_DIFFERENCE': True,    # Permitir projeções diferentes
            'SEPARATE': False,           # Queremos um mosaico, não bandas separadas
            'OUTPUT': output
        }

        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            result = processing.run("gdal:buildvirtualraster", parameters)
            output_path = result['OUTPUT']
            vrt_layer = QgsRasterLayer(output_path, f"AEROLEVANTAMENTOS ({dir_name})")

            if not vrt_layer.isValid():
                printMessage(self.iface, f"Falha ao carregar a camada criada em: {output_path}", push=True, level=Qgis.MessageLevel.Critical)
                QgsMapToolEmitPoint.deactivate(self)
                return
            
            QgsProject.instance().addMapLayer(vrt_layer)
            printMessage(self.iface, f"Mosaico virtual adicionado ao QGIS como AEROLEVANTAMENTOS", push=True, level=Qgis.MessageLevel.Success)

        except Exception as e:
            print(self.iface, f"Falha ao construir raster virtual: {e}", level=Qgis.MessageLevel.Critical)

        finally:
            QgsMapToolEmitPoint.deactivate(self)
            QApplication.restoreOverrideCursor()