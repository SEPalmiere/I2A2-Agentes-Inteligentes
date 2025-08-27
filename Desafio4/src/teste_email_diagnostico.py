#!/usr/bin/env python3
# =============================================================================
# TESTE DE DIAGNÓSTICO DE EMAIL - SISTEMA VR/VA
# =============================================================================

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def teste_conexao_smtp():
    """🔧 Testa conexão SMTP independente"""
    print("🔧 TESTE DE CONEXÃO SMTP")
    print("=" * 50)
    
    # Carregar configurações
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    print(f"📧 Configurações:")
    print(f"   Servidor: {smtp_server}:{smtp_port}")
    print(f"   Usuário: {email_user}")
    print(f"   Senha: {'*' * len(email_password) if email_password else 'NÃO CONFIGURADA'}")
    print()
    
    if not email_user or not email_password:
        print("❌ ERRO: Credenciais não configuradas no .env")
        return False
    
    try:
        # Teste 1: Conexão básica
        print("🔗 Teste 1: Conectando ao servidor SMTP...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        print("✅ Conexão estabelecida")
        
        # Teste 2: STARTTLS
        print("🔐 Teste 2: Iniciando criptografia STARTTLS...")
        server.starttls()
        print("✅ STARTTLS OK")
        
        # Teste 3: Autenticação
        print("🔑 Teste 3: Testando autenticação...")
        server.login(email_user, email_password)
        print("✅ Autenticação bem-sucedida")
        
        # Teste 4: Envio de email de teste
        print("📤 Teste 4: Enviando email de teste...")
        
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = email_user  # Enviar para si mesmo
        msg['Subject'] = 'Teste Sistema VR/VA'
        
        corpo = f"""
🧪 EMAIL DE TESTE - SISTEMA VR/VA

Este é um email de teste automático gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}.

Se você recebeu este email, significa que:
✅ Configuração SMTP está correta
✅ Credenciais estão funcionando
✅ Sistema de email está operacional

Teste realizado com sucesso!

---
Sistema VR/VA - Diagnóstico Automático
        """
        
        msg.attach(MIMEText(corpo, 'plain'))
        
        server.send_message(msg)
        server.quit()
        
        print("✅ Email de teste enviado com sucesso!")
        print(f"📬 Verifique sua caixa de entrada: {email_user}")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ ERRO DE AUTENTICAÇÃO: {e}")
        print("💡 Possíveis soluções:")
        print("   1. Verifique se a senha de app está correta")
        print("   2. Confirme que 2FA está ativado no Gmail")
        print("   3. Gere uma nova senha de app")
        return False
        
    except smtplib.SMTPServerDisconnected as e:
        print(f"❌ ERRO DE CONEXÃO: {e}")
        print("💡 Possíveis soluções:")
        print("   1. Verifique sua conexão com internet")
        print("   2. Confirme servidor SMTP e porta")
        return False
        
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {e}")
        print("💡 Detalhes técnicos para debug:")
        import traceback
        traceback.print_exc()
        return False

def verificar_configuracoes():
    """🔍 Verifica todas as configurações de email"""
    print("🔍 VERIFICAÇÃO DE CONFIGURAÇÕES")
    print("=" * 50)
    
    # Verificar arquivo .env
    env_file = ".env"
    if not os.path.exists(env_file):
        env_file = "../.env"  # Tentar na pasta pai
    
    if not os.path.exists(env_file):
        print("❌ Arquivo .env não encontrado")
        return False
    
    print(f"✅ Arquivo .env encontrado: {env_file}")
    
    # Verificar variáveis
    variaveis_necessarias = [
        "SMTP_SERVER",
        "SMTP_PORT", 
        "EMAIL_USER",
        "EMAIL_PASSWORD"
    ]
    
    missing = []
    for var in variaveis_necessarias:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"❌ {var}: NÃO CONFIGURADA")
        else:
            if var == "EMAIL_PASSWORD":
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
    
    if missing:
        print(f"\n❌ Variáveis faltando: {missing}")
        return False
    
    return True

def main():
    """🚀 Função principal de diagnóstico"""
    print("🧪 DIAGNÓSTICO COMPLETO DE EMAIL - SISTEMA VR/VA")
    print("=" * 60)
    print()
    
    # Passo 1: Verificar configurações
    if not verificar_configuracoes():
        print("\n❌ FALHA: Configure as variáveis de ambiente primeiro")
        return
    
    print()
    
    # Passo 2: Testar conexão
    if teste_conexao_smtp():
        print("\n🎉 SUCESSO: Sistema de email está funcionando corretamente!")
        print("💡 Se o Streamlit mostra 'Falha' mas você recebe os emails,")
        print("   o problema está na lógica de verificação de status.")
    else:
        print("\n❌ FALHA: Sistema de email não está funcionando")
        print("💡 Resolva os erros acima antes de usar o sistema VR/VA")

if __name__ == "__main__":
    main()