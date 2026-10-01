<#
  Cria as listas do app "Gestão de Fornecedores" num site do SharePoint e
  importa os dados extraídos da planilha (pasta .\dados, gerada por extrair_excel.py).

  Pré-requisitos (uma vez só):
    Install-Module PnP.PowerShell -Scope CurrentUser
    Register-PnPEntraIDAppForInteractiveLogin -ApplicationName "PnP Fornecedores" -Tenant <tenant>.onmicrosoft.com
      (anote o ClientId que ele devolve)

  Uso:
    .\provisionar-listas.ps1 -SiteUrl https://<tenant>.sharepoint.com/sites/Fornecedores -ClientId <guid>
    .\provisionar-listas.ps1 ... -SemDados      # só cria a estrutura, sem importar a planilha

  O script pode ser rodado de novo: listas e colunas que já existem são mantidas.
  A importação de dados, porém, NÃO verifica duplicados — rode-a só uma vez.
#>
param(
    [Parameter(Mandatory)] [string] $SiteUrl,
    [Parameter(Mandatory)] [string] $ClientId,
    [switch] $SemDados
)

$ErrorActionPreference = 'Stop'
$inv = [Globalization.CultureInfo]::InvariantCulture
Connect-PnPOnline -Url $SiteUrl -ClientId $ClientId -Interactive

# ---------------------------------------------------------------- helpers
function Nova-Lista($titulo, $nomeTitle) {
    if (-not (Get-PnPList -Identity $titulo -ErrorAction SilentlyContinue)) {
        New-PnPList -Title $titulo -Template GenericList -OnQuickLaunch | Out-Null
        Write-Host "Lista criada: $titulo"
    }
    if ($nomeTitle) { Set-PnPField -List $titulo -Identity Title -Values @{ Title = $nomeTitle } | Out-Null }
}

function Nova-Coluna($lista, $nome, $tipo, [string[]] $opcoes, [switch] $Obrigatoria) {
    if (Get-PnPField -List $lista -Identity $nome -ErrorAction SilentlyContinue) { return }
    $p = @{ List = $lista; DisplayName = $nome; InternalName = $nome; Type = $tipo; AddToDefaultView = $true }
    if ($opcoes) { $p.Choices = $opcoes }
    if ($Obrigatoria) { $p.Required = $true }
    Add-PnPField @p | Out-Null
}

function Nova-Pesquisa($lista, $nome, $listaAlvo, [switch] $Obrigatoria) {
    if (Get-PnPField -List $lista -Identity $nome -ErrorAction SilentlyContinue) { return }
    $alvo = (Get-PnPList -Identity $listaAlvo).Id
    $req  = if ($Obrigatoria) { 'TRUE' } else { 'FALSE' }
    $xml  = "<Field Type='Lookup' DisplayName='$nome' Name='$nome' StaticName='$nome' List='{$alvo}' ShowField='Title' Required='$req' Indexed='TRUE' />"
    Add-PnPFieldFromXml -List $lista -FieldXml $xml | Out-Null
    $view = Get-PnPView -List $lista | Where-Object DefaultView
    Set-PnPView -List $lista -Identity $view.Id -Fields (@($view.ViewFields) + $nome) | Out-Null
}

# ---------------------------------------------------------------- estrutura
# 1. Configuração (mantida pelo Administrador)
Nova-Lista 'Segmentos' 'Segmento'
Nova-Coluna 'Segmentos' 'Ordem' Number

Nova-Lista 'Capacidades' 'Capacidade'
Nova-Pesquisa 'Capacidades' 'Segmento' 'Segmentos' -Obrigatoria
Nova-Coluna 'Capacidades' 'Peso'  Number -Obrigatoria
Nova-Coluna 'Capacidades' 'Ordem' Number
Nova-Coluna 'Capacidades' 'Ativa' Boolean

Nova-Lista 'CriteriosQualificacao' 'Descricao'
Nova-Pesquisa 'CriteriosQualificacao' 'Segmento' 'Segmentos'          # vazio = vale para todos (Prazo e Custo)
Nova-Coluna 'CriteriosQualificacao' 'Dimensao' Choice @('Qualidade', 'Prazo', 'Custo') -Obrigatoria
Nova-Coluna 'CriteriosQualificacao' 'Nota' Number -Obrigatoria

Nova-Lista 'Usuarios' 'Nome'
Nova-Coluna 'Usuarios' 'Email' Text -Obrigatoria
Nova-Coluna 'Usuarios' 'Papel' Choice @('Administrador', 'Suprimentos', 'Projetista', 'Consulta') -Obrigatoria

# 2. Cadastro
Nova-Lista 'Fornecedores' 'Empresa'
Nova-Coluna 'Fornecedores' 'CNPJ'        Text
Nova-Coluna 'Fornecedores' 'Telefone'    Text
Nova-Coluna 'Fornecedores' 'Email'       Text
Nova-Coluna 'Fornecedores' 'Endereco'    Note
Nova-Coluna 'Fornecedores' 'Responsavel' Text
Nova-Coluna 'Fornecedores' 'Ativo'       Boolean
Nova-Coluna 'Fornecedores' 'Observacoes' Note

# 3. Fornecedor x Segmento: status e índices acumulados (o "card" do Dashboard)
Nova-Lista 'FornecedorSegmento' 'Vinculo'                             # ex.: "EISEN — Usinagem"
Nova-Pesquisa 'FornecedorSegmento' 'Fornecedor' 'Fornecedores' -Obrigatoria
Nova-Pesquisa 'FornecedorSegmento' 'Segmento'   'Segmentos'    -Obrigatoria
Nova-Coluna 'FornecedorSegmento' 'Status' Choice @('Em avaliação', 'Homologado', 'Especializado', 'Bloqueado')
Nova-Coluna 'FornecedorSegmento' 'JustificativaStatus' Note
foreach ($c in 'NotaCapacidade', 'MediaQualidade', 'MediaPrazo', 'MediaCusto', 'IndiceGlobal', 'QtdServicos') {
    Nova-Coluna 'FornecedorSegmento' $c Number
}
Nova-Coluna 'FornecedorSegmento' 'UltimoServico' DateTime

# 4. Capacidade técnica de cada fornecedor (uma linha por capacidade avaliada)
Nova-Lista 'AvaliacaoCapacidade'
Nova-Pesquisa 'AvaliacaoCapacidade' 'Vinculo'    'FornecedorSegmento' -Obrigatoria
Nova-Pesquisa 'AvaliacaoCapacidade' 'Capacidade' 'Capacidades'        -Obrigatoria
Nova-Coluna 'AvaliacaoCapacidade' 'Atendimento' Choice @('Atende', 'Atende parcialmente', 'Não atende') -Obrigatoria
Nova-Coluna 'AvaliacaoCapacidade' 'Nota' Number

# 5. Histórico de serviços (uma linha por orçamento/serviço avaliado)
Nova-Lista 'HistoricoServicos' 'Projeto'
Nova-Pesquisa 'HistoricoServicos' 'Vinculo' 'FornecedorSegmento' -Obrigatoria
Nova-Coluna 'HistoricoServicos' 'DataOrcamento' DateTime -Obrigatoria
Nova-Coluna 'HistoricoServicos' 'Projetista'    Text
Nova-Coluna 'HistoricoServicos' 'Relato'        Note
Nova-Coluna 'HistoricoServicos' 'ValorOrcado'   Currency
Nova-Coluna 'HistoricoServicos' 'DataPrevista'  DateTime
Nova-Coluna 'HistoricoServicos' 'DataEntrega'   DateTime
foreach ($c in 'NotaQualidade', 'NotaPrazo', 'NotaCusto') { Nova-Coluna 'HistoricoServicos' $c Number -Obrigatoria }

Write-Host "Estrutura pronta." -ForegroundColor Green
if ($SemDados) { return }

# ---------------------------------------------------------------- dados da planilha
$dir = Join-Path $PSScriptRoot 'dados'
function Ler($nome) { Import-Csv -Path (Join-Path $dir "$nome.csv") -Delimiter ';' -Encoding UTF8 }
function N($v) { if ($v -ne '') { [double]::Parse($v, $inv) } }

$seg = @{}
foreach ($r in Ler 'Segmentos') {
    $seg[$r.Title] = (Add-PnPListItem -List 'Segmentos' -Values @{ Title = $r.Title; Ordem = N $r.Ordem }).Id
}

$cap = @{}
foreach ($r in Ler 'Capacidades') {
    $i = Add-PnPListItem -List 'Capacidades' -Values @{
        Title = $r.Title; Segmento = $seg[$r.Segmento]; Peso = N $r.Peso; Ordem = N $r.Ordem; Ativa = $true }
    $cap["$($r.Segmento)|$($r.Title)"] = @{ Id = $i.Id; Peso = N $r.Peso }
}

foreach ($r in Ler 'CriteriosQualificacao') {
    $v = @{ Title = $r.Title; Dimensao = $r.Dimensao; Nota = N $r.Nota }
    if ($r.Segmento) { $v.Segmento = $seg[$r.Segmento] }
    Add-PnPListItem -List 'CriteriosQualificacao' -Values $v | Out-Null
}

$forn = @{}
foreach ($r in Ler 'Fornecedores') {
    $forn[$r.Title] = (Add-PnPListItem -List 'Fornecedores' -Values @{
        Title = $r.Title; Telefone = $r.Telefone; Endereco = $r.Endereco; Responsavel = $r.Responsavel; Ativo = $true }).Id
}

$vinc = @{}
foreach ($r in Ler 'FornecedorSegmento') {
    $vinc["$($r.Fornecedor)|$($r.Segmento)"] = (Add-PnPListItem -List 'FornecedorSegmento' -Values @{
        Title = "$($r.Fornecedor) — $($r.Segmento)"; Fornecedor = $forn[$r.Fornecedor]
        Segmento = $seg[$r.Segmento]; Status = $r.Status; QtdServicos = 0 }).Id
}

$somaNota = @{}
foreach ($r in Ler 'AvaliacaoCapacidade') {
    $c = $cap["$($r.Segmento)|$($r.Capacidade)"]
    $nota = N $r.Nota
    $atend = if ($nota -eq 0) { 'Não atende' } elseif ($nota -lt $c.Peso) { 'Atende parcialmente' } else { 'Atende' }
    $k = "$($r.Fornecedor)|$($r.Segmento)"
    Add-PnPListItem -List 'AvaliacaoCapacidade' -Values @{
        Title = "$($r.Fornecedor) — $($r.Capacidade)"; Vinculo = $vinc[$k]; Capacidade = $c.Id
        Atendimento = $atend; Nota = $nota } | Out-Null
    $somaNota[$k] += $nota
}

$hist = Ler 'HistoricoServicos'
foreach ($r in $hist) {
    Add-PnPListItem -List 'HistoricoServicos' -Values @{
        Title = $r.Projeto; Vinculo = $vinc["$($r.Fornecedor)|$($r.Segmento)"]; DataOrcamento = $r.DataOrcamento
        Projetista = $r.Projetista; NotaQualidade = N $r.NotaQualidade; NotaPrazo = N $r.NotaPrazo; NotaCusto = N $r.NotaCusto } | Out-Null
}

# índices acumulados — mesma regra que o app aplica ao salvar (ver powerfx.md)
$pesoSeg = @{}
foreach ($k in $cap.Keys) { $pesoSeg[$k.Split('|')[0]] += $cap[$k].Peso }
foreach ($k in $vinc.Keys) {
    $v = @{}
    if ($somaNota.ContainsKey($k)) { $v.NotaCapacidade = [math]::Round($somaNota[$k] / $pesoSeg[$k.Split('|')[1]] * 5, 2) }
    $h = @($hist | Where-Object { "$($_.Fornecedor)|$($_.Segmento)" -eq $k })
    if ($h.Count) {
        $q = ($h | ForEach-Object { N $_.NotaQualidade } | Measure-Object -Average).Average
        $p = ($h | ForEach-Object { N $_.NotaPrazo }     | Measure-Object -Average).Average
        $c = ($h | ForEach-Object { N $_.NotaCusto }     | Measure-Object -Average).Average
        $v += @{ MediaQualidade = [math]::Round($q, 2); MediaPrazo = [math]::Round($p, 2); MediaCusto = [math]::Round($c, 2)
                 IndiceGlobal = [math]::Round(($q + $p + $c) / 3, 2); QtdServicos = $h.Count
                 UltimoServico = ($h | Sort-Object DataOrcamento | Select-Object -Last 1).DataOrcamento }
    }
    if ($v.Count) { Set-PnPListItem -List 'FornecedorSegmento' -Identity $vinc[$k] -Values $v | Out-Null }
}

Write-Host "Dados da planilha importados." -ForegroundColor Green
