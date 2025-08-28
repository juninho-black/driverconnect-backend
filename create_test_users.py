#!/usr/bin/env python3
import os
import sys
from werkzeug.security import generate_password_hash

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.main import app, db
    from src.models.company import Company
    from src.models.driver import Driver  
    from src.models.customer import Customer
    
    def create_test_users():
        with app.app_context():
            print("🔧 Criando usuários de teste...")
            
            # Limpar usuários existentes (opcional)
            # Company.query.delete()
            # Driver.query.delete()
            # Customer.query.delete()
            
            # 1. Criar empresa de teste
            existing_company = Company.query.filter_by(email='empresa@teste.com').first()
            if not existing_company:
                company = Company(
                    nome_empresa='Empresa Teste',
                    email='empresa@teste.com',
                    cnpj='12345678000123',
                    telefone='(11) 99999-9999',
                    endereco='Rua Teste, 123',
                    cidade='São Paulo',
                    estado='SP',
                    cep='01000-000',
                    password_hash=generate_password_hash('empresa123')
                )
                db.session.add(company)
                print("✅ Empresa teste criada")
            else:
                print("⚠️ Empresa teste já existe")
            
            # 2. Criar motorista de teste
            existing_driver = Driver.query.filter_by(email='motorista@teste.com').first()
            if not existing_driver:
                driver = Driver(
                    nome='Motorista Teste',
                    email='motorista@teste.com',
                    cpf='12345678901',
                    telefone='(11) 88888-8888',
                    endereco='Rua Motorista, 456',
                    cidade='São Paulo',
                    estado='SP',
                    cep='02000-000',
                    cnh='12345678901',
                    veiculo_modelo='Honda Civic',
                    veiculo_placa='ABC-1234',
                    veiculo_ano=2020,
                    status='disponivel',
                    password_hash=generate_password_hash('motorista123')
                )
                db.session.add(driver)
                print("✅ Motorista teste criado")
            else:
                print("⚠️ Motorista teste já existe")
            
            # 3. Criar cliente de teste
            existing_customer = Customer.query.filter_by(email='cliente@teste.com').first()
            if not existing_customer:
                customer = Customer(
                    nome='Cliente Teste',
                    email='cliente@teste.com',
                    cpf='98765432100',
                    telefone='(11) 77777-7777',
                    endereco='Rua Cliente, 789',
                    cidade='São Paulo',
                    estado='SP',
                    cep='03000-000',
                    metodo_pagamento_preferido='pix',
                    password_hash=generate_password_hash('cliente123')
                )
                db.session.add(customer)
                print("✅ Cliente teste criado")
            else:
                print("⚠️ Cliente teste já existe")
            
            # Salvar no banco
            try:
                db.session.commit()
                print("✅ Usuários de teste salvos no banco!")
                
                # Verificar se foram criados
                print("\n📋 Usuários criados:")
                print(f"Empresas: {Company.query.count()}")
                print(f"Motoristas: {Driver.query.count()}")
                print(f"Clientes: {Customer.query.count()}")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao salvar: {e}")
                
    if __name__ == '__main__':
        create_test_users()
        
except Exception as e:
    print(f"❌ Erro ao importar: {e}")
    print("Certifique-se de que o backend está configurado corretamente")