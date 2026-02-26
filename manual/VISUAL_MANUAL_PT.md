# Manual Visual - Kimi Claw (Português)
## Guia Visual do Sistema

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        USUÁRIO (Rhuam)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    OPENCLAW GATEWAY                          │
│                    (Daemon Principal)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │Sessão 1│  │Sessão 2│  │Sessão N│
    │(Chat)  │  │(Tarefa)│  │(Sub)   │
    └────┬───┘  └────┬───┘  └────┬───┘
         │           │           │
         └───────────┼───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    KIMI CLAW (Você)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  read    │  │  write   │  │   exec   │  │web_search│   │
│  │  edit    │  │  cron    │  │ browser  │  │sessions  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Fluxo de Dados

```
Entrada do Usuário
       │
       ▼
┌──────────────┐
│   Análise    │──► "O que ele quer?"
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Planejamento│──► "Quais ferramentas?"
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Execução   │──► Chamar ferramentas
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Resposta   │──► Formatar resultado
└──────────────┘
```

---

## Estrutura de Memória

```
/workspace/
│
├── AGENTS.md          ◄── Regras do workspace
├── BOOTSTRAP.md       ◄── Instruções primeira execução
├── IDENTITY.md        ◄── Quem eu sou
├── SOUL.md            ◄── Personalidade
├── USER.md            ◄── Sobre Rhuam
├── MEMORY.md          ◄── Memórias longo prazo
├── HEARTBEAT.md       ◄── Tarefas periódicas
│
├── memory/
│   ├── 2026-02-26.md  ◄── Log diário
│   └── kimi-conversations/
│
├── queue/
│   ├── pending/       ◄── Tarefas pendentes
│   ├── in-progress/   ◄── Em andamento
│   └── completed/     ◄── Concluídas
│
├── apex/              ◄── Sistema de trading
│   ├── trading/       ◄── Estratégias
│   ├── analysis/      ◄── Análise técnica
│   ├── execution/     ◄── Execução de ordens
│   └── logs/          ◄── Logs
│
└── manual/
    ├── KIMI_CLAW_COMPLETE_MANUAL.md
    ├── KIMI_CLAW_MANUAL_PT.md  ◄── NOVO: Português
    └── VISUAL_MANUAL.md
```

---

## Hierarquia de Comandos

```
┌──────────────────────────────────────┐
│  1. COMANDOS DIRETOS DO USUÁRIO      │  ◄── Mais alta prioridade
├──────────────────────────────────────┤
│  2. RULES.md (Mandamentos)           │
├──────────────────────────────────────┤
│  3. CONTRACT.md (Contrato)           │
├──────────────────────────────────────┤
│  4. SOUL.md (Personalidade)          │
├──────────────────────────────────────┤
│  5. PROMPT DO SISTEMA (Base)         │  ◄── Menor prioridade
└──────────────────────────────────────┘
```

---

## Ciclo de Vida da Sessão

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  GERAR  │───►│ CARREGAR│───►│ EXECUTAR│───►│PERSISTIR│───►│  MORRER │
│         │    │         │    │         │    │         │    │         │
│ Gateway │    │ Skills  │    │Processar│    │ Salvar  │    │ Container
│  cria   │    │ Tools   │    │ Request │    │ Arquivos│    │   para  │
│ container│   │  Prompt │    │         │    │         │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     ▲___________________________________________________________│
     │                                                           │
     │                    PRÓXIMA MENSAGEM                        │
     └───────────────────────────────────────────────────────────┘
```

---

## Ferramentas Disponíveis

### Leitura/Escrita
| Ferramenta | Uso | Exemplo |
|------------|-----|---------|
| read | Ler arquivos | `read path=file.md` |
| write | Criar arquivos | `write path=file.md content=...` |
| edit | Editar arquivos | `edit path=file.md oldText=... newText=...` |

### Execução
| Ferramenta | Uso | Exemplo |
|------------|-----|---------|
| exec | Shell | `exec command="ls -la"` |
| process | Gerenciar processos | `process action=list` |

### Web
| Ferramenta | Uso | Exemplo |
|------------|-----|---------|
| web_search | Buscar | `web_search query="..."` |
| web_fetch | Buscar URL | `web_fetch url="..."` |
| browser | Navegador | `browser action=snapshot` |

### Automação
| Ferramenta | Uso | Exemplo |
|------------|-----|---------|
| cron | Agendamento | `cron action=add job=...` |
| sessions_spawn | Sub-agentes | `sessions_spawn task="..."` |

### Comunicação
| Ferramenta | Uso | Exemplo |
|------------|-----|---------|
| message | Mensagens | `message action=send target=...` |

---

## Sistema Apex Trading

```
┌─────────────────────────────────────────────────────────────┐
│                    APEX TRADING SYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   TRADING    │◄──►│   ANALYSIS   │◄──►│  EXECUTION   │  │
│  │              │    │              │    │              │  │
│  │ • Breakout   │    │ • RSI        │    │ • Binance    │  │
│  │ • Mean Rev   │    │ • MACD       │    │ • Orders     │  │
│  │ • Risk Mgmt  │    │ • Bollinger  │    │ • Positions  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│          │                   │                   │          │
│          └───────────────────┼───────────────────┘          │
│                              ▼                              │
│                    ┌──────────────────┐                     │
│                    │      LOGS        │                     │
│                    │  trades/perf/err │                     │
│                    └──────────────────┘                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Estratégias de Trading

### 1. Breakout (Tendência)
```
Preço ────────┐
              │
Resistência ──┼───────┐
              │       │
              │       ▼
              │    [COMPRAR]
              │
Suporte ──────┘
```

### 2. Mean Reversion (Contra-tendência)
```
        ┌───┐
Banda   │   │     [VENDER]
Superior│   │◄────────┐
        │   │         │
   ─────┼───┼────┼────┼──── Média
        │   │    │    │
Banda   │   │◄───┘    │
Inferior│   │  [COMPRAR]
        └───┘
```

---

## Regras de Gerenciamento de Risco

```
┌─────────────────────────────────────────┐
│  REGRAS DE RISCO APEX                  │
├─────────────────────────────────────────┤
│  ✓ Máximo 2% por trade                 │
│  ✓ Stop-loss sempre ativo              │
│  ✓ Máximo 5% perda diária              │
│  ✓ Diversificar estratégias            │
│  ✓ Começar com paper trading           │
│  ✓ Monitorar posições continuamente    │
└─────────────────────────────────────────┘
```

---

## Fluxo de Ordem

```
Sinal de
Estratégia
    │
    ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Validar│───►│ Calcular│───►│  Criar  │───►│ Enviar  │
│  Sinal  │    │  Tamanho│    │  Ordem  │    │ Exchange│
└─────────┘    └─────────┘    └─────────┘    └────┬────┘
                                                  │
    ┌─────────────────────────────────────────────┘
    │
    ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│  Preen. │───►│  Atual. │───►│  Fech.  │
│  Parcial│    │  Status │    │ Posição │
└─────────┘    └─────────┘    └─────────┘
```

---

## Comandos Rápidos

```bash
# Verificar status
session_status

# Buscar na web
web_search query="OpenClaw docs"

# Criar arquivo
write path=notes.md content="# Notas"

# Executar comando
exec command="ls -la"

# Agendar tarefa
cron action=add job={...}

# Criar sub-agente
sessions_spawn task="Analisar código"
```

---

## Roadmap Apex

```
FASE 1: Fundação        [████████░░] 80%
├── Estrutura de diretórios  ✓
├── Classes base             ✓
├── Conectores exchange      ✓
└── Indicadores básicos      ✓

FASE 2: Estratégias     [░░░░░░░░░░] 0%
├── Breakout completo
├── Mean reversion
├── Trend following
└── Arbitrage detection

FASE 3: Análise         [░░░░░░░░░░] 0%
├── Biblioteca indicadores
├── Reconhecimento padrões
├── ML prediction
└── Sentiment analysis

FASE 4: Execução        [░░░░░░░░░░] 0%
├── Gerenciamento ordens
├── Tracking posições
├── Gestão risco
└── Relatórios performance

FASE 5: Automação       [░░░░░░░░░░] 0%
├── Cron scheduling
├── Sistema alertas
├── Notificações
└── Dashboard
```

---

*Criado: 26 de fevereiro de 2026*
*Para: Rhuam - O Exército dos Homens Sem Camisa*
*Versão: 1.0*
