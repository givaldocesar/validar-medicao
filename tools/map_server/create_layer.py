def create_layer(name, vrt_path, title, group):
    return f"""
    LAYER
        NAME "{name}"
        GROUP "{group}"
        TYPE RASTER
        STATUS ON
        DATA "{vrt_path}"
        METADATA
            "wms_title" "Mosaico {title}"
        END
        PROJECTION
            "init=epsg:31983"
        END
    END
"""