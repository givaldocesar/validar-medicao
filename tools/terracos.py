from qgis.gui import QgsMapTool, QgsRubberBand, QgsMapToolEmitPoint
from qgis.core import Qgis, QgsProject, QgsMapLayer, QgsMessageLog, QgsField, QgsFeature, QgsGeometry, QgsDistanceArea
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QMetaType

COMPRIMENTO = "comprimento"
FIELD = QgsField(COMPRIMENTO, QMetaType.Double)

class Terracos(QgsMapTool):
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super().__init__(self.canvas)

        self.rubberBand = QgsRubberBand(self.canvas, Qgis.GeometryType.Line)
        self.rubberBand.setColor(QColor(255, 255, 0, 200)) 
        self.rubberBand.setWidth(4)

        self.temp_rubberBand = QgsRubberBand(self.canvas, Qgis.GeometryType.Line)
        self.temp_rubberBand.setColor(QColor(255, 165, 0, 200)) 
        self.temp_rubberBand.setWidth(2)
        self.temp_rubberBand.setLineStyle(Qt.DotLine) 

        self.points = []
        self.lastRubberPoint = None

    def activate(self):
        self.canvas.setCursor(Qt.CrossCursor)
        self.canvas.currentLayerChanged.connect(self.checkLayer)
    
    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.active_layer = self.canvas.currentLayer()

            if(self.checkLayer(self.active_layer)):
                point = self.toLayerCoordinates(self.active_layer, event.pos())
                self.points.append(point)

                self.lastRubberPoint = self.toMapCoordinates(event.pos())
                self.rubberBand.addPoint(self.lastRubberPoint )
                self.rubberBand.show()
        
        elif event.button() == Qt.RightButton:
            # Caso não tenha nenhum ponto, desativa a ferramenta
            if len(self.points) == 0:
                self.canvas.unsetMapTool(self)
            else:
                # Limpa a ferramenta e insere a feição na camada
                self.insert()
    
    def canvasMoveEvent(self, event):
        if len(self.points) == 0:
            return

        current_point = self.toMapCoordinates(event.pos())
        self.temp_rubberBand.reset()
        self.temp_rubberBand.addPoint(self.lastRubberPoint) 
        self.temp_rubberBand.addPoint(current_point)
        self.temp_rubberBand.show()
    
    def checkLayer(self, layer):
        isValid = True

        # VERIFICA SE A CAMADA ESTÁ ATIVA
        if not layer:
            self.printMessage("Por favor, selecione uma camada válida.", push=True, level=Qgis.MessageLevel.Critical)
            isValid = False
        
        # VERIFICA SE A CAMADA É VETORIAL
        elif layer.type() != QgsMapLayer.VectorLayer:
            self.printMessage("Por favor, selecione uma camada VETORIAL válida.", push=True, level=Qgis.MessageLevel.Critical)
            isValid = False

        # VERIFICA SE A CAMADA É DO TIPO POLIGONO
        elif layer.geometryType() !=  Qgis.GeometryType.Line:
            self.printMessage("Por favor, selecione uma camada de LINHAS válida.", push=True, level=Qgis.MessageLevel.Critical)
            isValid = False
        
        if not isValid:
            self.clean()

        return isValid

    def clean(self):
        self.rubberBand.reset()
        self.temp_rubberBand.reset()
        self.points = []

    def deactivate(self):
        self.clean()
        self.rubberBand.hide()
        self.action().setChecked(False)
        self.canvas.currentLayerChanged.disconnect(self.checkLayer)
        QgsMapToolEmitPoint.deactivate(self)
        self.printMessage(f"Criar Terraços desativada.", level=Qgis.MessageLevel.Info)
    
    def insert(self):
        self.active_layer = self.canvas.currentLayer()

        if self.checkLayer(self.active_layer):
            try:
                self.active_layer.startEditing()
                field_idx = self.active_layer.fields().indexOf(COMPRIMENTO)
                
                if field_idx == -1:
                    response = self.active_layer.dataProvider().addAttributes([FIELD])
                    if(response):
                        self.active_layer.updateFields()
                        field_idx = self.active_layer.fields().indexOf(COMPRIMENTO)
                    else:
                        self.printMessage("Erro ao criar campo >>comprimento<<")
                        return
                
                geometry = QgsGeometry.fromPolylineXY(self.points)
                length = 0

                if(self.active_layer.crs().isGeographic()):
                    dist_area = QgsDistanceArea()
                    dist_area.setEllipsoid(self.active_layer.crs().ellipsoidAcronym())
                    length = dist_area.measureLength(geometry)
                else:
                    length = geometry.length()

                layer_fields = self.active_layer.fields()
                feat = QgsFeature(layer_fields)
                feat.setGeometry(geometry)
                feat[COMPRIMENTO] = length
                self.active_layer.addFeature(feat)
                self.active_layer.commitChanges()
            except Exception as e:
                self.active_layer.rollBack()
                self.printMessage(f"Erro ao inserir feição: {e}", push=True, level=Qgis.MessageLevel.Critical)

        self.clean()
    
    def printMessage(self, message, push=False, level=Qgis.MessageLevel.Warning):
        QgsMessageLog.logMessage(str(message), "Validar Medição", level)
        if push:
            self.iface.messageBar().pushMessage("Validar Medição", str(message), level=level, duration=5)