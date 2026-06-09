import os, subprocess
from http.server import BaseHTTPRequestHandler

def create_map_handler(mapserver_dir_path, proj_lib, gdal_data):

    class MapServerHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            exe_mapserver = os.path.join(mapserver_dir_path, "mapserv.exe")
            
            #QUERY
            query_string = self.path.split('?', 1)[-1] if '?' in self.path else ''
            if "map=" not in query_string.lower():
                query_string = f"map=AEROLEVANTAMENTOS&{query_string}"

            #ENVIRONMENT
            env = os.environ.copy()
            if 'PROJ_LIB' in env: del env['PROJ_LIB']
            if 'GDAL_DATA' in env: del env['GDAL_DATA']

            env['QUERY_STRING'] = query_string
            env['REQUEST_METHOD'] = 'GET'
            env['MAPSERVER_CONFIG_FILE'] = os.path.join(mapserver_dir_path, "mapserv.conf").replace("\\", "/")
            env['CPL_DEBUG'] = 'ON'
            env['CPL_LOG'] = os.path.join(mapserver_dir_path, "ms_gdal_log.txt").replace("\\", "/")
           
            clean_path = []
            for path in env.get('PATH', '').split(os.pathsep):
                if 'qgis' not in path.lower() and 'osgeo4w' not in path.lower():
                    clean_path.append(path)
            
            env['PATH'] = mapserver_dir_path + os.pathsep + os.pathsep.join(clean_path)
            
            env['PROJ_LIB'] = proj_lib
            env['PROJ_DATA'] = proj_lib
            env['GDAL_DATA'] = gdal_data

            plugins_dir = os.path.join(mapserver_dir_path, "gdalplugins")
            if os.path.exists(plugins_dir):
                env['GDAL_DRIVER_PATH'] = plugins_dir
            else:
                env['GDAL_DRIVER_PATH'] = mapserver_dir_path

            #EXECUTION
            HIDE_CONSOLE = 0x08000000

            try:
                proc = subprocess.run(
                    [exe_mapserver], 
                    env=env, 
                    capture_output=True, 
                    cwd=mapserver_dir_path, 
                    creationflags=HIDE_CONSOLE
                )
            except Exception as e:
                print(f"\n[ERRO FATAL] O Python não conseguiu invocar o executável: {e}")
                self.send_response(500)
                self.end_headers()
                return
            
            raw_output = proc.stdout

            if proc.returncode != 0 or len(raw_output) == 0:
                print(f"\n{'='*50}")
                print(f"CRASH DO MAPSERVER DETECTADO")
                print(f"Código de Retorno (Return Code): {proc.returncode}")
                print(f"Erro STDERR: {proc.stderr.decode('utf-8', errors='ignore')}")
                print(f"Caminho Executável: {exe_mapserver}")
                print(f"{'='*50}\n")

                if proc.returncode in [-1073741515, 3221225781]:
                    print(">>> DIAGNÓSTICO: Faltam DLLs no Windows <<<")

            if b'\r\n\r\n' in raw_output:
                headers_raw, body = raw_output.split(b'\r\n\r\n', 1)
            elif b'\n\n' in raw_output:
                headers_raw, body = raw_output.split(b'\n\n', 1)
            else:
                headers_raw = b'Content-Type: text/plain'
                body = raw_output + (proc.stderr if proc.stderr else b'')

            if proc.returncode == 0 and b'image' not in headers_raw.lower():
                print(f"\n[ALERTA MAPSERVER] Resposta inesperada. Detalhes:\n{body.decode('utf-8', errors='ignore')[:1000]}\n")

            self.send_response(200)

            #HEADERS
            for line in headers_raw.decode('utf-8', errors='ignore').splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    self.send_header(k.strip(), v.strip())
            
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()

            try:
                self.wfile.write(body)
            except ConnectionAbortedError:
                pass # O usuário mudou de zoom rápido demais, ignora o erro
            except Exception as e:
                print(f"Erro interno de socket: {e}")
        
        def log_message(self, format, *args):
            pass
    
    return MapServerHandler