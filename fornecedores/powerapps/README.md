# Qualificação de Fornecedores no Power Apps (Dataverse)

Versão oficial do site de qualificação de fornecedores: **tabelas no Dataverse + app de tela
(canvas) no Power Apps**, com o mesmo layout do site:
- cabeçalho com logo e abas;
- KPIs e cartões de segmento;
- ranking com barras e estrelas;
- ficha do fornecedor;
- metodologia.

| Pasta / arquivo | Para que serve |
|---|---|
| `dataverse/*.csv` | Dados da planilha prontos para importar nas tabelas, na ordem 1 → 7 |
| `app/App.Formulas.fx` | Cores, fonte, permissões e regras de status. Cole em **App → Formulas** |
| `app/logoSenai.png` | Logo do cabeçalho. Envie em **Mídia** com este nome |
| `telas/<tela>.pa.yaml` | Cada tela completa, em código YAML do Power Apps |
| `telas/controles/<tela>.yaml` | Só os controles da tela, para **Colar código** numa tela em branco |
| `gerar_telas.py`, `gerar_csv_dataverse.py` | Geram os arquivos acima. Rode de novo se mudar algo |

> **O que já foi conferido:** as telas passam no schema oficial do código YAML do Power Apps
> (pa.yaml v3) e as 4.040 fórmulas passam no parser oficial do Power Fx. As regras de status
> foram testadas no motor do Power Fx. Toda coluna e todo controle citados nas fórmulas existem.
>
> **O que não foi conferido:** o app ainda não foi aberto dentro de um Power Apps de verdade.
> No primeiro uso podem aparecer pequenos avisos do Studio, por exemplo de delegação ou de
> versão de controle. Se algo não colar ou der erro, me mande a mensagem exata.

---

## Passo 1. Criar uma solução

Em [make.powerapps.com](https://make.powerapps.com), escolha o ambiente da empresa.
1. Vá em **Soluções → Nova solução**, com o nome *Qualificação de Fornecedores*.
2. Crie também um editor (*publisher*) com o prefixo da empresa, por exemplo `senai`.
3. Faça tudo daqui em diante **dentro da solução**. Assim dá para levar o app para outro
   ambiente depois (teste → produção).

---

## Passo 2. Criar as tabelas

**Os nomes de exibição precisam ser exatamente estes, sem acento.** As fórmulas do app usam
esses nomes. Em cada tabela, o nome de exibição da **coluna primária** vem indicado.

Tipos:
- *Texto* = Linha única de texto
- *Texto longo* = Várias linhas de texto
- *Decimal* = Número decimal
- *Inteiro* = Número inteiro
- *Sim/Não* = Sim/Não
- *Data* = Data somente (formato *Somente data*)
- *Moeda* = Moeda
- *Pesquisa* = Pesquisa, apontando para a tabela indicada

**1. Segmento** (plural: **Segmentos**) · coluna primária: **Nome**
| Coluna | Tipo |
|---|---|
| Ordem | Inteiro |

**2. Capacidade** (plural: **Capacidades**) · coluna primária: **Nome**
| Coluna | Tipo |
|---|---|
| Segmento | Pesquisa → Segmento (obrigatória) |
| Peso | Decimal (2 casas) |
| Ordem | Inteiro |
| Ativa | Sim/Não (padrão: Sim) |

**3. Criterio** (plural: **Criterios**) · coluna primária: **Descricao**
| Coluna | Tipo |
|---|---|
| Segmento | Pesquisa → Segmento (vazia em Prazo e Custo) |
| Dimensao | Texto (Qualidade, Prazo ou Custo) |
| Nota | Inteiro (0 a 5) |

**4. Fornecedor** (plural: **Fornecedores**) · coluna primária: **Empresa**
| Coluna | Tipo |
|---|---|
| CNPJ, Telefone, Email, Responsavel | Texto |
| Endereco, Observacoes | Texto longo |
| Ativo | Sim/Não (padrão: Sim) |

**5. Vinculo** (plural: **Vinculos**), um registro por fornecedor × segmento · coluna primária: **Nome**
| Coluna | Tipo |
|---|---|
| Fornecedor | Pesquisa → Fornecedor (obrigatória) |
| Segmento | Pesquisa → Segmento (obrigatória) |
| StatusCalculado | Texto. É calculado pelo app; **não** use o nome "Status", que já existe em toda tabela |
| Especializado | Sim/Não (padrão: Não). É o selo manual |
| NotaCapacidade, MediaQualidade, MediaPrazo, MediaCusto, IndiceGlobal | Decimal (2 casas) |
| QtdServicos | Inteiro |
| UltimoServico | Data |

**6. AvaliacaoCapacidade** (plural: **AvaliacoesCapacidade**) · coluna primária: **Nome**
| Coluna | Tipo |
|---|---|
| Vinculo | Pesquisa → Vinculo (obrigatória) |
| Capacidade | Pesquisa → Capacidade (obrigatória) |
| Atendimento | Texto (atende, parcial ou nao) |

**7. Servico** (plural: **Servicos**) · coluna primária: **Projeto**
| Coluna | Tipo |
|---|---|
| Vinculo | Pesquisa → Vinculo (obrigatória) |
| DataOrcamento | Data (obrigatória) |
| Projetista | Texto |
| Relato | Texto longo |
| ValorOrcado | Moeda |
| DataPrevista, DataEntrega | Data |
| NotaQualidade, NotaPrazo, NotaCusto | Inteiro (0 a 5) |

**Histórico de alterações.** Em **Configurações → Auditoria**, ative a auditoria do ambiente e
das tabelas *Vinculo* e *Servico*. O Dataverse passa a registrar quem marcou o selo
Especializado, quem registrou ou excluiu serviços, e quando. No site isso não existia.

---

## Passo 3. Importar os dados da planilha

Para cada tabela, **na ordem dos números** (1 → 7):
1. Abra a tabela e escolha **Importar → Importar dados do Excel**.
2. Escolha o CSV correspondente em `dataverse/`.
3. Em **Mapear colunas**, ligue cada coluna do arquivo à coluna de mesmo nome.

As colunas de **pesquisa** vêm com o **nome** do registro relacionado. O Dataverse liga pelo
nome, por isso a ordem importa: um segmento precisa existir antes das capacidades que apontam
para ele. Exemplos:
- "Usinagem" em *Segmento*;
- "EISEN — Usinagem" em *Vinculo*;
- "Torno CNC" em *Capacidade*.

| Arquivo | Tabela | Linhas |
|---|---|---|
| 1-Segmentos.csv | Segmentos | 5 |
| 2-Capacidades.csv | Capacidades | 29 |
| 3-Criterios.csv | Criterios | 36 |
| 4-Fornecedores.csv | Fornecedores | 30 |
| 5-Vinculos.csv | Vinculos (já com índices e status calculados) | 30 |
| 6-AvaliacoesCapacidade.csv | AvaliacoesCapacidade | 160 |
| 7-Servicos.csv | Servicos | 10 |

As colunas Sim/Não vêm como **Sim/Não**. Se o ambiente estiver em inglês e a importação
recusar, troque por **Yes/No** no CSV.

Os CSVs têm os dados da planilha original. Se a equipe já cadastrou coisas novas no site do
claude.ai, eu reativo a exportação do site para levar esses dados também.

---

## Passo 4. Funções de segurança (quem pode o quê)

Em **Configurações → Usuários + permissões → Funções de segurança**, crie três funções com
nível **Organização**:

| Função | Segmentos, Capacidades, Criterios | Fornecedores, Vinculos, AvaliacoesCapacidade | Servicos |
|---|---|---|---|
| **Fornecedores – Consulta** | Ler | Ler | Ler |
| **Fornecedores – Registro** | Ler | Ler, Criar, Gravar | Ler, Criar, Gravar, Excluir |
| **Fornecedores – Metodologia** | Tudo | Tudo | Tudo |

O app lê essas permissões sozinho, pela fórmula `DataSourceInfo` em *App.Formulas*.
- Quem só tem *Consulta* não vê os botões de cadastrar, registrar nem o selo.
- Só quem tem *Metodologia* edita segmentos, pesos e critérios.

---

## Passo 5. Criar o app

1. Na solução, escolha **Novo → Aplicativo → Aplicativo de tela**, formato **Tablet**, com o
   nome *Qualificação de Fornecedores*.
2. Em **Configurações**:
   - **Geral → Limite de linhas de dados** = **2000**.
   - **Atualizações → Novo**: ative **Funções definidas pelo usuário**, caso ainda não estejam
     ativas no seu ambiente.
   - **Exibição**: desligue **Dimensionar para ajustar** e deixe **Bloquear proporção**
     desligado. As telas foram feitas para se ajustar à largura da janela.
3. Em **Dados → Adicionar dados**, adicione as 7 tabelas: Segmentos, Capacidades, Criterios,
   Fornecedores, Vinculos, AvaliacoesCapacidade e Servicos.
4. Em **Mídia → Carregar**, envie `app/logoSenai.png`. Ela precisa aparecer com o nome
   **logoSenai**.
5. Selecione **App** na árvore e, na propriedade **Formulas**, cole o conteúdo de
   `app/App.Formulas.fx`.
6. Ainda em **App**, defina **StartScreen** = `scrPainel`.

---

## Passo 6. Colar as telas

**Primeiro crie as 5 telas em branco, já com estes nomes**, porque elas se referenciam entre si:
`scrPainel`, `scrFornecedores`, `scrFornecedorForm`, `scrFicha` e `scrMetodologia`.

Depois, para cada tela:
1. Abra `telas/controles/<tela>.yaml`, selecione tudo e copie.
2. Na **Exibição em árvore**, clique com o botão direito na tela e escolha **Colar código**.
3. Copie as propriedades da própria tela, que estão no começo de `telas/<tela>.pa.yaml`:

| Tela | Fill | OnVisible |
|---|---|---|
| scrPainel | `Cor.Fundo` | (vazio) |
| scrFornecedores | `Cor.Fundo` | (vazio) |
| scrFornecedorForm | `Cor.Fundo` | Reset dos campos (copiar do arquivo) |
| scrFicha | `Cor.Fundo` | Carrega capacidades, histórico e mudanças de status (copiar do arquivo) |
| scrMetodologia | `Cor.Fundo` | Seleciona o primeiro segmento (copiar do arquivo) |

> Nas versões mais novas do Studio dá para colar a **tela inteira** (`telas/<tela>.pa.yaml`)
> clicando com o botão direito numa área vazia da árvore → **Colar código**. Assim as
> propriedades da tela já vêm junto.

Se o Studio pedir para atualizar a versão de algum controle, aceite.

---

## Passo 7. Testar, publicar e compartilhar

1. Abra o **Painel** (F5). O ranking deve mostrar EISEN como **Homologado** (6 serviços,
   global 2,89, quase 3 estrelas) e VITARI como **Em avaliação** (2 serviços).
2. Na ficha de um fornecedor, registre um serviço de teste. As médias e o status se
   recalculam na hora. Depois exclua o serviço de teste.
3. Escolha **Salvar → Publicar**.
4. Em **Compartilhar**, adicione as pessoas ou o grupo do Microsoft 365. Na mesma tela,
   atribua a **função de segurança** do Passo 4 a cada uma.
5. Opcional: fixe o app no Teams (**Aplicativos → Power Apps → adicionar como aba**).

---

## Como as regras ficaram no app

- **Status (automático).** É recalculado e gravado em `StatusCalculado` sempre que um serviço
  é registrado ou excluído. A função está em `StatusPor` (*App.Formulas*):
  - menos de 2 serviços → Em avaliação;
  - índice global abaixo de 2 → Bloqueado;
  - 5 ou mais serviços e índice global acima de 2 → Homologado;
  - demais casos → Em avaliação.
- **Especializado.** É uma caixa de seleção na ficha e o único item manual.
- **Capacidade.** É recalculada quando se marca Atende / Parcial / Não atende. Na Metodologia,
  ao mudar um peso ou remover uma capacidade, o app recalcula todos os fornecedores do segmento.
- **Mudanças de status** na ficha. São reconstruídas serviço a serviço, igual ao site.
- **Excluir segmento.** Apaga junto as capacidades, os critérios, as ligações com fornecedores
  e os serviços do segmento, depois de uma confirmação na tela.

Se alguém alterar dados direto nas tabelas, fora do app, os índices daquele fornecedor só se
atualizam no próximo serviço registrado. Para evitar isso, dá para criar um fluxo no Power
Automate ("quando uma linha de Servico for adicionada, modificada ou excluída") que faça o
mesmo recálculo. Posso montar esse fluxo depois.

## Diferenças em relação ao site

- O app usa os controles clássicos do Power Apps. Cores, espaçamentos e organização seguem o
  site, mas os cantos e as fontes são os do Power Apps (Segoe UI).
- Não há tema escuro.
- O layout foi pensado para computador e tablet. No celular funciona, mas fica apertado; se
  precisar, dá para fazer uma versão de celular só com Painel e Registrar serviço.
- A aba Exportar não existe: os dados já estão no Dataverse, e dá para abrir qualquer tabela
  no Excel pelo próprio Power Apps.
