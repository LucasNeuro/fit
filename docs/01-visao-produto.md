# 01 — Visão do Produto (FIT)

## Nome e posicionamento

| Item | Valor |
|------|-------|
| **Marca / repositório** | FIT |
| **Tagline** | Gestão da academia com IA no WhatsApp — atende, vende, matricula e registra presença. |
| **Público** | Donos de academias pequenas e médias no Brasil |
| **Canal principal** | WhatsApp (via UAZAPI) |

## Problema

Donos de academias perdem tempo e dinheiro com três frentes:

1. **Atendimento manual** — Responder WhatsApp, confirmar aulas, explicar planos.
2. **Vendas perdidas** — Leads sem follow-up; matrículas não fechadas.
3. **Clientes desistindo** — Falta de engajamento, lembretes e visão de frequência.

**Resultado:** Menos lucro, mais estresse, vagas ociosas.

## Solução

Um **funcionário digital 24/7** que:

| Função | O que faz |
|--------|-----------|
| **Atende** | Agenda aulas, tira dúvidas, encaminha para humano quando necessário |
| **Vende** | Qualifica leads, apresenta planos, follow-up automático |
| **Cuida** | Lembretes de treino, feedback pós-aula, motivação |
| **Organiza** | Mini CRM (UAZAPI + espelho Supabase) |
| **Gerencia** | Matrículas e presença com QR na entrada (fases 2–3) |

## Exemplos de conversa (WhatsApp)

| Situação | Cliente | Agente |
|----------|---------|--------|
| Agendamento | "Quais horários de funcional?" | Lista horários reais + oferta de reserva |
| Venda | "Quanto custa o plano mensal?" | Preço do banco + CTA para fechar |
| Lembrete | — | "Lucas, sua aula é às 18h. Confirma presença?" |
| Cobrança | — | "Mensalidade vence amanhã. Pagar agora? [Pix]" |
| Feedback | "Como foi sua aula?" | Escala 1–5 + registro no banco |

## Planos comerciais

| Plano | Preço | Inclui |
|-------|-------|--------|
| **Básico** | R$ 199/mês | WhatsApp ilimitado + agendamento, lembrete, cobrança |
| **Premium** | R$ 399/mês | Básico + vendas automáticas + CRM no painel + integração academia |
| **Enterprise** | R$ 999/mês | Personalização total + suporte prioritário + relatórios avançados |

## ROI esperado (referência comercial)

| Benefício | Estimativa |
|-----------|------------|
| Economia de tempo | ~10 h/semana (equivalente a 1 funcionário) |
| Vendas | +15% matrículas (follow-up automático) |
| Retenção | −20% cancelamentos (engajamento contínuo) |

## Diferenciais

1. Funciona mesmo sem sistema legado (cadastro via painel/planilha).
2. Ativação simples: conectar WhatsApp + configurar horários/planos.
3. Resultados em ~1 semana (agendamentos e menos no-show).
4. Custo abaixo de um salário mínimo/mês no plano Básico.

## Métricas de sucesso (piloto)

- Tempo de resposta no WhatsApp **< 30 segundos**
- **≥ 1 agendamento confirmado/dia** via agente (academia piloto)
- Dono acessa painel **≥ 3×/semana**
- **NPS ≥ 8** após 30 dias de uso

## Validação comercial (pré-MVP)

- Meta: **10 donos de academia** entrevistados
- Pergunta-chave: *"Você pagaria R$ 200/mês por um assistente que faz isso tudo?"*
- Meta forte: **3 academias** dispostas a testar 30 dias grátis
