#!/usr/bin/env python3
import os
import sys
import importlib.util

# Adicionar o diretório driverconnect_backend/src ao Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_src_dir = os.path.join(current_dir, 'driverconnect_backend', 'src')
backend_dir = os.path.join(current_dir, 'driverconnect_backend')

sys.path.insert(0, backend_src_dir)
sys.path.insert(0, backend_dir)

# Tentar carregar do diretório src na raiz PRIMEIRO
src_dir = os.path.join(current_dir, 'src')
main_file_path = os.path.join(src_dir, "main.py")

print(f"🔍 Tentando carregar de: {main_file_path}")
print(f"📁 Arquivo existe: {os.path.exists(main_file_path)}")

try:
    if os.path.exists(main_file_path):
        print("✅ Carregando do src/ na raiz...")
        spec = importlib.util.spec_from_file_location("backend_main", main_file_path)
        backend_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backend_main)
        
        app = backend_main.app
        socketio = backend_main.socketio
        print("✅ Aplicação importada com sucesso do src/!")
    else:
        print("⚠️ src/main.py não encontrado, tentando fallback...")
        # Fallback: tentar do driverconnect_backend/src
        main_file_path = os.path.join(backend_src_dir, "main.py")
        print(f"🔍 Tentando fallback: {main_file_path}")
        
        spec = importlib.util.spec_from_file_location("backend_main", main_file_path)
        backend_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backend_main)
        
        app = backend_main.app
        socketio = backend_main.socketio
        print("✅ Aplicação importada com sucesso do driverconnect_backend/src/!")
        
except Exception as e:
    print(f"❌ Erro ao importar: {e}")
    print(f"📁 Diretório atual: {current_dir}")
    print(f"📁 Tentou carregar de: {main_file_path}")
    print(f"📁 Existe main.py: {os.path.exists(main_file_path)}")
    
    # Debug: listar todos os diretórios disponíveis
    print(f"📁 Conteúdo raiz: {os.listdir(current_dir) if os.path.exists(current_dir) else 'Não existe'}")
    src_root = os.path.join(current_dir, 'src')
    if os.path.exists(src_root):
        print(f"📁 Conteúdo src/: {os.listdir(src_root)}")
    if os.path.exists(backend_dir):
        print(f"📁 Conteúdo driverconnect_backend: {os.listdir(backend_dir)}")
    if os.path.exists(backend_src_dir):
        print(f"📁 Conteúdo driverconnect_backend/src: {os.listdir(backend_src_dir)}")
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Iniciando DriverConnect Backend na porta {port}")
    
    # Usar gunicorn em produção (Render/Railway), socketio apenas em desenvolvimento
    if os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT'):
        # Produção - usar apenas Flask
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Desenvolvimento local - usar SocketIO com flag de produção
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
