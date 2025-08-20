#!/usr/bin/env python
"""
Script de desenvolvimento para WhatsApp Automation
Facilita tarefas comuns de desenvolvimento
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, cwd=None, shell=True):
    """Executa um comando e retorna o resultado"""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def start_dev_server():
    """Inicia o servidor de desenvolvimento"""
    print("🚀 Iniciando servidor de desenvolvimento...")
    backend_dir = Path('backend')
    
    if not backend_dir.exists():
        print("❌ Diretório backend não encontrado")
        return
    
    # Aplicar migrações
    print("📊 Aplicando migrações...")
    success, output = run_command("python manage.py migrate", cwd=backend_dir)
    if not success:
        print(f"❌ Erro nas migrações: {output}")
        return
    
    # Iniciar servidor
    print("🌐 Iniciando servidor em http://localhost:8000")
    subprocess.run(["python", "manage.py", "runserver"], cwd=backend_dir)


def run_tests():
    """Executa os testes"""
    print("🧪 Executando testes...")
    backend_dir = Path('backend')
    
    success, output = run_command("python manage.py test", cwd=backend_dir)
    if success:
        print("✅ Todos os testes passaram")
        print(output)
    else:
        print("❌ Alguns testes falharam")
        print(output)


def make_migrations():
    """Cria novas migrações"""
    print("📊 Criando migrações...")
    backend_dir = Path('backend')
    
    success, output = run_command("python manage.py makemigrations", cwd=backend_dir)
    if success:
        print("✅ Migrações criadas")
        print(output)
    else:
        print("❌ Erro ao criar migrações")
        print(output)


def shell():
    """Abre o shell do Django"""
    print("🐍 Abrindo shell do Django...")
    backend_dir = Path('backend')
    subprocess.run(["python", "manage.py", "shell"], cwd=backend_dir)


def docker_up():
    """Inicia os serviços Docker"""
    print("🐳 Iniciando serviços Docker...")
    success, output = run_command("docker-compose up -d")
    if success:
        print("✅ Serviços Docker iniciados")
        print("🌐 Backend: http://localhost:8000")
        print("🔧 Admin: http://localhost:8000/admin")
        print("⚡ n8n: http://localhost:5678")
    else:
        print(f"❌ Erro ao iniciar Docker: {output}")


def docker_down():
    """Para os serviços Docker"""
    print("🐳 Parando serviços Docker...")
    success, output = run_command("docker-compose down")
    if success:
        print("✅ Serviços Docker parados")
    else:
        print(f"❌ Erro ao parar Docker: {output}")


def docker_logs():
    """Mostra logs do Docker"""
    print("📋 Logs dos serviços Docker...")
    subprocess.run(["docker-compose", "logs", "-f"])


def lint_code():
    """Executa linting do código"""
    print("🔍 Executando linting...")
    
    # Verificar se flake8 está instalado
    success, _ = run_command("flake8 --version")
    if not success:
        print("⚠️  flake8 não encontrado. Instalando...")
        run_command("pip install flake8")
    
    # Executar linting
    success, output = run_command("flake8 backend/ --max-line-length=88 --exclude=migrations")
    if success:
        print("✅ Código está limpo")
    else:
        print("⚠️  Problemas encontrados:")
        print(output)


def format_code():
    """Formata o código com black"""
    print("🎨 Formatando código...")
    
    # Verificar se black está instalado
    success, _ = run_command("black --version")
    if not success:
        print("⚠️  black não encontrado. Instalando...")
        run_command("pip install black")
    
    # Formatar código
    success, output = run_command("black backend/ --line-length=88")
    if success:
        print("✅ Código formatado")
    else:
        print(f"❌ Erro na formatação: {output}")


def reset_db():
    """Reseta o banco de dados"""
    print("🗄️  Resetando banco de dados...")
    backend_dir = Path('backend')
    
    # Remover arquivo SQLite se existir
    db_file = backend_dir / 'db.sqlite3'
    if db_file.exists():
        db_file.unlink()
        print("✅ Arquivo SQLite removido")
    
    # Remover migrações
    migrations_dir = backend_dir / 'core' / 'migrations'
    if migrations_dir.exists():
        for file in migrations_dir.glob('*.py'):
            if file.name != '__init__.py':
                file.unlink()
        print("✅ Migrações removidas")
    
    # Criar novas migrações
    make_migrations()
    
    # Aplicar migrações
    success, output = run_command("python manage.py migrate", cwd=backend_dir)
    if success:
        print("✅ Banco de dados resetado")
    else:
        print(f"❌ Erro ao resetar banco: {output}")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Script de desenvolvimento WhatsApp Automation')
    parser.add_argument('command', choices=[
        'runserver', 'test', 'makemigrations', 'shell', 'docker-up', 'docker-down',
        'docker-logs', 'lint', 'format', 'reset-db'
    ], help='Comando a ser executado')
    
    args = parser.parse_args()
    
    commands = {
        'runserver': start_dev_server,
        'test': run_tests,
        'makemigrations': make_migrations,
        'shell': shell,
        'docker-up': docker_up,
        'docker-down': docker_down,
        'docker-logs': docker_logs,
        'lint': lint_code,
        'format': format_code,
        'reset-db': reset_db,
    }
    
    command_func = commands.get(args.command)
    if command_func:
        command_func()
    else:
        print(f"❌ Comando '{args.command}' não encontrado")


if __name__ == '__main__':
    main()