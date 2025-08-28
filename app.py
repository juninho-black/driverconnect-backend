import os
import sys

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.main import app, socketio
    print("✅ Aplicação importada com sucesso!")
except Exception as e:
    print(f"❌ Erro ao importar aplicação: {e}")
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Iniciando DriverConnect Backend na porta {port}")
    
    # Para produção no Railway, usar gunicorn através do SocketIO
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=port, 
        debug=False, 
        allow_unsafe_werkzeug=True  # Permitir em produção
    )
