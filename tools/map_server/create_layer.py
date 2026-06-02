def create_layer(name, vrt_path, title, group, product_type="ORTOFOTOS"):
    processing_block = ""
    if product_type.upper() in ['MDT', 'MDS']:
        processing_block = 'PROCESSING "SCALE=AUTO"'
    
    return f"""
    LAYER
        NAME "{name}"
        GROUP "{group}"
        TYPE RASTER
        STATUS ON
        DATA "{vrt_path}"
        { processing_block }
        METADATA
            "wms_title" "Mosaico {title}"
        END
        PROJECTION
            "init=epsg:31983"
        END
    END
"""