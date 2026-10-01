# Fórmulas Power Fx do app

Fórmulas prontas para colar no Power Apps (app de tela / canvas), usando as listas criadas
por `provisionar-listas.ps1`. Os nomes de controles (`ddSegmento`, `galCap`…) são sugestões:
se você der outros nomes, troque nas fórmulas.

Fontes de dados a adicionar no app (Dados → Adicionar dados → SharePoint → seu site):
`Fornecedores`, `Segmentos`, `FornecedorSegmento`, `Capacidades`, `AvaliacaoCapacidade`,
`CriteriosQualificacao`, `HistoricoServicos`, `Usuarios`.

> **Separadores:** as fórmulas estão no formato com vírgula (`,`) entre argumentos e
> ponto-e-vírgula (`;`) entre ações. Se o seu Power Apps Studio estiver em português e usar
> `;` entre argumentos e `;;` entre ações, ajuste ao colar (ou mude o idioma do navegador
> para inglês durante a montagem). Os números aparecem no formato brasileiro via `"pt-BR"`
> no `Text(...)`.

---

## 1. App → Formulas (fórmulas nomeadas)

```powerfx
PapelAtual = Coalesce(
    LookUp(Usuarios, Lower(Email) = Lower(User().Email)).Papel.Value,
    "Consulta"
);
PodeEditarCadastro = PapelAtual in ["Administrador", "Suprimentos"];
PodeAvaliarServico = PapelAtual in ["Administrador", "Suprimentos", "Projetista"];
EhAdmin            = PapelAtual = "Administrador";

CorStatus(status: Text): Color =
    Switch(status,
        "Homologado",    RGBA(46, 125, 50, 1),
        "Especializado", RGBA(21, 101, 192, 1),
        "Bloqueado",     RGBA(198, 40, 40, 1),
        RGBA(117, 117, 117, 1)
    );
```

> `CorStatus` é uma função definida pelo usuário (UDF). Se o seu ambiente ainda não tiver
> UDFs, ative em Configurações → Recursos futuros, ou repita o `Switch` direto no `Fill`.
>
> Esconder um botão não é segurança: quem tem acesso à lista consegue editá-la pelo
> SharePoint. A permissão real é dada nas próprias listas (ver README, "Papéis").

---

## 2. Tela Dashboard

**Filtros**

```powerfx
// ddSegmento.Items
Sort(Segmentos, Ordem)

// ddStatus.Items
["Em avaliação", "Homologado", "Especializado", "Bloqueado"]
```

(Deixe `AllowEmptySelection = true` nos dois para "todos".)

**Cartões de resumo (KPIs)**

```powerfx
// lblTotalFornecedores.Text
CountRows(Filter(Fornecedores, Ativo))

// lblHomologados.Text
CountRows(Filter(FornecedorSegmento, Status.Value = "Homologado"))

// lblMediaGlobal.Text  — média de todos os fornecedores que já têm serviço avaliado
Text(Average(Filter(FornecedorSegmento, QtdServicos > 0), IndiceGlobal), "0.00", "pt-BR")
```

**Galeria `galDashboard` — um cartão por fornecedor × segmento**

```powerfx
// galDashboard.Items
SortByColumns(
    Filter(FornecedorSegmento,
        IsBlank(ddSegmento.Selected) || Segmento.Id = ddSegmento.Selected.ID,
        IsBlank(ddStatus.Selected.Value) || Status.Value = ddStatus.Selected.Value
    ),
    "IndiceGlobal", SortOrder.Descending
)
```

Dentro do cartão:

```powerfx
lblNome.Text        = ThisItem.Fornecedor.Value
lblSegmento.Text    = ThisItem.Segmento.Value
lblStatus.Text      = ThisItem.Status.Value
lblStatus.Fill      = CorStatus(ThisItem.Status.Value)
lblGlobal.Text      = If(IsBlank(ThisItem.IndiceGlobal), "–", Text(ThisItem.IndiceGlobal, "0.0", "pt-BR"))
lblServicos.Text    = Coalesce(ThisItem.QtdServicos, 0) & " serviço(s)"

// barras 0–5 (um retângulo de fundo + um retângulo por cima com esta largura)
recCapacidade.Width = Parent.TemplateWidth * 0.5 * Coalesce(ThisItem.NotaCapacidade, 0) / 5
recQualidade.Width  = Parent.TemplateWidth * 0.5 * Coalesce(ThisItem.MediaQualidade, 0) / 5
recPrazo.Width      = Parent.TemplateWidth * 0.5 * Coalesce(ThisItem.MediaPrazo, 0) / 5
recCusto.Width      = Parent.TemplateWidth * 0.5 * Coalesce(ThisItem.MediaCusto, 0) / 5

// status sugerido pela regra (ver README, seção 6) — mostrado ao lado do status oficial
lblSugerido.Text =
    With({s:
        If(Coalesce(ThisItem.QtdServicos, 0) < 2,  "Em avaliação",
           ThisItem.IndiceGlobal < 2,              "Bloqueado",
           Coalesce(ThisItem.NotaCapacidade, 0) >= 2.5, "Homologado",
           "Especializado")},
        If(s <> ThisItem.Status.Value, "Sugerido: " & s, ""))

// ao clicar no cartão
galDashboard.OnSelect = Set(varVinculo, ThisItem); Navigate(scrFornecedor)
```

---

## 3. Tela Fornecedores (lista e cadastro)

```powerfx
// galFornecedores.Items
SortByColumns(
    Search(Fornecedores, txtBusca.Text, "Title", "Responsavel"),
    "Title"
)

// btnNovo.Visible
PodeEditarCadastro
// btnNovo.OnSelect
NewForm(frmFornecedor); Navigate(scrFornecedorForm)

// frmFornecedor: DataSource = Fornecedores, Item = galFornecedores.Selected
// btnSalvar.OnSelect
SubmitForm(frmFornecedor)
```

Depois de salvar um fornecedor novo, ligue-o a um ou mais segmentos
(caixa de seleção `cbSegmentos`, Items = `Sort(Segmentos, Ordem)`):

```powerfx
// frmFornecedor.OnSuccess
ForAll(cbSegmentos.SelectedItems As s,
    If(IsBlank(LookUp(FornecedorSegmento,
                      Fornecedor.Id = frmFornecedor.LastSubmit.ID && Segmento.Id = s.ID)),
        Patch(FornecedorSegmento, Defaults(FornecedorSegmento), {
            Title:      frmFornecedor.LastSubmit.Title & " — " & s.Title,
            Fornecedor: {Id: frmFornecedor.LastSubmit.ID, Value: frmFornecedor.LastSubmit.Title},
            Segmento:   {Id: s.ID, Value: s.Title},
            Status:     {Value: "Em avaliação"},
            QtdServicos: 0
        })
    )
);
Notify("Fornecedor salvo", NotificationType.Success);
Back()
```

---

## 4. Tela do fornecedor → aba Capacidade técnica

```powerfx
// scrCapacidade.OnVisible — carrega o que já foi avaliado
ClearCollect(colAval, Filter(AvaliacaoCapacidade, Vinculo.Id = varVinculo.ID))

// galCap.Items — capacidades exigidas pelo segmento, com o peso
Sort(Filter(Capacidades, Segmento.Id = varVinculo.Segmento.Id, Ativa), Ordem)

// dentro da galeria
lblCap.Text       = ThisItem.Title & "  (peso " & ThisItem.Peso & ")"
ddAtend.Items     = ["Atende", "Atende parcialmente", "Não atende"]
ddAtend.Default   = Coalesce(LookUp(colAval, Capacidade.Id = ThisItem.ID).Atendimento.Value, "Não atende")
ddAtend.DisplayMode = If(PodeEditarCadastro, DisplayMode.Edit, DisplayMode.View)

// nota ao vivo (0–5) no topo da tela — App.Formulas não enxerga controles, então use
// uma variável de contexto atualizada pelo OnChange de ddAtend:
ddAtend.OnChange = UpdateContext({locNotaCap:
    Sum(galCap.AllItems,
        Switch(ddAtend.Selected.Value, "Atende", Peso, "Atende parcialmente", Peso / 2, 0))
    / Sum(galCap.AllItems, Peso) * 5})
lblNotaCap.Text = Text(Coalesce(locNotaCap, varVinculo.NotaCapacidade), "0.0", "pt-BR")
```

```powerfx
// btnSalvarCapacidade.OnSelect
ForAll(galCap.AllItems As linha,
    With({
        existente: LookUp(colAval, Capacidade.Id = linha.ID),
        nota: Switch(linha.ddAtend.Selected.Value,
                     "Atende", linha.Peso,
                     "Atende parcialmente", linha.Peso / 2,
                     0)
    },
        Patch(AvaliacaoCapacidade, Coalesce(existente, Defaults(AvaliacaoCapacidade)), {
            Title:       varVinculo.Fornecedor.Value & " — " & linha.Title,
            Vinculo:     {Id: varVinculo.ID, Value: varVinculo.Title},
            Capacidade:  {Id: linha.ID, Value: linha.Title},
            Atendimento: {Value: linha.ddAtend.Selected.Value},
            Nota:        nota
        })
    )
);
Set(varVinculo,
    Patch(FornecedorSegmento, LookUp(FornecedorSegmento, ID = varVinculo.ID), {
        NotaCapacidade: Round(
            Sum(galCap.AllItems,
                Switch(ddAtend.Selected.Value, "Atende", Peso, "Atende parcialmente", Peso / 2, 0))
            / Sum(galCap.AllItems, Peso) * 5, 2)
    })
);
Notify("Capacidade técnica salva", NotificationType.Success)
```

---

## 5. Tela "Registrar serviço" (histórico + qualificação)

Os três índices são escolhidos pela **descrição** do critério (o usuário não digita nota):
a lista de critérios de Qualidade muda conforme o segmento; Prazo e Custo são os mesmos para todos.

```powerfx
// ddQualidade.Items
Sort(Filter(CriteriosQualificacao,
            Dimensao.Value = "Qualidade", Segmento.Id = varVinculo.Segmento.Id),
     Nota, SortOrder.Descending)
// ddPrazo.Items
Sort(Filter(CriteriosQualificacao, Dimensao.Value = "Prazo"), Nota, SortOrder.Descending)
// ddCusto.Items
Sort(Filter(CriteriosQualificacao, Dimensao.Value = "Custo"), Nota, SortOrder.Descending)

// os três: Value = "Title" (mostra a descrição); exiba a nota ao lado:
lblNotaQ.Text = ddQualidade.Selected.Nota
```

Opcional — sugerir o índice de prazo a partir das datas (se preencher Data prevista / Data de entrega):

```powerfx
// ddPrazo.Default
With({atraso: DateDiff(dpPrevista.SelectedDate, dpEntrega.SelectedDate, TimeUnit.Days)},
    LookUp(ddPrazo.Items, Nota =
        If(IsBlank(dpEntrega.SelectedDate), 0,
           atraso <= 0, 5,
           atraso = 1,  4,
           atraso <= 3, 3,
           atraso <= 7, 2,
           1)).Title)
```

```powerfx
// btnSalvarServico.OnSelect
Patch(HistoricoServicos, Defaults(HistoricoServicos), {
    Title:         txtProjeto.Text,
    Vinculo:       {Id: varVinculo.ID, Value: varVinculo.Title},
    DataOrcamento: dpOrcamento.SelectedDate,
    Projetista:    User().FullName,
    Relato:        txtRelato.Text,
    ValorOrcado:   Value(txtValor.Text),
    DataPrevista:  dpPrevista.SelectedDate,
    DataEntrega:   dpEntrega.SelectedDate,
    NotaQualidade: ddQualidade.Selected.Nota,
    NotaPrazo:     ddPrazo.Selected.Nota,
    NotaCusto:     ddCusto.Selected.Nota
});

// recalcula os índices acumulados do fornecedor (= "Índices Acumulados" da planilha)
With({h: Filter(HistoricoServicos, Vinculo.Id = varVinculo.ID)},
    With({q: Average(h, NotaQualidade), p: Average(h, NotaPrazo), c: Average(h, NotaCusto)},
        Set(varVinculo,
            Patch(FornecedorSegmento, LookUp(FornecedorSegmento, ID = varVinculo.ID), {
                MediaQualidade: Round(q, 2),
                MediaPrazo:     Round(p, 2),
                MediaCusto:     Round(c, 2),
                IndiceGlobal:   Round((q + p + c) / 3, 2),
                QtdServicos:    CountRows(h),
                UltimoServico:  Max(h, DataOrcamento)
            })
        )
    )
);
Notify("Serviço registrado", NotificationType.Success);
Back()

// btnSalvarServico.DisplayMode
If(PodeAvaliarServico && !IsBlank(txtProjeto.Text) && !IsBlank(dpOrcamento.SelectedDate)
   && !IsBlank(ddQualidade.Selected) && !IsBlank(ddPrazo.Selected) && !IsBlank(ddCusto.Selected),
   DisplayMode.Edit, DisplayMode.Disabled)
```

Galeria do histórico na tela do fornecedor:

```powerfx
// galHistorico.Items
SortByColumns(Filter(HistoricoServicos, Vinculo.Id = varVinculo.ID), "DataOrcamento", SortOrder.Descending)
```

---

## 6. Alterar status (Suprimentos / Administrador)

```powerfx
// ddNovoStatus.Items
["Em avaliação", "Homologado", "Especializado", "Bloqueado"]

// btnAlterarStatus.OnSelect
Set(varVinculo,
    Patch(FornecedorSegmento, LookUp(FornecedorSegmento, ID = varVinculo.ID), {
        Status: {Value: ddNovoStatus.Selected.Value},
        JustificativaStatus: Text(Today(), "dd/mm/yyyy") & " – " & User().FullName & ": "
                             & txtJustificativa.Text & Char(10) & varVinculo.JustificativaStatus
    })
)
```

---

## Observação sobre delegação

Todas as consultas filtram primeiro por um ID de pesquisa (`Vinculo.Id = …`,
`Segmento.Id = …`), o que o SharePoint resolve no servidor. As médias (`Average`) rodam
só sobre o histórico de **um** fornecedor, então o limite de 500/2.000 linhas do Power Apps
não chega a ser um problema mesmo com anos de registros. Se aparecer o triângulo amarelo
de delegação no filtro do Dashboard (por causa do `IsBlank(...) ||`), aumente o limite em
Configurações → Geral → "Limite de linhas de dados" para 2000 — a lista `FornecedorSegmento`
tem uma linha por fornecedor × segmento e não deve passar disso.
