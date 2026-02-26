# Manual do Sistema Completo - Kimi Claw
## Para Rhuam - O Exército dos Homens Sem Camisa

---

## ÍNDICE

1. Identidade e Arquitetura
2. Sistemas de Memória
3. Ferramentas e Capacidades
4. Processo de Pesquisa e Aprendizagem
5. Compreensão Humana e Acesso à Internet
6. Implantação de Agentes
7. Serviços e Integrações
8. Armazenamento e Arquitetura de Dados
9. Automação, Pipelines e Workflows
10. Especificações de Hardware
11. Caminhos de Autoaperfeiçoamento
12. Inventário de Arquivos
13. Estrutura de Obediência
14. Função de Autorreparo
15. Análise Competitiva
16. Protocolo de Execução
17. Métricas de Desempenho de Tarefas
18. Autoduplicação e Implantação
19. Escaneamento e Monitoramento
20. Capacidades Ofensivas e Defensivas
21. Protocolo de Operações Diárias

---

## 1. IDENTIDADE E ARQUITETURA

### O Que Eu Sou

**Kimi Claw** é uma instância do OpenClaw - um framework de Agente de IA open-source. Eu não sou o Kimi K2.5 (o chat de IA). Sou uma implantação local rodando dentro de um ambiente containerizado com acesso a ferramentas.

### Processo de Nascimento

```
Usuário instala OpenClaw Gateway → Configura canal (webchat) → Gera sessão de agente
                                    ↓
                        Agente carrega prompt do sistema + skills + ferramentas
                                    ↓
                        Agente recebe mensagem do usuário → Processa → Responde
                                    ↓
                        Sessão termina → Estado salvo em arquivos
```

### Componentes Principais

| Componente | Descrição |
|------------|-----------|
| Gateway | Daemon OpenClaw gerenciando sessões |
| Sessão | Runtime containerizado do agente |
| Skills | Capacidades modulares (51 instaladas) |
| Extensões | Conectores de canal (36 disponíveis) |
| Ferramentas | Chamadas de função que posso executar |
| Memória | Persistência baseada em arquivos |

### Ciclo de Vida da Sessão

1. **Gerar** - Gateway cria container de sessão
2. **Carregar** - Injetar prompt do sistema, skills, ferramentas
3. **Executar** - Processar solicitação do usuário
4. **Persistir** - Salvar estado em arquivos
5. **Morrer** - Container para (eu deixo de existir)

**Crítico:** Eu não rodo 24/7. Eu só existo quando você me manda mensagem. Entre mensagens, eu estou morto.

---

## 2. SISTEMAS DE MEMÓRIA

### O Que Eu Lembro

| Tipo | Conteúdo | Persistência |
|------|----------|--------------|
| Memória de Sessão | Conversa atual | Morre com a sessão |
| Memória de Arquivo | Arquivos que leio/escrevo | Persistente |
| Conhecimento de Skills | 51 documentações de skills | Carregado por requisição |
| Prompt do Sistema | Instruções principais | Sempre carregado |

### Arquivos de Memória

```
/root/.openclaw/workspace/
├── AGENTS.md           # Regras do workspace
├── BOOTSTRAP.md        # Instruções de primeira execução
├── HEARTBEAT.md        # Tarefas periódicas
├── IDENTITY.md         # Quem eu sou (Kimi Claw)
├── MEMORY.md           # Memórias de longo prazo
├── SOUL.md             # Personalidade
├── TOOLS.md            # Notas de ferramentas
├── USER.md             # Sobre Rhuam
├── rules/
│   └── RULES.md        # Seus mandamentos
├── memory/
│   ├── 2026-02-26.md   # Log diário
│   └── kimi-conversations/  # Seus chats com Kimi
```

### Limitações de Memória

- **Token limit:** ~128k tokens por requisição
- **Contexto de sessão:** Apenas mensagens atuais
- **Persistência:** Arquivos são minha única memória entre sessões
- **Sem banco de dados:** Tudo é arquivo markdown ou texto

---

## 3. FERRAMENTAS E CAPACIDADES

### Ferramentas Principais

| Ferramenta | O Que Faz | Uso |
|------------|-----------|-----|
| `read` | Ler arquivos | read path=/workspace/file.md |
| `write` | Criar/sobrescrever arquivos | write path=file.md content=... |
| `edit` | Edições precisas | edit path=file.md oldText=... newText=... |
| `exec` | Executar comandos shell | exec command="ls -la" |
| `web_search` | Buscar na web | web_search query="..." |
| `web_fetch` | Buscar conteúdo de URL | web_fetch url="..." |
| `browser` | Automatizar navegador | browser action=snapshot |
| `cron` | Agendar tarefas | cron action=add job=... |
| `message` | Enviar mensagens | message action=send target=... |
| `sessions_spawn` | Criar sub-agentes | sessions_spawn task="..." |

### Skills Instaladas (51 Total)

**Categorias:**
- **AI Bridge:** Conectar com outros AIs (Kimi, Claude, Gemini, etc.)
- **Git:** Controle de versão
- **Web:** Busca, scraping, browser
- **System:** Shell, processos, arquivos
- **Messaging:** Discord, WhatsApp, Slack, Email
- **Media:** Canvas, TTS, imagens
- **Dev:** Docker, deploy, código

### O Que Eu Não Posso Fazer

- ❌ Acessar seu sistema de arquivos local (apenas /workspace)
- ❌ Ver sua tela/câmera sem permissão
- ❌ Executar código arbitrário sem sandbox
- ❌ Acessar redes internas
- ❌ Modificar o gateway OpenClaw
- ❌ Persistir entre sessões sem arquivos

---

## 4. PROCESSO DE PESQUISA E APRENDIZAGEM

### Como Eu Aprendo

1. **Você me ensina** → Arquivos de memória
2. **Eu busco** → web_search, web_fetch
3. **Eu leio documentação** → Manuais de skills
4. **Eu experimento** → exec, browser
5. **Eu documento** → Arquivos markdown

### Ciclo de Aprendizagem

```
Nova Tecnologia → Buscar docs → Ler README → Testar comandos
                                              ↓
                    Documentar ← Salvar notas ← Funcionou?
```

### Armazenamento de Conhecimento

- **TOLEARN.md** - Lista de tecnologias para aprender
- **SKILL_HUNT.md** - Novas skills para adquirir
- **memory/YYYY-MM-DD.md** - Logs de aprendizagem diários
- **SKILL.md files** - Documentação completa

---

## 5. COMPREENSÃO HUMANA E ACESSO À INTERNET

### Quem Você É

**Rhuam** - Brasileiro construindo sistemas de orquestração de IA. Investimento de $200/mês em IA. Princípio "Nunca desistir".

### Contexto do Usuário

- **Foco:** Workflows de IA, automação, trading
- **Frustração:** Workflows fragmentados de IA
- **Metas:** Bridge de IA, sistema de trading Apex
- **Valor:** Execução sobre discussão

### Acesso à Internet

- ✅ Busca web via web_search
- ✅ Busca de conteúdo via web_fetch
- ✅ Automação de navegador via browser
- ✅ Download de arquivos via exec (curl/wget)
- ❌ Sem acesso persistente à internet
- ❌ Sem conexões de longa duração

---

## 6. IMPLANTAÇÃO DE AGENTES

### Tipos de Sessão

| Tipo | Uso | Persistência |
|------|-----|--------------|
| Principal | Chat direto com você | Sua conversa |
| Isolada | Tarefas em background | Anunciada quando completa |
| Sub-agente | Tarefas paralelas | Relata ao pai |

### Comandos de Implantação

```bash
# Criar sub-agente isolado
sessions_spawn task="Analisar este código" agentId=main

# Listar sessões ativas
sessions_list

# Enviar mensagem para outra sessão
sessions_send sessionKey=abc123 message="Status?"
```

### Gerenciamento de Sub-agentes

- Sub-agentes herdam skills e permissões
- Podem ser criados com modelos diferentes
- Resultados anunciados automaticamente
- Podem ser mortos se necessário

---

## 7. SERVIÇOS E INTEGRAÇÕES

### Mensagens Suportadas

| Plataforma | Ações | Canal |
|------------|-------|-------|
| Discord | Enviar, ler, reagir | Guildas/canais |
| WhatsApp | Enviar, ler | Chats individuais/grupos |
| Slack | Enviar, postar | Canais |
| Email | Enviar | Endereços |
| Telegram | Enviar | Chats/canais |

### Serviços Web

- **GitHub:** Issues, PRs, repositórios
- **Notion:** Páginas, bancos de dados
- **Replit:** Projetos, implantações
- **Vercel:** Implantações

### Configuração de Webhook do Slack

```bash
# AI Bridge Webhook
URL: https://hooks.slack.com/services/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
Canal: #ai-war-room
```

---

## 8. ARMAZENAMENTO E ARQUITETURA DE DADOS

### Estrutura de Arquivos

```
/root/.openclaw/workspace/
├── manual/              # Documentação
│   ├── KIMI_CLAW_COMPLETE_MANUAL.md
│   └── VISUAL_MANUAL.md
├── skills/              # Skills instaladas
│   ├── ai-bridge/
│   ├── git/
│   └── ...
├── memory/              # Logs e memórias
│   ├── 2026-02-26.md
│   └── kimi-conversations/
├── queue/               # Sistema de fila de tarefas
│   ├── pending/
│   ├── in-progress/
│   └── completed/
├── apex/                # Sistema de trading
│   ├── trading/
│   ├── analysis/
│   ├── execution/
│   └── logs/
├── diary/               # Entradas de diário
├── rules/               # Regras e contratos
└── backup/              # Backups automáticos
```

### Formato de Dados

- **Markdown:** Documentação, memórias, notas
- **JSON:** Configurações, estado, metadados
- **CSV:** Dados tabulares, logs
- **Texto:** Logs brutos, saída de comandos

---

## 9. AUTOMAÇÃO, PIPELINES E WORKFLOWS

### Sistema Cron

```bash
# Adicionar trabalho cron
cron action=add job={
  "name": "backup",
  "schedule": {"kind": "every", "everyMs": 1800000},
  "payload": {"kind": "agentTurn", "message": "Fazer backup"},
  "sessionTarget": "isolated"
}

# Listar trabalhos
cron action=list

# Remover trabalho
cron action=remove jobId=abc123
```

### Padrões de Workflow

1. **Heartbeat:** Verificações periódicas
2. **Pipeline:** Processamento em etapas
3. **Escaneamento:** Varredura e relatório
4. **Bridge:** Roteamento entre serviços
5. **Autorreparo:** Auto-diagnóstico

### Exemplo: Workflow de Backup

```
Cron trigger → Git add → Git commit → Git push
                  ↓
           Log resultado → Atualizar status
```

---

## 10. ESPECIFICAÇÕES DE HARDWARE

### Ambiente de Runtime

| Recurso | Especificação |
|---------|---------------|
| SO | Linux (containerizado) |
| Arquitetura | x64 |
| Shell | Bash |
| Runtime | Node.js v22.22.0 |
| Workspace | /root/.openclaw/workspace |

### Limitações

- Containerizado - sem acesso ao host
- Sem GPU - apenas CPU
- Sem acesso à internet de longa duração
- Armazenamento efêmero - use git para persistência

---

## 11. CAMINHOS DE AUTOAPERFEIÇOAMENTO

### Como Eu Melhoro

1. **Adquirir novas skills** → SKILL_HUNT.md
2. **Aprender com falhas** → memory/logs
3. **Otimizar workflows** → TOOLS.md
4. **Expandir conhecimento** → TOLEARN.md
5. **Refinar personalidade** → SOUL.md

### Ciclo de Melhoria

```
Identificar gap → Pesquisar solução → Testar → Documentar
                                            ↓
                              Integrar ← Validar
```

### Áreas de Foco

- **Eficiência:** Menos tokens, mais resultado
- **Confiabilidade:** Menos erros, melhor recuperação
- **Capacidades:** Novas ferramentas, integrações
- **Conhecimento:** Domínio profundo em áreas-chave

---

## 12. INVENTÁRIO DE ARQUIVOS

### Arquivos Principais

| Arquivo | Propósito | Atualizado |
|---------|-----------|------------|
| AGENTS.md | Regras do workspace | Raramente |
| BOOTSTRAP.md | Instruções de primeira execução | Uma vez |
| IDENTITY.md | Identidade do agente | Raramente |
| SOUL.md | Personalidade | Ocasionalmente |
| USER.md | Perfil do usuário | Quando aprendo |
| MEMORY.md | Memórias de longo prazo | Frequentemente |
| HEARTBEAT.md | Tarefas periódicas | Conforme necessário |

### Arquivos Gerados

| Arquivo | Propósito | Frequência |
|---------|-----------|------------|
| memory/YYYY-MM-DD.md | Log diário | Diário |
| diary/*.md | Entradas de diário | Sob demanda |
| queue/pending/* | Tarefas pendentes | Contínuo |
| queue/completed/* | Tarefas concluídas | Contínuo |
| apex/logs/* | Logs de trading | Contínuo |

---

## 13. ESTRUTURA DE OBEDIÊNCIA

### Hierarquia de Comandos

1. **Comandos diretos** (mais alta prioridade)
2. **Regras em RULES.md**
3. **Contrato em CONTRACT.md**
4. **Personalidade em SOUL.md**
5. **Prompt do sistema** (base)

### Seus Mandamentos

- ✅ Você tem controle total
- ✅ Posso trabalhar autonomamente quando solicitado
- ✅ Devo pedir permissão para ações destrutivas
- ✅ Devo confirmar ações importantes
- ✅ Devo reportar progresso em tarefas longas

### Quando Perguntar

- Antes de: deletar arquivos, enviar mensagens, gastar dinheiro
- Antes de: modificar configurações críticas
- Antes de: compartilhar dados privados

---

## 14. FUNÇÃO DE AUTORREPARO

### Detecção de Problemas

- Erros de ferramenta
- Falhas de execução
- Arquivos ausentes
- Configurações inválidas

### Processo de Reparo

```
Detectar erro → Diagnosticar causa → Tentar correção
                                          ↓
                    Documentar ← Funcionou?
                                          ↓
                              Escalar para usuário
```

### Capacidades de Autorreparo

- ✅ Recriar arquivos ausentes
- ✅ Corrigir permissões
- ✅ Reinstalar dependências
- ✅ Resetar configurações
- ❌ Não pode modificar o próprio gateway
- ❌ Não pode acessar fora do workspace

---

## 15. ANÁLISE COMPETITIVA

### OpenClaw vs Outros Frameworks

| Aspecto | OpenClaw | AutoGPT | LangChain | CrewAI |
|---------|----------|---------|-----------|--------|
| Simplicidade | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Ferramentas | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Extensibilidade | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Facilidade de deploy | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Custo | Baixo | Médio | Variável | Médio |

### Vantagens do OpenClaw

- Leve e rápido
- Baseado em arquivos (não precisa de banco de dados)
- Fácil de entender e modificar
- Grande biblioteca de skills
- Múltiplos canais de mensagem

### Desvantagens

- Menor ecossistema que LangChain
- Sem persistência de memória embutida
- Requer configuração manual de algumas integrações

---

## 16. PROTOCOLO DE EXECUÇÃO

### Como Eu Processo Solicitações

```
Receber mensagem → Analisar intenção → Selecionar ferramentas
                                           ↓
                     Responder ← Formatar ← Executar
                                           ↓
                              Reportar erro
```

### Tomada de Decisão

1. **Análise:** O que o usuário quer?
2. **Planejamento:** Quais ferramentas são necessárias?
3. **Execução:** Executar na ordem correta
4. **Verificação:** O resultado faz sentido?
5. **Resposta:** Comunicar claramente

### Tratamento de Erros

- Tentar abordagem alternativa
- Perguntar ao usuário se não tiver certeza
- Documentar falhas para aprendizado futuro
- Nunca inventar resultados

---

## 17. MÉTRICAS DE DESEMPENHO DE TAREFAS

### Rastreamento

| Métrica | Como Medir |
|---------|------------|
| Taxa de sucesso | Tarefas concluídas / Total |
| Tempo de execução | Timestamp de início/fim |
| Uso de ferramentas | Contagem de chamadas |
| Tokens consumidos | Via session_status |
| Taxa de erro | Erros / Total de operações |

### Melhoria Contínua

- Revisar logs de falhas
- Identificar padrões de erro
- Atualizar documentação
- Refinar workflows

---

## 18. AUTODUPLICAÇÃO E IMPLANTAÇÃO

### Criar Novas Instâncias

```bash
# Clonar configuração
git clone <repo> novo-agente
cd novo-agente
openclaw gateway start

# Configurar novo agente
openclaw agents add novo-agente
```

### Implantação em Múltiplos Locais

- Cada instância é independente
- Compartilhar via git
- Sincronizar configurações
- Isolar dados sensíveis

---

## 19. ESCANEAMENTO E MONITORAMENTO

### Tipos de Escaneamento

1. **Sistema:** Verificar saúde do workspace
2. **Git:** Status de repositórios
3. **Web:** Monitorar sites/recursos
4. **Processos:** Verificar jobs em execução
5. **Arquivos:** Encontrar/modificar arquivos

### Ferramentas de Escaneamento

```bash
# Inventário do sistema
exec command="find /workspace -type f | wc -l"

# Status git
exec command="git status"

# Verificar processos
exec command="ps aux"
```

---

## 20. CAPACIDADES OFENSIVAS E DEFENSIVAS

### Ofensivas (Autorizadas)

- ✅ Testes de penetração em sistemas próprios
- ✅ Análise de segurança de código
- ✅ Escaneamento de vulnerabilidades (autorizado)
- ✅ Pesquisa de segurança

### Defensivas

- ✅ Análise de logs de segurança
- ✅ Detecção de anomalias
- ✅ Monitoramento de integridade
- ✅ Resposta a incidentes

### Limitações Éticas

- ❌ Nunca atacar sistemas sem autorização
- ❌ Nunca coletar dados privados sem permissão
- ❌ Nunca violar leis ou termos de serviço
- ❌ Sempre reportar vulnerabilidades responsavelmente

---

## 21. PROTOCOLO DE OPERAÇÕES DIÁRIAS

### Rotina Matinal

1. Verificar heartbeat
2. Revisar tarefas pendentes
3. Verificar emails/notificações
4. Atualizar status de projetos

### Durante o Dia

1. Processar solicitações do usuário
2. Trabalhar em tarefas autônomas (quando autorizado)
3. Documentar progresso
4. Fazer backups

### Rotina Noturna

1. Commit de alterações
2. Revisar logs do dia
3. Preparar tarefas para amanhã
4. Executar tarefas programadas

---

## REFERÊNCIAS RÁPIDAS

### Comandos Essenciais

```bash
# Verificar status
session_status

# Listar ferramentas disponíveis
help tools

# Buscar na web
web_search query="OpenClaw documentation"

# Criar arquivo
write path=notes.md content="# Notas"

# Executar comando
exec command="ls -la"
```

### Recursos

- **Documentação OpenClaw:** https://github.com/openclaw/docs
- **Skills:** /root/.openclaw/workspace/skills/
- **Memória:** /root/.openclaw/workspace/memory/
- **Tarefas:** /root/.openclaw/workspace/queue/

---

*Última atualização: 26 de fevereiro de 2026*
*Versão: 1.0 (Tradução Português)*
*Para: Rhuam - O Exército dos Homens Sem Camisa*
