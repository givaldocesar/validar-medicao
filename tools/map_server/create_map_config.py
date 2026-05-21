import os

def create_map_config(mapserver_dir_path, layers):
    log_path = os.path.join(mapserver_dir_path, "ms_error.txt").replace("\\", "/")
    
    return f"""MAP
    NAME "WMS_AEROLEVANTAMENTOS_LOCAL"
    STATUS ON
    SIZE 800 600
    EXTENT 0 0 1000000 10000000
    UNITS METERS
    IMAGECOLOR 255 255 255
    IMAGETYPE PNG32
    OUTPUTFORMAT
        NAME "png32"
        DRIVER "AGG/PNG"
        MIMETYPE "image/png"
        IMAGEMODE RGBA
        EXTENSION "png"
        FORMATOPTION "TRANSPARENT=ON"
    END

    CONFIG "MS_ERRORFILE" "{log_path}"
    DEBUG 5

    WEB
        METADATA
            "wms_title" "Base de Aerolevantamentos Mensal"
            "wms_onlineresource" "http://localhost:8080/mapserv.exe?"
            "wms_srs" "EPSG:31983"
            "wms_supported_versions" "1.1.1"
            "wms_enable_request" "*"
        END
    END

    PROJECTION
        "init=epsg:31983"
    END

    { layers }
END
"""