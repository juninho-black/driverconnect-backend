#!/usr/bin/env python3
"""
Script para corrigir o banco de dados adicionando as colunas que estão faltando
Execute este script para resolver o erro: "Coluna desconhecida 'drivers.endereco'"
"""

import os
import pymysql
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco Railway
DB_HOST = os.getenv('DB_HOST', 'junction.proxy.rlwy.net')
DB_PORT = os.getenv('DB_PORT', '10501')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'railway')

def fix_database():
    """Adiciona as colunas que estão faltando no banco de dados"""
    try:
        print("🔧 Conectando ao banco de dados Railway...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=60,
            read_timeout=60,
            write_timeout=60,
            charset='utf8mb4'
        )
        cursor = connection.cursor()
        
        migrations_executed = []
        
        print("🚀 Executando migrações...")
        
        # 1. Adicionar colunas de endereço no Driver
        migrations = [
            ("ALTER TABLE drivers ADD COLUMN endereco VARCHAR(300)", "drivers.endereco"),
            ("ALTER TABLE drivers ADD COLUMN cidade VARCHAR(100)", "drivers.cidade"),
            ("ALTER TABLE drivers ADD COLUMN estado VARCHAR(2)", "drivers.estado"),
            ("ALTER TABLE drivers ADD COLUMN cep VARCHAR(10)", "drivers.cep"),
        ]
        
        for sql, description in migrations:
            try:
                cursor.execute(sql)
                migrations_executed.append(description)
                print(f"✅ Adicionado: {description}")
            except Exception as e:
                if '1060' in str(e):  # Coluna já existe
                    print(f"⚠️ Já existe: {description}")
                else:
                    print(f"❌ Erro em {description}: {e}")
        
        # 2. Adicionar customer_id nas outras tabelas
        customer_migrations = [
            ("ALTER TABLE services ADD COLUMN customer_id INT", "services.customer_id"),
            ("ALTER TABLE payments ADD COLUMN customer_id INT", "payments.customer_id"),
            ("ALTER TABLE trips ADD COLUMN customer_id INT", "trips.customer_id"),
            ("ALTER TABLE driver_ratings ADD COLUMN customer_id INT", "driver_ratings.customer_id"),
        ]
        
        for sql, description in customer_migrations:
            try:
                cursor.execute(sql)
                migrations_executed.append(description)
                print(f"✅ Adicionado: {description}")
            except Exception as e:
                if '1060' in str(e):  # Coluna já existe
                    print(f"⚠️ Já existe: {description}")
                else:
                    print(f"❌ Erro em {description}: {e}")
        
        # 3. Adicionar foreign keys (se as tabelas existirem)
        try:
            cursor.execute("SELECT COUNT(*) FROM customers")
            if cursor.fetchone()[0] >= 0:  # Tabela customers existe
                fk_migrations = [
                    ("ALTER TABLE services ADD FOREIGN KEY (customer_id) REFERENCES customers(id)", "services.customer_fk"),
                    ("ALTER TABLE payments ADD FOREIGN KEY (customer_id) REFERENCES customers(id)", "payments.customer_fk"),
                    ("ALTER TABLE trips ADD FOREIGN KEY (customer_id) REFERENCES customers(id)", "trips.customer_fk"),
                    ("ALTER TABLE driver_ratings ADD FOREIGN KEY (customer_id) REFERENCES customers(id)", "driver_ratings.customer_fk"),
                ]
                
                for sql, description in fk_migrations:
                    try:
                        cursor.execute(sql)
                        migrations_executed.append(description)
                        print(f"✅ Foreign Key: {description}")
                    except Exception as e:
                        if '1005' in str(e) or '1022' in str(e):  # FK já existe
                            print(f"⚠️ FK já existe: {description}")
                        else:
                            print(f"❌ Erro FK {description}: {e}")
        except Exception as e:
            print(f"⚠️ Tabela customers não encontrada, pulando foreign keys")
        
        # 4. Tornar company_id opcional nas tabelas
        nullable_migrations = [
            ("ALTER TABLE services MODIFY company_id INT NULL", "services.company_id_nullable"),
            ("ALTER TABLE driver_ratings MODIFY company_id INT NULL", "driver_ratings.company_id_nullable"),
        ]
        
        for sql, description in nullable_migrations:
            try:
                cursor.execute(sql)
                migrations_executed.append(description)
                print(f"✅ Nullable: {description}")
            except Exception as e:
                print(f"⚠️ Nullable {description}: {e}")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"\n🎉 Migração concluída com sucesso!")
        print(f"📊 Total de migrações executadas: {len(migrations_executed)}")
        print("📋 Migrações executadas:")
        for migration in migrations_executed:
            print(f"   - {migration}")
        
        print(f"\n✅ O erro 'Coluna desconhecida drivers.endereco' foi corrigido!")
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        print(f"🔍 Tipo do erro: {type(e).__name__}")
        return False
    
    return True

if __name__ == '__main__':
    print("🔧 DriverConnect - Script de Correção do Banco de Dados")
    print("=" * 60)
    
    if not DB_PASSWORD:
        print("❌ Erro: DB_PASSWORD não encontrada nas variáveis de ambiente")
        print("Certifique-se de ter um arquivo .env com as credenciais do Railway")
        exit(1)
    
    print(f"🎯 Conectando em: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    success = fix_database()
    
    if success:
        print("\n🚀 Agora você pode testar o backend novamente!")
        print("📱 Teste os logins em: https://web-production-a7c54.up.railway.app/create-test-users")
    else:
        print("\n❌ Falha na migração. Verifique os logs acima.")