from qgis.core import Qgis, QgsMessageLog 

def printMessage(iface, message, push=False, level=Qgis.MessageLevel.Warning):
    QgsMessageLog.logMessage(str(message), "Validar Medição", level)
    if push:
        iface.messageBar().pushMessage("Cria 3D de bacia de captação", str(message), level=level, duration=5)