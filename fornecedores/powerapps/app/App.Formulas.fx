// Cole em App → Formulas (Power Apps Studio).
// Paleta e regras iguais às do site. Telas usam Cor.*, Fonte e as funções abaixo.

Cor = {
    Fundo: RGBA(241, 243, 246, 1),
    Superficie: RGBA(255, 255, 255, 1),
    Afundado: RGBA(232, 235, 240, 1),
    Tinta: RGBA(22, 26, 34, 1),
    Suave: RGBA(88, 97, 114, 1),
    Linha: RGBA(214, 218, 226, 1),
    Destaque: RGBA(51, 65, 184, 1),
    Ok: RGBA(43, 122, 75, 1),
    Espec: RGBA(14, 116, 130, 1),
    Alerta: RGBA(168, 100, 0, 1),
    Ruim: RGBA(179, 38, 30, 1),
    Neutro: RGBA(107, 114, 128, 1),
    Estrela: RGBA(217, 154, 0, 1)
};

Fonte = Font.'Segoe UI';

// "mais de 4 serviços" para ser Homologado
MinServicosHomologado = 5;

// Permissões vêm das funções de segurança do Dataverse (quem não pode, vê os botões escondidos)
PodeRegistrar = DataSourceInfo(Servicos, DataSourceInfo.CreatePermission);
PodeEditarMetodologia = DataSourceInfo(Capacidades, DataSourceInfo.EditPermission);

// ---------- funções ----------
StatusPor(n: Number, g: Number): Text =
    If(n < 2, "Em avaliação",
       g < 2, "Bloqueado",
       n >= MinServicosHomologado && g > 2, "Homologado",
       "Em avaliação");

Motivo(n: Number, g: Number): Text =
    With({sv: n & If(n = 1, " serviço", " serviços")},
        If(n < 2, sv & If(n = 1, " avaliado", " avaliados") & "; são precisos pelo menos 2 para sair de Em avaliação",
           g < 2, sv & ", índice global " & FmtNota(g) & ", abaixo de 2",
           n >= MinServicosHomologado && g > 2, sv & ", índice global " & FmtNota(g) & ", acima de 2",
           n < MinServicosHomologado, sv & ", índice global " & FmtNota(g) & "; faltam " & (MinServicosHomologado - n) & " para poder ser Homologado",
           sv & ", índice global " & FmtNota(g) & "; precisa ficar acima de 2 para ser Homologado"));

CorStatus(s: Text): Color =
    Switch(s,
        "Homologado", Cor.Ok,
        "Bloqueado", Cor.Ruim,
        "Especializado", Cor.Espec,
        Cor.Neutro);

CorNota(n: Number): Color = If(n >= 3.5, Cor.Ok, n >= 2, Cor.Alerta, Cor.Ruim);

FmtNota(n: Number): Text = If(IsBlank(n), "–", Text(n, "0.00", "pt-BR"));
FmtNota1(n: Number): Text = If(IsBlank(n), "–", Text(n, "0.0", "pt-BR"));
