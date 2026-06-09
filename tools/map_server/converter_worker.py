import os, datetime, traceback
from osgeo import gdal
from qgis.PyQt.QtCore import QThread, pyqtSignal

class ConverterWorker(QThread):
    file_progress_changed = pyqtSignal(int)
    progress_changed = pyqtSignal(int)
    progress_text = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, input_dir, base_output_dir, product_type):
        super().__init__()
        self.input_dir = input_dir
        self.base_output_dir = base_output_dir
        self.product_type = product_type
        self.is_canceled = False
        
        self.months = {
            1: 'JANEIRO', 2: 'FEVEREIRO', 3: 'MARCO', 4: 'ABRIL',
            5: 'MAIO', 6: 'JUNHO', 7: 'JULHO', 8: 'AGOSTO',
            9: 'SETEMBRO', 10: 'OUTUBRO', 11: 'NOVEMBRO', 12: 'DEZEMBRO'
        }

    def cancel(self):
        self.is_canceled = True

    def gdal_progress_callback(self, complete, message, user_data):
        if self.is_canceled:
            return 0
        
        percentual = int(complete*100)
        self.file_progress_changed.emit(percentual)
        return 1
    
    def run(self):
        self.progress_changed.emit(0)

        try:
            tif_files = [file for file in os.listdir(self.input_dir) if file.lower().endswith('.tif')]
            total = len(tif_files)
            processed = 0

            if total == 0:
                self.finished.emit(False, f"Nenhum arquivo .tif encontrado em {self.input_dir}.")
                return
            
            for index, file in enumerate(tif_files):
                if(self.is_canceled):
                    break
                
                input_path = os.path.join(self.input_dir, file)
                
                self.file_progress_changed.emit(0)
                self.progress_text.emit(f"Processando {index+1}/{total}: {file}...")

                # 1.PEGA A DATA DA ARQUIVO E SETA O DIRETORIO DE SAÍDA
                timestamp = os.path.getmtime(input_path)
                file_date = datetime.datetime.fromtimestamp(timestamp)
                dest_dir_name = f"{file_date.year}-{self.months[file_date.month]}"
                
                # 2. CRIA O DIRETORIO CASO NÃO EXISTA
                dest_dir = os.path.join(self.base_output_dir, dest_dir_name)
                os.makedirs(dest_dir, exist_ok=True)
                
                # 3. SETA O ARQUIVO DE SAIDA DA CONVERSÃO
                output_path = os.path.join(dest_dir, file.replace('.tif', '_cog.tif'))
                
                # 4.APLICA AS REGRAS DE CONVERSAO CASO ELEVACAO
                is_elevation = self.product_type in ["MDT", "MDS"]
                gdal.UseExceptions()
                
                if is_elevation:
                    options = gdal.TranslateOptions(
                        format="COG",
                        creationOptions=["COMPRESS=DEFLATE", "PREDICTOR=YES", "RESAMPLING=BILINEAR"],
                        callback=self.gdal_progress_callback
                    )
                else:
                    options = gdal.TranslateOptions(
                        format="COG",
                        creationOptions=["COMPRESS=JPEG", "QUALITY=85", "RESAMPLING=AVERAGE", "BIGTIFF=YES"],
                        callback=self.gdal_progress_callback
                    )

                # 5. CONVERTE
                try:
                    gdal.Translate(output_path, input_path, options=options)
                    processed += 1
                except Exception as e:
                    if self.is_canceled:
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        break
                    else:
                        raise e
                finally:
                    self.progress_changed.emit(int(((index + 1) / total) * 100))


            if self.is_canceled:
                self.progress_text.emit("Processamento interrompido pelo usuário.")
                self.finished.emit(True, f"Operação cancelada! {processed} de {total} arquivos foram processados com sucesso.")
            else:
                self.progress_changed.emit(100)
                self.progress_text.emit("Processamento concluído!")
                self.finished.emit(True, f"{total} arquivos processados.")

        except Exception as e:
            self.finished.emit(False, f"Erro: {str(e)}\n{traceback.format_exc()}")