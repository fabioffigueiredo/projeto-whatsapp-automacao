#!/usr/bin/env python
"""
Script de configuração inicial do projeto WhatsApp Automation
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, cwd=None):
    """Executa um comando e retorna o resultado"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def check_python_version():
    """Verifica se a versão do Python é compatível"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ é necessário")
        return False
    print(f"✅ Python {sys.version.split()[0]} detectado")
    return True


def create_env_file():
    """Cria arquivo .env se não existir"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        print("✅ Arquivo .env criado a partir do .env.example")
        print("⚠️  Configure as variáveis de ambiente no arquivo .env")
    elif env_file.exists():
        print("✅ Arquivo .env já existe")
    else:
        print("❌ Arquivo .env.example não encontrado")
        return False
    return True


def install_dependencies():
    """Instala as dependências do projeto"""
    print("📦 Instalando dependências...")
    success, output = run_command("pip install -r requirements.txt")
    if success:
        print("✅ Dependências instaladas com sucesso")
        return True
    else:
        print(f"❌ Erro ao instalar dependências: {output}")
        return False


def setup_database():
    """Configura o banco de dados"""
    print("🗄️  Configurando banco de dados...")
    
    backend_dir = Path('backend')
    if not backend_dir.exists():
        print("❌ Diretório backend não encontrado")
        return False
    
    # Fazer migrações
    success, output = run_command("python manage.py makemigrations", cwd=backend_dir)
    if not success:
        print(f"❌ Erro ao criar migrações: {output}")
        return False
    
    success, output = run_command("python manage.py migrate", cwd=backend_dir)
    if success:
        print("✅ Banco de dados configurado")
        return True
    else:
        print(f"❌ Erro ao aplicar migrações: {output}")
        return False


def create_superuser():
    """Pergunta se o usuário quer criar um superusuário"""
    response = input("\n🔐 Deseja criar um superusuário? (y/N): ")
    if response.lower() in ['y', 'yes', 's', 'sim']:
        backend_dir = Path('backend')
        success, output = run_command("python manage.py createsuperuser", cwd=backend_dir)
        if success:
            print("✅ Superusuário criado")
        else:
            print(f"❌ Erro ao criar superusuário: {output}")


def main():
    """Função principal do setup"""
    print("🚀 Configurando projeto WhatsApp Automation...\n")
    
    # Verificar versão do Python
    if not check_python_version():
        return
    
    # Criar arquivo .env
    if not create_env_file():
        return
    
    # Instalar dependências
    if not install_dependencies():
        return
    
    # Configurar banco de dados
    if not setup_database():
        return
    
    # Criar superusuário (opcional)
    create_superuser()
    
    print("\n🎉 Setup concluído com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Configure as variáveis de ambiente no arquivo .env")
    print("2. Execute: cd backend && python manage.py runserver")
    print("3. Acesse: http://localhost:8000/admin")
    print("\n📚 Consulte o README.md para mais informações")


if __name__ == '__main__':
    main()