# =============================================================================
# CORREÇÕES PARA VR_SYSTEM.PY - STATUS DE EMAIL CORRETO
# =============================================================================

def enviar_emails(self, arquivo_final):
    """📧 Envia emails para VR e RH COM CONTROLE DETALHADO DE STATUS - VERSÃO CORRIGIDA"""
    self.logger.info("📧 Iniciando processo de envio de emails")
    
    # Contadores de status
    emails_enviados_com_sucesso = 0
    emails_falharam = 0
    detalhes_envio = {
        'vr_empresa': {'status': False, 'erro': None, 'timestamp': None},
        'rh_interno': {'status': False, 'erro': None, 'timestamp': None}
    }
    
    try:
        # Verificar configurações básicas
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        email_user = os.getenv("EMAIL_USER")
        email_password = os.getenv("EMAIL_PASSWORD")
        
        if not email_user or not email_password:
            self.logger.error("❌ Configurações de email não encontradas no .env")
            self.logger.error("   📋 Configure EMAIL_USER e EMAIL_PASSWORD no arquivo .env")
            
            # 🔧 CORREÇÃO: Salvar status de falha por configuração
            self.status_emails = {
                'sucesso_geral': False,
                'emails_enviados': 0,
                'emails_falharam': 2,
                'erro_critico': 'Configurações de email não encontradas',
                'detalhes': detalhes_envio,
                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            return False
        
        if not os.path.exists(arquivo_final):
            self.logger.error(f"❌ Arquivo final não encontrado: {arquivo_final}")
            
            # 🔧 CORREÇÃO: Salvar status de falha por arquivo
            self.status_emails = {
                'sucesso_geral': False,
                'emails_enviados': 0,
                'emails_falharam': 2,
                'erro_critico': f'Arquivo não encontrado: {arquivo_final}',
                'detalhes': detalhes_envio,
                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            return False
        
        self.logger.info(f"✅ Configurações verificadas:")
        self.logger.info(f"   📧 Servidor SMTP: {smtp_server}:{smtp_port}")
        self.logger.info(f"   👤 Usuário: {email_user}")
        self.logger.info(f"   📁 Arquivo: {os.path.basename(arquivo_final)} ({os.path.getsize(arquivo_final)/1024:.1f} KB)")
        
        # ENVIO 1: Email para empresa VR
        self.logger.info("📤 Enviando email 1/2: Empresa VR...")
        try:
            inicio_vr = datetime.now()
            self._enviar_email_vr(smtp_server, smtp_port, email_user, email_password, arquivo_final)
            fim_vr = datetime.now()
            
            emails_enviados_com_sucesso += 1
            detalhes_envio['vr_empresa']['status'] = True
            detalhes_envio['vr_empresa']['timestamp'] = fim_vr.strftime("%d/%m/%Y %H:%M:%S")
            self.logger.info(f"✅ Email para empresa VR enviado em {(fim_vr - inicio_vr).total_seconds():.2f}s")
            
        except Exception as e_vr:
            emails_falharam += 1
            detalhes_envio['vr_empresa']['erro'] = str(e_vr)
            detalhes_envio['vr_empresa']['timestamp'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self.logger.error(f"❌ Falha no email para empresa VR: {str(e_vr)}")
            self.logger.debug(f"🔍 Stacktrace VR: {traceback.format_exc()}")
        
        # ENVIO 2: Email para RH
        self.logger.info("📤 Enviando email 2/2: RH Interno...")
        try:
            inicio_rh = datetime.now()
            self._enviar_email_rh(smtp_server, smtp_port, email_user, email_password, arquivo_final)
            fim_rh = datetime.now()
            
            emails_enviados_com_sucesso += 1
            detalhes_envio['rh_interno']['status'] = True
            detalhes_envio['rh_interno']['timestamp'] = fim_rh.strftime("%d/%m/%Y %H:%M:%S")
            self.logger.info(f"✅ Email para RH enviado em {(fim_rh - inicio_rh).total_seconds():.2f}s")
            
        except Exception as e_rh:
            emails_falharam += 1
            detalhes_envio['rh_interno']['erro'] = str(e_rh)
            detalhes_envio['rh_interno']['timestamp'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self.logger.error(f"❌ Falha no email para RH: {str(e_rh)}")
            self.logger.debug(f"🔍 Stacktrace RH: {traceback.format_exc()}")
        
        # 🔧 CORREÇÃO CRÍTICA: Definir sucesso baseado em critério mais flexível
        # Se pelo menos 1 email foi enviado, consideramos sucesso parcial
        # Se ambos falharam, é falha total
        sucesso_geral = emails_enviados_com_sucesso > 0
        
        self.logger.info("📊 RESULTADO DO ENVIO DE EMAILS:")
        self.logger.info(f"   ✅ Emails enviados com sucesso: {emails_enviados_com_sucesso}/2")
        self.logger.info(f"   ❌ Emails que falharam: {emails_falharam}/2")
        self.logger.info(f"   🎯 Status geral: {'SUCESSO' if sucesso_geral else 'FALHA TOTAL'}")
        
        # Log detalhado por destinatário
        for destinatario, info in detalhes_envio.items():
            if info['status']:
                self.logger.info(f"   ✅ {destinatario}: ENVIADO em {info['timestamp']}")
            else:
                self.logger.error(f"   ❌ {destinatario}: FALHOU em {info['timestamp']} - {info['erro']}")
        
        # 🔧 CORREÇÃO: Salvar status detalhado no objeto para uso no Streamlit
        self.status_emails = {
            'sucesso_geral': sucesso_geral,
            'emails_enviados': emails_enviados_com_sucesso,
            'emails_falharam': emails_falharam,
            'detalhes': detalhes_envio,
            'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'resumo': f"{emails_enviados_com_sucesso} de 2 emails enviados"
        }
        
        if sucesso_geral:
            if emails_enviados_com_sucesso == 2:
                self.logger.info("🎉 Processo de envio de emails CONCLUÍDO COM SUCESSO TOTAL")
            else:
                self.logger.warning("⚠️ Processo de envio de emails CONCLUÍDO COM SUCESSO PARCIAL")
        else:
            self.logger.error("❌ Processo de envio de emails FALHOU COMPLETAMENTE")
        
        return sucesso_geral
        
    except Exception as e:
        self.logger.error(f"❌ ERRO CRÍTICO no envio de emails: {str(e)}")
        self.logger.debug(f"🔍 Stacktrace crítico: {traceback.format_exc()}")
        
        # 🔧 CORREÇÃO: Salvar erro crítico com detalhes
        self.status_emails = {
            'sucesso_geral': False,
            'emails_enviados': emails_enviados_com_sucesso,
            'emails_falharam': 2 - emails_enviados_com_sucesso,
            'erro_critico': str(e),
            'detalhes': detalhes_envio,
            'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        
        return False

# 🔧 CORREÇÃO: Melhorar função de execução completa
def executar_processo_completo(self):
    """🚀 Executa todo o processo COM LOGS DETALHADOS E STATUS CORRETO"""
    inicio_processo = datetime.now()
    self.logger.info("🚀 INICIANDO PROCESSAMENTO COMPLETO SISTEMA VR/VA")
    self.logger.info("="*80)
    
    try:
        # ... código existente das etapas 1-7 ...
        
        # Enviar emails com controle aprimorado
        self.logger.info("8️⃣ Enviando emails...")
        inicio_emails = datetime.now()
        emails_ok = self.enviar_emails(arquivo_final)
        fim_emails = datetime.now()
        tempo_emails = (fim_emails - inicio_emails).total_seconds()
        
        # 🔧 CORREÇÃO: Log detalhado baseado no status real
        if emails_ok:
            status_info = getattr(self, 'status_emails', {})
            emails_enviados = status_info.get('emails_enviados', 0)
            
            if emails_enviados == 2:
                self.logger.info(f"✅ Todos os emails enviados com sucesso em {tempo_emails:.2f}s")
            else:
                self.logger.warning(f"⚠️ Emails enviados parcialmente ({emails_enviados}/2) em {tempo_emails:.2f}s")
        else:
            self.logger.error(f"❌ Falha no envio de emails ({tempo_emails:.2f}s)")
        
        # Estatísticas finais
        fim_processo = datetime.now()
        tempo_total = (fim_processo - inicio_processo).total_seconds()
        
        self.logger.info("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
        self.logger.info(f"⏱️ Tempo total: {tempo_total:.2f}s ({tempo_total/60:.1f} min)")
        
        # Logs de estatísticas finais
        if self.resultado_final is not None:
            total_colaboradores = len(self.resultado_final)
            valor_total = self.resultado_final['TOTAL'].sum()
            custo_empresa = self.resultado_final['Custo empresa'].sum()
            
            self.logger.info(f"📊 ESTATÍSTICAS FINAIS:")
            self.logger.info(f"   👥 Colaboradores processados: {total_colaboradores:,}")
            self.logger.info(f"   💰 Valor total VR: R$ {valor_total:,.2f}")
            self.logger.info(f"   🏢 Custo empresa: R$ {custo_empresa:,.2f}")
            
            # Breakdown por estado nos logs
            df_estados = self.resultado_final.copy()
            df_estados['Estado'] = df_estados['Sindicato do Colaborador'].apply(self.extrair_estado_corrigido)
            breakdown = df_estados.groupby('Estado').agg({
                'Matricula': 'count',
                'TOTAL': 'sum'
            }).round(2)
            
            self.logger.info(f"🗺️ BREAKDOWN POR ESTADO:")
            for estado, dados in breakdown.iterrows():
                self.logger.info(f"   📍 {estado}: {dados['Matricula']} colaboradores, R$ {dados['TOTAL']:,.2f}")
        
        self.logger.info("="*80)
        
        # 🔧 CORREÇÃO: Retornar resultado com status de email correto
        resultado_final = {
            'arquivo': arquivo_final,
            'colaboradores': len(self.resultado_final),
            'valor_total': self.resultado_final['TOTAL'].sum(),
            'emails_enviados': emails_ok,  # Status real do envio
            'tempo_processamento': tempo_total,
            'status_detalhado_emails': getattr(self, 'status_emails', {})
        }
        
        return True, resultado_final
        
    except Exception as e:
        fim_processo = datetime.now()
        tempo_total = (fim_processo - inicio_processo).total_seconds()
        
        self.logger.error(f"❌ ERRO CRÍTICO NO PROCESSAMENTO após {tempo_total:.2f}s:")
        self.logger.error(f"   🔍 Erro: {str(e)}")
        self.logger.error(f"   🔍 Stacktrace completo:")
        
        # Log do stacktrace completo
        for linha in traceback.format_exc().split('\n'):
            if linha.strip():
                self.logger.error(f"   {linha}")
        
        return False, str(e)

# 🔧 FUNÇÃO AUXILIAR: Teste de email isolado
def testar_configuracao_email(self):
    """🧪 Testa configuração de email de forma isolada"""
    self.logger.info("🧪 Testando configuração de email...")
    
    try:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        email_user = os.getenv("EMAIL_USER")
        email_password = os.getenv("EMAIL_PASSWORD")
        
        if not email_user or not email_password:
            self.logger.error("❌ Credenciais de email não configuradas")
            return False, "Credenciais não configuradas no .env"
        
        # Teste de conexão básica
        import smtplib
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_password)
        server.quit()
        
        self.logger.info("✅ Configuração de email testada com sucesso")
        return True, "Configuração OK"
        
    except Exception as e:
        self.logger.error(f"❌ Erro no teste de email: {str(e)}")
        return False, str(e)

# 🔧 FUNÇÃO AUXILIAR: Formatação monetária para logs
def log_valor_formatado(self, nome, valor):
    """📊 Loga valores monetários formatados"""
    valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    self.logger.info(f"   💰 {nome}: {valor_formatado}")

# 🔧 CORREÇÃO: Melhorar sistema de notificações
def criar_notificacao_status(self):
    """📢 Cria notificação de status para interface"""
    if hasattr(self, 'status_emails'):
        status = self.status_emails
        
        if status['sucesso_geral']:
            emails_ok = status['emails_enviados']
            if emails_ok == 2:
                return {
                    'tipo': 'sucesso',
                    'titulo': '✅ Emails Enviados',
                    'mensagem': 'Todos os emails foram enviados com sucesso',
                    'detalhes': f"Empresa VR e RH notificados em {status['timestamp']}"
                }
            else:
                return {
                    'tipo': 'aviso',
                    'titulo': '⚠️ Envio Parcial',
                    'mensagem': f'{emails_ok} de 2 emails enviados',
                    'detalhes': 'Verifique os logs para detalhes do erro'
                }
        else:
            return {
                'tipo': 'erro',
                'titulo': '❌ Falha no Envio',
                'mensagem': 'Nenhum email foi enviado com sucesso',
                'detalhes': status.get('erro_critico', 'Erro desconhecido')
            }
    
    return {
        'tipo': 'info',
        'titulo': 'ℹ️ Status Indisponível',
        'mensagem': 'Status do email não disponível',
        'detalhes': 'Sistema processado sem informação de email'
    }

# 🔧 CORREÇÃO: Melhorar validação de arquivos de email
def validar_anexos_email(self, arquivo_final):
    """📎 Valida se o arquivo está pronto para anexar"""
    try:
        if not os.path.exists(arquivo_final):
            self.logger.error(f"❌ Arquivo não existe: {arquivo_final}")
            return False, "Arquivo não encontrado"
        
        tamanho = os.path.getsize(arquivo_final)
        if tamanho == 0:
            self.logger.error(f"❌ Arquivo vazio: {arquivo_final}")
            return False, "Arquivo está vazio"
        
        # Limite de 25MB para anexos (padrão Gmail)
        limite_mb = 25 * 1024 * 1024
        if tamanho > limite_mb:
            self.logger.warning(f"⚠️ Arquivo muito grande: {tamanho/1024/1024:.1f}MB")
            return False, f"Arquivo excede limite de 25MB ({tamanho/1024/1024:.1f}MB)"
        
        self.logger.info(f"✅ Arquivo validado: {os.path.basename(arquivo_final)} ({tamanho/1024:.1f}KB)")
        return True, "Arquivo OK"
        
    except Exception as e:
        self.logger.error(f"❌ Erro na validação do arquivo: {str(e)}")
        return False, str(e)

# 🔧 MELHORIA: Sistema de retry para emails
def enviar_email_com_retry(self, smtp_server, smtp_port, email_user, email_password, msg, destinatario, max_tentativas=3):
    """🔄 Envia email com sistema de retry"""
    for tentativa in range(1, max_tentativas + 1):
        try:
            self.logger.debug(f"🔄 Tentativa {tentativa}/{max_tentativas} para {destinatario}")
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"✅ Email enviado para {destinatario} na tentativa {tentativa}")
            return True, f"Sucesso na tentativa {tentativa}"
            
        except Exception as e:
            self.logger.warning(f"⚠️ Tentativa {tentativa} falhou para {destinatario}: {str(e)}")
            
            if tentativa == max_tentativas:
                self.logger.error(f"❌ Todas as {max_tentativas} tentativas falharam para {destinatario}")
                return False, str(e)
            
            # Aguardar antes da próxima tentativa
            import time
            time.sleep(2 ** tentativa)  # Backoff exponencial
    
    return False, "Máximo de tentativas excedido"
        