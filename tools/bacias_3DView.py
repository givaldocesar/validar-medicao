import processing, os, tempfile
from qgis.gui import QgsMapToolIdentify, QgsMapLayerComboBox, QgsMapToolEmitPoint
from qgis.core import Qgis, QgsMapLayer, QgsFeatureRequest, QgsRasterLayer, QgsRasterFileWriter, QgsRasterPipe, QgsProject
from qgis.core import QgsProcessing, QgsProcessingContext, QgsProcessingFeedback, QgsMessageLog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QLabel
from .bacias_3DView_dialog import Model3DDialog
from .utils import printMessage

class bacias_3DView(QgsMapToolIdentify):
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super().__init__(self.canvas)
        self.feedback = QgsProcessingFeedback()
        self.context = QgsProcessingContext()
    
    def activate(self):
        self.canvas.setCursor(Qt.CrossCursor)
    
    def addComboBox(self, toolbar):
        self.camada_raster = QgsMapLayerComboBox(self.iface.mainWindow())
        self.camada_raster.setFilters(QgsMapLayer.RasterLayer)
        self.camada_raster.setMinimumWidth(250)
        toolbar.addWidget(QLabel("MDT: "))
        toolbar.addWidget(self.camada_raster)
    
    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            layer = self.iface.activeLayer()
            if self.checkLayer(layer):
                layer.removeSelection()
                mask = self.get_mask(event, layer)
                if mask:
                    mdt = self.createTempRaster(mask)
                    if mdt:
                        self.show3DModel(mdt, mask)
            
        elif event.button() == Qt.RightButton:
            self.canvas.unsetMapTool(self)
    
    def checkLayer(self, layer):
        isValid = True

        # VERIFICA SE A CAMADA ESTÁ ATIVA
        if not layer:
            printMessage(self.iface, "Por favor, selecione uma camada válida.", push=True, level=Qgis.MessageLevel.Critical)
            isValid = False
        
        # VERIFICA SE A CAMADA É VETORIAL
        elif layer.type() != QgsMapLayer.VectorLayer:
            printMessage(self.iface, "Por favor, selecione uma camada VETORIAL válida.", push=True, level=Qgis.MessageLevel.Critical)
            isValid = False

        # VERIFICA SE A CAMADA É DO TIPO POLIGONO
        elif layer.geometryType() !=  Qgis.GeometryType.Polygon:
            printMessage(self.iface, "Por favor, selecione uma camada de POLÍGONOS válida.", push=True, level=Qgis.MessageLevel.Critical)
            isValid = False

        return isValid
    
    def createTempRaster(self, mask):
        mdt = self.camada_raster.currentLayer()
        if (not mdt) or (not mdt.isValid()) or not mask:
            return None

        printMessage(self.iface, "Baixando camada MDT para um arquivo temporário.")
        with tempfile.NamedTemporaryFile(suffix='.tif') as temp_file_obj:
            temp_file_path = temp_file_obj.name

        pipe = QgsRasterPipe()
        pipe.set(mdt.dataProvider().clone())
        width, height = int (mask.extent().width() / mdt.rasterUnitsPerPixelX()), int (mask.extent().height() / mdt.rasterUnitsPerPixelY())

        writer = QgsRasterFileWriter(temp_file_path)
        error = writer.writeRaster(pipe, width, height, mask.extent().buffered(5), mdt.crs())
        
        if error == QgsRasterFileWriter.NoError :
            temp = QgsRasterLayer(temp_file_path, "MDT Temporário")
            if temp.isValid():
                return temp
        
        printMessage(self.iface, "MDT temporário não foi gerado com sucesso.", level=Qgis.MessageLevel.Critical)
        return None

    def deactivate(self):
        QgsMapToolEmitPoint.deactivate(self)
        printMessage(self.iface, f"Criar Modelo 3D desativada", level=Qgis.MessageLevel.Info)

    def get_mask(self, event, layer):
        printMessage(self.iface, "Criando máscara")
        
        try:
            result = self.identify(event.x(), event.y(), QgsMapToolIdentify.TopDownStopAtFirst, [layer],  QgsMapToolIdentify.VectorLayer)
            if(len(result) == 0):
                return None

            layer.selectByIds([result[-1].mFeature.id()])
            request = QgsFeatureRequest().setFilterFid(result[-1].mFeature.id())
            mask = layer.materialize(request)

            mdt = self.camada_raster.currentLayer()
            if(mdt.crs() != mask.crs()):
                printMessage(self.iface, "Reprojetando camada máscara")

                result = processing.run("native:reprojectlayer", {
                    'INPUT': mask,
                    'TARGET_CRS': mdt.crs(),
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, 
                    context=self.context,
                    feedback=self.feedback,
                    is_child_algorithm=True)

                reprojected = self.context.takeResultLayer(result['OUTPUT'])
                return reprojected
            else:
                return mask
        except Exception as e:
            printMessage(self.iface, f"Falha ao criar máscara. Erro: {e}", push=True, level=Qgis.MessageLevel.Critical)
            return None
    
    def show3DModel(self, raster, mask):
        printMessage(self.iface, "Montando a visualização 3D")
        self.map_dialog = Model3DDialog(raster, mask)
        self.map_dialog.show()
        printMessage(self.iface, "Modelo 3D criado")
