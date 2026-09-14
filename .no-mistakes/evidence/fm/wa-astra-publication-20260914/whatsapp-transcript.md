# WhatsApp: evidência comportamental local

Revisão: `36e2d4dad6b19c4c6a83781204a5f96ea913a2e7`.

Inbox, autenticação da CLI e SQLite reais; transporte WhatsApp e principal simulados. Não houve execução de modelo, acesso a conta, processamento de anexos ou ativação de produção.

## Pedido e resposta de texto

Usuário: Conte as linhas do arquivo local

Saída aceita pelo transporte simulado: Pedido recebido e preservado. O Firstmate está disponível apenas em checkpoints; o início da execução ainda não foi confirmado.

Saída aceita pelo transporte simulado: Análise iniciada

Saída aceita pelo transporte simulado: O arquivo tem 3 linhas.

Estado final do pedido: `completed`.

## Decisão expirada: mensagem deve chegar ao principal

Após a pergunta conversacional “Quer um resumo?”, as confirmações abaixo foram encaminhadas pela nota persistida e reivindicadas pela CLI autenticada.

| Entrada | Estado de entrada | Texto recebido pelo principal |
| --- | --- | --- |
| sim | received | sim |
| ok | received | ok |
| aprovo | received | aprovo |
| pode | received | pode |
| 👍 | received | 👍 |
| ✅ | received | ✅ |

Na implementação anterior (`684c61bc`), a mesma regressão falhou nas seis entradas: todas eram marcadas como `answered`, impedindo o encaminhamento. Veja [a execução anterior](r1-before-fix.txt).

Código explícito expirado: Nenhuma ação foi aprovada. Responda com o código da pergunta vigente: aprovar CÓDIGO. Uma confirmação genérica não escolhe entre tarefas.

A decisão expirada permaneceu pendente e sem `answer_wamid`; nenhuma aprovação foi criada. No instante exato do vencimento e enquanto há decisões vigentes, a confirmação genérica continua solicitando o código. A aprovação explícita vigente continua sendo consumida uma única vez.

## CLI e persistência

Dois ciclos CLI com a mesma entrada preservaram um único pedido. O backup SQLite foi aberto e manteve a entrada. A configuração launchd gerada foi interpretada com plistlib e manteve `Disabled=true`; nenhum comando de instalação foi executado.

Os detalhes abaixo são saída real dos testes em fixtures:

- [Entradas, respostas da CLI, mensagens simuladas e estado persistido](whatsapp-product-evidence.json)
- [Script de reprodução](reproduce_whatsapp.py)
