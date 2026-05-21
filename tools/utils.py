import os, sys
from osgeo import gdal
from qgis.core import Qgis, QgsMessageLog, QgsApplication

def printMessage(iface, message, push=False, level=Qgis.MessageLevel.Warning):
    QgsMessageLog.logMessage(str(message), "Validar Medição", level)
    if push:
        iface.messageBar().pushMessage("Cria 3D de bacia de captação", str(message), level=level, duration=5)

def get_proj_lib():
    path_found = ""

    possible_paths = [
        os.environ.get('PROJ_LIB', ''),
        os.path.join(sys.exec_prefix, 'share', 'proj'),
        os.path.join(sys.exec_prefix, '..', 'share', 'proj'),
        os.path.join(QgsApplication.pkgDataPath(), '..', '..', 'share', 'proj'),
        os.path.join(QgsApplication.pkgDataPath(), '..', 'proj'),
        r"C:\OSGeo4W\share\proj",
        r"C:\OSGeo4W64\share\proj"
    ]

    for path in possible_paths:
        if path and os.path.exists(os.path.join(path, 'proj.db')):
            path_found = os.path.abspath(path).replace("\\", "/")
            break

    if not path_found:
        path_found = os.path.join(sys.exec_prefix, 'share', 'proj').replace("\\", "/")

    return path_found

def get_gdal_path():
    path_found = ""

    possible_paths = [
        os.environ.get('GDAL_DATA', ''),
        os.path.join(sys.exec_prefix, 'share', 'gdal'),
        os.path.join(QgsApplication.pkgDataPath(), '..', '..', 'share', 'gdal')
    ]

    for path in possible_paths:
        if path and os.path.exists(os.path.join(path, 'gcs.csv')):
            path_found = os.path.abspath(path).replace("\\", "/")
            break
    
    return path_found

def get_global_proj_gdal():
    proj_lib = gdal.GetConfigOption('PROJ_LIB') or os.environ.get('PROJ_LIB', '')
    gdal_data = gdal.GetConfigOption('GDAL_DATA') or os.environ.get('GDAL_DATA', '')

    base_dir = os.path.dirname(sys.executable)
    if not proj_lib or not os.path.exists(proj_lib):
        proj_lib = os.path.abspath(os.path.join(base_dir, '..', 'share', 'proj')).replace("\\", "/")
    if not gdal_data or not os.path.exists(gdal_data):
        gdal_data = os.path.abspath(os.path.join(base_dir, '..', 'share', 'gdal')).replace("\\", "/")

    return proj_lib.replace("\\", "/"), gdal_data.replace("\\", "/")