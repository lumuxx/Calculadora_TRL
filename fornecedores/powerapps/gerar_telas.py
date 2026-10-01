"""Gera as telas do app canvas (Power Apps) em YAML, no formato de código do Studio (pa.yaml v3).

Uso:  python3 gerar_telas.py
Gera: telas/<tela>.pa.yaml          -> a tela inteira (Screens: ...)
      telas/controles/<tela>.yaml   -> só a lista de controles, para "Colar código" numa tela vazia

As telas reproduzem o layout do site (cabeçalho com logo e abas, KPIs, cartões de segmento,
ranking com barras e estrelas, ficha do fornecedor, metodologia) usando controles clássicos.
Cores e regras ficam em App.Formulas (ver app/App.Formulas.fx).
"""
from pathlib import Path

import yaml

OUT = Path(__file__).parent / "telas"


# ------------------------------------------------------------------ YAML
class Dumper(yaml.SafeDumper):
    pass


def _str(dumper, s):
    if "\n" in s:
        return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", s)


Dumper.add_representer(str, _str)


def f(x):
    """Converte um valor Python em fórmula Power Fx ("=..." )."""
    if isinstance(x, bool):
        return "=" + ("true" if x else "false")
    if isinstance(x, (int, float)):
        return "=" + str(x)
    x = str(x).strip("\n")
    return x if x.startswith("=") else "=" + x


def ctl(name, control, props, children=None, variant=None):
    body = {"Control": control}
    if variant:
        body["Variant"] = variant
    body["Properties"] = {k: f(v) for k, v in props.items() if v is not None}
    if children:
        body["Children"] = children
    return {name: body}


def q(s):
    """Texto literal Power Fx entre aspas."""
    return '"' + s.replace('"', '""') + '"'


# ------------------------------------------------------------------ peças
def label(name, text, x, y, w, h, size=11, bold=False, color="Cor.Tinta", align=None, fill=None,
          wrap=None, **extra):
    p = {"Text": text, "X": x, "Y": y, "Width": w, "Height": h, "Size": size, "Color": color,
         "Font": "Fonte", "PaddingLeft": 0, "PaddingRight": 0, "PaddingTop": 0, "PaddingBottom": 0}
    if bold:
        p["FontWeight"] = "FontWeight.Semibold" if bold is True else bold
    if align:
        p["Align"] = align
    if fill:
        p["Fill"] = fill
    if wrap is not None:
        p["Wrap"] = wrap
    p.update(extra)
    return ctl(name, "Label", p)


def rect(name, x, y, w, h, fill, **extra):
    p = {"X": x, "Y": y, "Width": w, "Height": h, "Fill": fill}
    p.update(extra)
    return ctl(name, "Rectangle", p)


def button(name, text, x, y, w, h, onselect, primary=False, danger=False, **extra):
    if primary:
        fill, color, border, hover = "Cor.Destaque", "Cor.Superficie", "Cor.Destaque", "ColorFade(Cor.Destaque, -0.12)"
    else:
        fill, color, border, hover = "Cor.Superficie", "Cor.Ruim" if danger else "Cor.Tinta", "Cor.Linha", "Cor.Afundado"
    p = {"Text": text, "X": x, "Y": y, "Width": w, "Height": h, "OnSelect": onselect,
         "Fill": fill, "Color": color, "BorderColor": border, "BorderThickness": 1,
         "HoverFill": hover, "HoverColor": color, "HoverBorderColor": border,
         "PressedFill": hover, "PressedColor": color, "PressedBorderColor": border,
         "RadiusTopLeft": 6, "RadiusTopRight": 6, "RadiusBottomLeft": 6, "RadiusBottomRight": 6,
         "Size": 11, "FontWeight": "FontWeight.Semibold", "Font": "Fonte"}
    p.update(extra)
    return ctl(name, "Classic/Button", p)


def card(name, x, y, w, h, children, **extra):
    """Cartão branco com borda e cantos arredondados (contêiner de layout manual)."""
    p = {"X": x, "Y": y, "Width": w, "Height": h, "Fill": "Cor.Superficie", "BorderColor": "Cor.Linha",
         "BorderThickness": 1, "RadiusTopLeft": 6, "RadiusTopRight": 6, "RadiusBottomLeft": 6,
         "RadiusBottomRight": 6, "DropShadow": "DropShadow.None"}
    p.update(extra)
    return ctl(name, "GroupContainer", p, children, variant="ManualLayout")


def textinput(name, default, x, y, w, h=36, hint="", **extra):
    p = {"Default": default, "HintText": q(hint), "X": x, "Y": y, "Width": w, "Height": h,
         "Size": 11, "Font": "Fonte", "BorderColor": "Cor.Linha", "BorderThickness": 1,
         "HoverBorderColor": "Cor.Suave", "FocusedBorderColor": "Cor.Destaque", "FocusedBorderThickness": 2,
         "RadiusTopLeft": 6, "RadiusTopRight": 6, "RadiusBottomLeft": 6, "RadiusBottomRight": 6,
         "Color": "Cor.Tinta", "Fill": "Cor.Superficie"}
    p.update(extra)
    return ctl(name, "Classic/TextInput", p)


def combobox(name, items, display, x, y, w, h=36, placeholder="", multiple=False, **extra):
    p = {"Items": items, "DisplayFields": f'["{display}"]', "SearchFields": f'["{display}"]',
         "SelectMultiple": multiple, "InputTextPlaceholder": q(placeholder), "IsSearchable": True,
         "X": x, "Y": y, "Width": w, "Height": h, "Font": "Fonte", "Size": 11,
         "BorderColor": "Cor.Linha", "BorderThickness": 1, "ChevronBackground": "Cor.Superficie",
         "ChevronFill": "Cor.Suave", "SelectionFill": "Cor.Destaque", "SelectionColor": "Cor.Superficie"}
    p.update(extra)
    return ctl(name, "Classic/ComboBox", p)


def dropdown(name, items, default, x, y, w, h=36, **extra):
    p = {"Items": items, "Default": default, "X": x, "Y": y, "Width": w, "Height": h, "Font": "Fonte",
         "Size": 11, "BorderColor": "Cor.Linha", "BorderThickness": 1, "ChevronBackground": "Cor.Superficie",
         "ChevronFill": "Cor.Suave", "SelectionFill": "Cor.Destaque", "SelectionColor": "Cor.Superficie"}
    p.update(extra)
    return ctl(name, "Classic/DropDown", p)


def datepicker(name, default, x, y, w, h=36, **extra):
    p = {"DefaultDate": default, "Format": '"dd/mm/yyyy"', "Language": '"pt-BR"', "X": x, "Y": y,
         "Width": w, "Height": h, "Font": "Fonte", "Size": 11, "BorderColor": "Cor.Linha",
         "IconBackground": "Cor.Destaque"}
    p.update(extra)
    return ctl(name, "Classic/DatePicker", p)


def gallery(name, items, x, y, w, h, template_size, children, wrap=1, onselect=None, **extra):
    p = {"Items": items, "X": x, "Y": y, "Width": w, "Height": h, "TemplateSize": template_size,
         "TemplatePadding": 0, "WrapCount": wrap, "ShowScrollbar": True, "BorderThickness": 0}
    if onselect:
        p["OnSelect"] = onselect
    p.update(extra)
    return ctl(name, "Gallery", p, children, variant="BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0")


def barra(prefix, valor, x, y, w):
    """Régua 0–5: trilho + preenchimento colorido + valor (igual ao site)."""
    track_w = f"({w}) - 34"
    return [
        rect(f"{prefix}Trilho", x, y, track_w, 8, "Cor.Afundado"),
        rect(f"{prefix}Valor", x, y, f"({track_w}) * Coalesce({valor}, 0) / 5", 8, f"CorNota({valor})",
             Visible=f"!IsBlank({valor})"),
        label(f"{prefix}Num", f"FmtNota1({valor})", f"{x} + ({w}) - 30", f"{y} - 6", 30, 20, size=10,
              align="Align.Right", color="Cor.Suave"),
    ]


def estrelas(prefix, valor, x, y, size=14):
    w = 90
    return [
        label(f"{prefix}Vazias", '"★★★★★"', x, y, w, 22, size=size, color="Cor.Linha", wrap=False,
              Visible=f"!IsBlank({valor})"),
        label(f"{prefix}Cheias", '"★★★★★"', x, y, f"Max(1, {w} * Coalesce({valor}, 0) / 5)", 22, size=size,
              color="Cor.Estrela", wrap=False, Overflow="Overflow.Hidden", Visible=f"!IsBlank({valor})",
              Tooltip=f'FmtNota({valor}) & " de 5"'),
    ]


TABS = [("Painel", "scrPainel"), ("Fornecedores", "scrFornecedores"), ("Metodologia", "scrMetodologia")]


def cabecalho(sfx, ativa):
    """Barra superior com logo, título e abas. `ativa` = índice da aba destacada."""
    kids = [
        rect(f"recTopo{sfx}", 0, 0, "Parent.Width", 72, "Cor.Superficie"),
        rect(f"recTopoLinha{sfx}", 0, 72, "Parent.Width", 1, "Cor.Linha"),
        ctl(f"imgLogo{sfx}", "Image", {"Image": "logoSenai", "X": 24, "Y": 14, "Width": 204, "Height": 44,
                                        "ImagePosition": "ImagePosition.Fit"}),
        rect(f"recTopoSep{sfx}", 244, 18, 1, 36, "Cor.Linha"),
        label(f"lblTitulo{sfx}", '"Qualificação de Fornecedores"', 260, 12, 420, 30, size=18, bold="FontWeight.Bold"),
        label(f"lblSubtitulo{sfx}", '"Dados compartilhados no Dataverse"', 260, 42, 420, 18, size=10, color="Cor.Suave"),
    ]
    for i, (nome, tela) in enumerate(TABS):
        x = f"Parent.Width - 24 - {len(TABS) - i} * 132"
        on = i == ativa
        kids.append(button(f"btnAba{nome}{sfx}", q(nome), x, 18, 128, 40, f"Navigate({tela}, ScreenTransition.None)",
                           Fill="Color.Transparent", HoverFill="Cor.Afundado", PressedFill="Cor.Afundado",
                           BorderThickness=0, Color="Cor.Tinta" if on else "Cor.Suave",
                           HoverColor="Cor.Tinta", FontWeight="FontWeight.Semibold" if on else "FontWeight.Normal"))
        if on:
            kids.append(rect(f"recAbaAtiva{sfx}", x, 69, 128, 3, "Cor.Destaque"))
    return kids


def tela(nome, children, props=None):
    p = {"Fill": "Cor.Fundo"}
    p.update(props or {})
    return {"Screens": {nome: {"Properties": {k: f(v) for k, v in p.items()}, "Children": children}}}


# ------------------------------------------------------------------ Painel
def scr_painel():
    m = 24
    kids = cabecalho("P", 0)

    # KPIs
    kpis = [
        ("Media", '"MÉDIA GLOBAL"', 'FmtNota(Average(Filter(Vinculos, QtdServicos > 0), IndiceGlobal))',
         '"de 5, entre " & CountRows(Filter(Vinculos, QtdServicos > 0)) & " fornecedores com serviço avaliado"'),
        ("Ativos", '"FORNECEDORES ATIVOS"', 'CountRows(Filter(Fornecedores, Ativo))',
         '"em " & CountRows(Segmentos) & " segmentos"'),
        ("Homolog", '"HOMOLOGADOS"', 'CountRows(Filter(Vinculos, StatusCalculado = "Homologado"))',
         'CountRows(Filter(Vinculos, Especializado)) & " com selo Especializado"'),
        ("Servicos", '"SERVIÇOS AVALIADOS"', 'CountRows(Servicos)', '"qualidade, prazo e custo"'),
    ]
    kw = f"(Parent.Width - {2 * m} - 36) / 4"
    for i, (k, titulo, valor, sub) in enumerate(kpis):
        kids.append(card(f"conKpi{k}", f"{m} + {i} * ({kw} + 12)", 92, kw, 96, [
            label(f"lblKpi{k}Rot", titulo, 16, 12, "Parent.Width - 32", 16, size=9, bold=True, color="Cor.Suave"),
            label(f"lblKpi{k}Val", valor, 16, 30, "Parent.Width - 32", 36, size=24, bold="FontWeight.Bold"),
            label(f"lblKpi{k}Sub", sub, 16, 68, "Parent.Width - 32", 18, size=9, color="Cor.Suave"),
        ]))

    # cartões de segmento (galeria em grade)
    seg_cnt = "CountRows(Filter(Vinculos, Segmento.Segmento = ThisItem.Segmento))"
    def seg_n(st):
        return f'CountRows(Filter(Vinculos, Segmento.Segmento = ThisItem.Segmento && StatusCalculado = "{st}"))'
    bar_w = "Parent.TemplateWidth - 40"
    kids.append(gallery(
        "galSegmentos", "Sort(Segmentos, Ordem)", m, 200, f"Parent.Width - {2 * m}", 92, 88, [
            button("btnSegCard", '""', 0, 0, "Parent.TemplateWidth - 12", 84,
                   "Set(varSegFiltro, If(varSegFiltro.Segmento = ThisItem.Segmento, Blank(), ThisItem))",
                   BorderColor='If(varSegFiltro.Segmento = ThisItem.Segmento, Cor.Destaque, Cor.Linha)',
                   BorderThickness='If(varSegFiltro.Segmento = ThisItem.Segmento, 2, 1)',
                   HoverBorderColor="Cor.Destaque", HoverFill="Cor.Superficie", PressedFill="Cor.Afundado"),
            label("lblSegNome", "Upper(ThisItem.Nome)", 14, 10, "Parent.TemplateWidth - 40", 22, size=12,
                  bold="FontWeight.Bold"),
            rect("recSegBase", 14, 38, bar_w, 6, "Cor.Afundado"),
            rect("recSegAval", 14, 38, f"({bar_w}) * {seg_n('Em avaliação')} / Max(1, {seg_cnt})", 6, "Cor.Neutro"),
            rect("recSegHom", f"14 + ({bar_w}) * {seg_n('Em avaliação')} / Max(1, {seg_cnt})", 38,
                 f"({bar_w}) * {seg_n('Homologado')} / Max(1, {seg_cnt})", 6, "Cor.Ok"),
            rect("recSegBloq", f"14 + ({bar_w}) * ({seg_n('Em avaliação')} + {seg_n('Homologado')}) / Max(1, {seg_cnt})",
                 38, f"({bar_w}) * {seg_n('Bloqueado')} / Max(1, {seg_cnt})", 6, "Cor.Ruim"),
            label("lblSegQtd", f'{seg_cnt} & " fornecedores"', 14, 52, 140, 18, size=9, color="Cor.Suave"),
            label("lblSegMedia",
                  '"média " & FmtNota(Average(Filter(Vinculos, Segmento.Segmento = ThisItem.Segmento && QtdServicos > 0), IndiceGlobal))',
                  "Parent.TemplateWidth - 160", 52, 134, 18, size=9, color="Cor.Suave", align="Align.Right"),
        ], wrap="Max(1, CountRows(Segmentos))", ShowScrollbar=False))

    # ranking
    cols = [("Fornecedor", 0.0, 0.15), ("Segmento", 0.15, 0.13), ("Status", 0.28, 0.13), ("Capacidade", 0.41, 0.095),
            ("Qualidade", 0.505, 0.095), ("Prazo", 0.60, 0.095), ("Custo", 0.695, 0.095), ("Global", 0.79, 0.14),
            ("Serviços", 0.93, 0.07)]
    W = "Parent.TemplateWidth"
    def cx(frac, base=W):
        return f"{base} * {frac}"
    row = [
        label("lblRkEmpresa", "ThisItem.Fornecedor.Empresa", cx(0.0), 0, cx(0.15), 56, size=11, bold=True),
        label("lblRkSegmento", "ThisItem.Segmento.Nome", cx(0.15), 0, cx(0.13), 56, size=11),
        label("lblRkStatus", "ThisItem.StatusCalculado", cx(0.28), 8, 116, 22, size=9, bold=True, align="Align.Center",
              color="CorStatus(ThisItem.StatusCalculado)", fill="ColorFade(CorStatus(ThisItem.StatusCalculado), 0.85)",
              Tooltip="Motivo(ThisItem.QtdServicos, ThisItem.IndiceGlobal)"),
        label("lblRkEspec", '"Especializado"', cx(0.28), 32, 116, 18, size=8, bold=True, align="Align.Center",
              color="Cor.Espec", fill="ColorFade(Cor.Espec, 0.85)", Visible="ThisItem.Especializado"),
    ]
    for key, col, frac in [("Cap", "NotaCapacidade", 0.41), ("Q", "MediaQualidade", 0.505),
                           ("P", "MediaPrazo", 0.60), ("C", "MediaCusto", 0.695)]:
        row += barra(f"recRk{key}", f"ThisItem.{col}", f"{cx(frac)} + 4", 24, f"{cx(0.095)} - 12")
    row += estrelas("lblRkEstrela", "ThisItem.IndiceGlobal", cx(0.79), 17)
    row += [
        label("lblRkGlobal", "FmtNota(ThisItem.IndiceGlobal)", f"{cx(0.79)} + 96", 0, 56, 56, size=12,
              bold="FontWeight.Bold"),
        label("lblRkServ", "Coalesce(ThisItem.QtdServicos, 0)", cx(0.93), 8, cx(0.07), 20, size=11,
              bold=True, align="Align.Center"),
        label("lblRkUltimo", 'If(IsBlank(ThisItem.UltimoServico), "", "últ. " & Text(ThisItem.UltimoServico, "dd/mm/yyyy"))',
              cx(0.93), 28, cx(0.07), 18, size=8, color="Cor.Suave", align="Align.Center"),
        rect("recRkLinha", 0, 55, W, 1, "Cor.Linha"),
    ]
    gal_items = """=With({busca: Lower(Trim(txtBuscaPainel.Text))},
    Sort(
        Sort(
            Filter(Vinculos,
                IsBlank(varSegFiltro) || Segmento.Segmento = varSegFiltro.Segmento,
                drpStatusPainel.Selected.Value = "Todos os status"
                    || If(drpStatusPainel.Selected.Value = "Especializado", Especializado, StatusCalculado = drpStatusPainel.Selected.Value),
                IsBlank(busca) || busca in Lower(Fornecedor.Empresa)
            ),
            Coalesce(NotaCapacidade, -1), SortOrder.Descending
        ),
        Coalesce(IndiceGlobal, -1), SortOrder.Descending
    )
)"""
    gw = "Parent.Width - 32"
    rk = [
        label("lblRanking", 'If(IsBlank(varSegFiltro), "Ranking", "Ranking · " & varSegFiltro.Nome)', 16, 14, 400, 30,
              size=16, bold="FontWeight.Bold"),
        textinput("txtBuscaPainel", '""', "Parent.Width - 16 - 200 - 12 - 200 - 12 - 200", 12, 200,
                  hint="Buscar fornecedor", DelayOutput=True),
        combobox("cbSegPainel", "Sort(Segmentos, Ordem)", "Nome", "Parent.Width - 16 - 200 - 12 - 200", 12, 200,
                 placeholder="Todos os segmentos", DefaultSelectedItems="If(IsBlank(varSegFiltro), Blank(), [varSegFiltro])",
                 OnChange="Set(varSegFiltro, Self.Selected)"),
        dropdown("drpStatusPainel", '["Todos os status", "Em avaliação", "Homologado", "Bloqueado", "Especializado"]',
                 '"Todos os status"', "Parent.Width - 16 - 200", 12, 200),
    ]
    for nome, x0, w in cols:
        rk.append(label(f"lblCab{nome.replace('ç', 'c')}", q(nome.upper()), f"16 + ({gw}) * {x0}", 60, f"({gw}) * {w}", 20,
                        size=9, bold=True, color="Cor.Suave",
                        align="Align.Center" if nome == "Serviços" else None))
    rk += [
        rect("recCabLinha", 16, 82, gw, 1, "Cor.Linha"),
        gallery("galRanking", gal_items, 16, 84, gw, "Parent.Height - 84 - 40", 56, row,
                onselect="Set(varForn, LookUp(Fornecedores, Fornecedor = ThisItem.Fornecedor.Fornecedor)); "
                         "Set(varVinc, ThisItem); Navigate(scrFicha, ScreenTransition.None)"),
        label("lblRankNota",
              '"Notas de 0 a 5. Global = média de qualidade, prazo e custo; as estrelas mostram a mesma nota. '
              'O status é calculado automaticamente (passe o mouse sobre ele para ver o motivo). '
              'Especializado é um selo manual."',
              16, "Parent.Height - 34", gw, 28, size=9, color="Cor.Suave", wrap=True),
    ]
    kids.append(card("conRanking", m, 304, f"Parent.Width - {2 * m}", "Parent.Height - 304 - 24", rk))
    return tela("scrPainel", kids)


# ------------------------------------------------------------------ Fornecedores
def scr_fornecedores():
    m = 24
    kids = cabecalho("F", 1)
    itens = """=With({busca: Lower(Trim(txtBuscaForn.Text))},
    SortByColumns(
        Filter(Fornecedores As fo,
            IsBlank(busca) || busca in Lower(fo.Empresa) || busca in Lower(fo.Responsavel) || busca in Lower(fo.CNPJ),
            IsBlank(varSegFiltro)
                || !IsBlank(LookUp(Vinculos, Fornecedor.Fornecedor = fo.Fornecedor && Segmento.Segmento = varSegFiltro.Segmento))
        ),
        "Empresa"
    )
)"""
    W = "Parent.TemplateWidth"
    row = [
        label("lblFoEmpresa", 'ThisItem.Empresa & If(ThisItem.Ativo, "", "  (inativo)")', 0, 0, f"{W} * 0.22", 52,
              size=11, bold=True),
        label("lblFoSegmentos",
              'Concat(Filter(Vinculos, Fornecedor.Fornecedor = ThisItem.Fornecedor), '
              'Segmento.Nome & ": " & StatusCalculado & If(Especializado, " + Especializado", ""), "   ·   ")',
              f"{W} * 0.22", 0, f"{W} * 0.40", 52, size=10, wrap=True),
        label("lblFoResp", 'Coalesce(ThisItem.Responsavel, "–")', f"{W} * 0.62", 0, f"{W} * 0.14", 52, size=10),
        label("lblFoTel", 'Coalesce(ThisItem.Telefone, "–")', f"{W} * 0.76", 0, f"{W} * 0.12", 52, size=10),
        label("lblFoContato", '"contato a completar"', f"{W} * 0.88", 0, f"{W} * 0.12", 52, size=9, color="Cor.Alerta",
              Visible="IsBlank(ThisItem.Telefone) && IsBlank(ThisItem.Email) && IsBlank(ThisItem.Endereco)"),
        rect("recFoLinha", 0, 51, W, 1, "Cor.Linha"),
    ]
    gw = "Parent.Width - 32"
    corpo = [
        label("lblFornTitulo", 'If(IsBlank(varSegFiltro), "Fornecedores", "Fornecedores · " & varSegFiltro.Nome)',
              16, 14, 400, 30, size=16, bold="FontWeight.Bold"),
        textinput("txtBuscaForn", '""', "Parent.Width - 16 - 160 - 12 - 200 - 12 - 240", 12, 240,
                  hint="Empresa, CNPJ ou responsável", DelayOutput=True),
        combobox("cbSegForn", "Sort(Segmentos, Ordem)", "Nome", "Parent.Width - 16 - 160 - 12 - 200", 12, 200,
                 placeholder="Todos os segmentos", DefaultSelectedItems="If(IsBlank(varSegFiltro), Blank(), [varSegFiltro])",
                 OnChange="Set(varSegFiltro, Self.Selected)"),
        button("btnNovoForn", '"Novo fornecedor"', "Parent.Width - 16 - 160", 12, 160, 36,
               "Set(varForn, Blank()); Navigate(scrFornecedorForm, ScreenTransition.None)", primary=True,
               Visible="PodeRegistrar"),
    ]
    for nome, x0, w in [("Empresa", 0, .22), ("Segmentos e status", .22, .40), ("Responsável", .62, .14),
                        ("Telefone", .76, .12)]:
        corpo.append(label(f"lblFoCab{x0}".replace(".", ""), q(nome.upper()), f"16 + ({gw}) * {x0}", 60,
                           f"({gw}) * {w}", 20, size=9, bold=True, color="Cor.Suave"))
    corpo += [
        rect("recFoCabLinha", 16, 82, gw, 1, "Cor.Linha"),
        gallery("galFornecedores", itens, 16, 84, gw, "Parent.Height - 84 - 12", 52, row,
                onselect="Set(varForn, ThisItem); "
                         "Set(varVinc, First(Filter(Vinculos, Fornecedor.Fornecedor = ThisItem.Fornecedor))); "
                         "Navigate(scrFicha, ScreenTransition.None)"),
    ]
    kids.append(card("conFornecedores", m, 92, f"Parent.Width - {2 * m}", "Parent.Height - 92 - 24", corpo))
    return tela("scrFornecedores", kids)


# ------------------------------------------------------------------ Cadastro de fornecedor
def scr_form():
    m = 24
    kids = cabecalho("C", 1)
    w2 = "(Parent.Width - 48 - 16) / 2"
    x2 = f"24 + {w2} + 16"
    campos = [
        ("Empresa", "Empresa *", 24, 64, w2, "Empresa"),
        ("Cnpj", "CNPJ", x2, 64, w2, "CNPJ"),
        ("Resp", "Responsável no fornecedor", 24, 132, w2, "Responsavel"),
        ("Tel", "Telefone", x2, 132, w2, "Telefone"),
        ("Email", "E-mail", 24, 200, w2, "Email"),
        ("End", "Endereço", x2, 200, w2, "Endereco"),
    ]
    corpo = [label("lblFormTitulo", 'If(IsBlank(varForn), "Novo fornecedor", "Editar " & varForn.Empresa)', 24, 18,
                   600, 30, size=16, bold="FontWeight.Bold")]
    for k, rot, x, y, w, col in campos:
        corpo += [label(f"lblForm{k}", q(rot), x, y, w, 18, size=9, color="Cor.Suave", bold=True),
                  textinput(f"txtForm{k}", f"varForn.{col}", x, f"{y} + 20", w)]
    corpo += [
        label("lblFormSegs", '"Segmentos em que atua"', 24, 268, w2, 18, size=9, color="Cor.Suave", bold=True),
        combobox("cbFormSegs", "Sort(Segmentos, Ordem)", "Nome", 24, 288, w2, placeholder="Escolha os segmentos",
                 multiple=True,
                 DefaultSelectedItems="Filter(Segmentos As s, !IsBlank(LookUp(Vinculos, "
                                      "Fornecedor.Fornecedor = varForn.Fornecedor && Segmento.Segmento = s.Segmento)))"),
        ctl("chkFormAtivo", "Classic/CheckBox", {"Text": '"Fornecedor ativo"', "Default": "Coalesce(varForn.Ativo, true)",
                                                  "X": x2, "Y": 288, "Width": 240, "Height": 36, "Size": 11,
                                                  "Font": "Fonte", "CheckboxBorderColor": "Cor.Suave",
                                                  "CheckmarkFill": "Cor.Superficie", "CheckboxBackgroundFill": "Cor.Destaque"}),
        label("lblFormObs", '"Observações"', 24, 336, "Parent.Width - 48", 18, size=9, color="Cor.Suave", bold=True),
        textinput("txtFormObs", "varForn.Observacoes", 24, 356, "Parent.Width - 48", 80, Mode="TextMode.MultiLine"),
        label("lblFormNota",
              '"Desmarcar um segmento não apaga o histórico. Para tirar o fornecedor de uso, desmarque \'Fornecedor ativo\'."',
              24, 444, "Parent.Width - 48", 20, size=9, color="Cor.Suave"),
        button("btnFormCancelar", '"Cancelar"', "Parent.Width - 24 - 140 - 12 - 120", 476, 120, 38, "Back()"),
        button("btnFormSalvar", 'If(IsBlank(varForn), "Cadastrar", "Salvar")', "Parent.Width - 24 - 140", 476, 140, 38,
               """If(IsBlank(Trim(txtFormEmpresa.Text)),
    Notify("Informe o nome da empresa.", NotificationType.Error),
    Set(varForn,
        Patch(Fornecedores, If(IsBlank(varForn), Defaults(Fornecedores), varForn), {
            Empresa: Trim(txtFormEmpresa.Text),
            CNPJ: txtFormCnpj.Text,
            Responsavel: txtFormResp.Text,
            Telefone: txtFormTel.Text,
            Email: txtFormEmail.Text,
            Endereco: txtFormEnd.Text,
            Observacoes: txtFormObs.Text,
            Ativo: chkFormAtivo.Value
        })
    );
    ForAll(cbFormSegs.SelectedItems As s,
        If(IsBlank(LookUp(Vinculos, Fornecedor.Fornecedor = varForn.Fornecedor && Segmento.Segmento = s.Segmento)),
            Patch(Vinculos, Defaults(Vinculos), {
                Nome: varForn.Empresa & " — " & s.Nome,
                Fornecedor: varForn,
                Segmento: s,
                StatusCalculado: "Em avaliação",
                Especializado: false,
                QtdServicos: 0
            })
        )
    );
    Set(varVinc, First(Filter(Vinculos, Fornecedor.Fornecedor = varForn.Fornecedor)));
    Notify("Fornecedor salvo.", NotificationType.Success);
    Navigate(scrFicha, ScreenTransition.None)
)""", primary=True),
    ]
    kids.append(card("conForm", m, 92, f"Min(960, Parent.Width - {2 * m})", 540, corpo))
    reset = "; ".join(f"Reset(txtForm{k})" for k, *_ in campos) + "; Reset(txtFormObs); Reset(cbFormSegs); Reset(chkFormAtivo)"
    return tela("scrFornecedorForm", kids, {"OnVisible": reset})


# ------------------------------------------------------------------ Ficha
CARREGAR = """=ClearCollect(colAval, Filter(AvaliacoesCapacidade, Vinculo.Vinculo = varVinc.Vinculo));
ClearCollect(colHist, Sort(Filter(Servicos, Vinculo.Vinculo = varVinc.Vinculo), DataOrcamento, SortOrder.Ascending));
Clear(colTL);
If(CountRows(colHist) > 0, ClearCollect(colTL,
    ForAll(Sequence(CountRows(colHist)) As i,
        With({sub: FirstN(colHist, i.Value)},
            With({g: (Sum(sub, NotaQualidade) + Sum(sub, NotaPrazo) + Sum(sub, NotaCusto)) / (3 * i.Value)},
                {i: i.Value, data: Last(sub).DataOrcamento, g: g, st: StatusPor(i.Value, g)}
            )
        )
    )
))"""

RECALC_SERV = """=With({h: Filter(Servicos, Vinculo.Vinculo = varVinc.Vinculo)},
    With({n: CountRows(h), q: Average(h, NotaQualidade), p: Average(h, NotaPrazo), c: Average(h, NotaCusto)},
        Set(varVinc,
            Patch(Vinculos, LookUp(Vinculos, Vinculo = varVinc.Vinculo), {
                MediaQualidade: If(n > 0, Round(q, 2)),
                MediaPrazo: If(n > 0, Round(p, 2)),
                MediaCusto: If(n > 0, Round(c, 2)),
                IndiceGlobal: If(n > 0, Round((q + p + c) / 3, 2)),
                QtdServicos: n,
                UltimoServico: Max(h, DataOrcamento),
                StatusCalculado: StatusPor(n, If(n > 0, (q + p + c) / 3, 0))
            })
        )
    )
);
Select(btnCarregarFicha)"""

RECALC_CAP = """=With({caps: Filter(Capacidades, Segmento.Segmento = varVinc.Segmento.Segmento && Ativa)},
    With({pesos: Sum(caps, Peso)},
        Set(varVinc,
            Patch(Vinculos, LookUp(Vinculos, Vinculo = varVinc.Vinculo), {
                NotaCapacidade: If(pesos > 0 && CountRows(colAval) > 0,
                    Round(Sum(caps As k,
                        Switch(LookUp(colAval, Capacidade.Capacidade = k.Capacidade).Atendimento,
                            "atende", k.Peso, "parcial", k.Peso / 2, 0)) / pesos * 5, 2))
            })
        )
    )
)"""


def marcar(valor):
    return f"""With({{ex: LookUp(colAval, Capacidade.Capacidade = ThisItem.Capacidade)}},
    If(IsBlank(ex),
        Patch(AvaliacoesCapacidade, Defaults(AvaliacoesCapacidade), {{
            Nome: varForn.Empresa & " — " & ThisItem.Nome,
            Vinculo: varVinc,
            Capacidade: ThisItem,
            Atendimento: "{valor}"
        }}),
        Patch(AvaliacoesCapacidade, LookUp(AvaliacoesCapacidade, AvaliacaoCapacidade = ex.AvaliacaoCapacidade), {{Atendimento: "{valor}"}})
    )
);
ClearCollect(colAval, Filter(AvaliacoesCapacidade, Vinculo.Vinculo = varVinc.Vinculo));
Select(btnRecalcCap)"""


def scr_ficha():
    m = 24
    kids = cabecalho("D", 1)
    kids += [
        button("btnVoltarFicha", '"‹ Fornecedores"', m, 84, 140, 30, "Navigate(scrFornecedores, ScreenTransition.None)",
               Fill="Color.Transparent", BorderThickness=0, Color="Cor.Destaque", HoverColor="Cor.Destaque",
               HoverFill="Cor.Afundado", Align="Align.Left", PaddingLeft=4),
        # botões ocultos usados com Select()
        button("btnCarregarFicha", '"carregar"', 0, 0, 10, 10, CARREGAR, Visible=False),
        button("btnRecalcServ", '"recalc"', 0, 0, 10, 10, RECALC_SERV, Visible=False),
        button("btnRecalcCap", '"recalc cap"', 0, 0, 10, 10, RECALC_CAP, Visible=False),
    ]
    # dados do fornecedor
    facts = [("Responsável", "Responsavel"), ("Telefone", "Telefone"), ("E-mail", "Email"), ("CNPJ", "CNPJ"),
             ("Endereço", "Endereco")]
    dados = [
        label("lblFiEmpresa", 'varForn.Empresa & If(varForn.Ativo, "", "  (inativo)")', 16, 10, "Parent.Width - 200", 34,
              size=20, bold="FontWeight.Bold"),
        button("btnEditarForn", '"Editar cadastro"', "Parent.Width - 16 - 150", 12, 150, 34,
               "Navigate(scrFornecedorForm, ScreenTransition.None)", Visible="PodeRegistrar"),
    ]
    fw = "(Parent.Width - 32) / 5"
    for i, (rot, col) in enumerate(facts):
        dados += [
            label(f"lblFiRot{col}", q(rot.upper()), f"16 + {i} * {fw}", 52, f"{fw} - 12", 16, size=8, bold=True,
                  color="Cor.Suave"),
            label(f"lblFiVal{col}", f'Coalesce(varForn.{col}, "–")', f"16 + {i} * {fw}", 68, f"{fw} - 12", 36, size=10,
                  wrap=True, VerticalAlign="VerticalAlign.Top"),
        ]
    kids.append(card("conFiDados", m, 118, f"Parent.Width - {2 * m}", 110, dados))

    # segmentos do fornecedor (chips)
    kids.append(gallery("galFiSegs", "Filter(Vinculos, Fornecedor.Fornecedor = varForn.Fornecedor)", m, 238,
                        f"Parent.Width - {2 * m}", 36, 34, [
        button("btnFiSegChip", "ThisItem.Segmento.Nome", 0, 0, "Parent.TemplateWidth - 8", 32,
               "Set(varVinc, ThisItem); Select(btnCarregarFicha)",
               Fill='If(ThisItem.Vinculo = varVinc.Vinculo, Cor.Tinta, Cor.Superficie)',
               Color='If(ThisItem.Vinculo = varVinc.Vinculo, Cor.Superficie, Cor.Tinta)',
               HoverColor='If(ThisItem.Vinculo = varVinc.Vinculo, Cor.Superficie, Cor.Tinta)',
               HoverFill='If(ThisItem.Vinculo = varVinc.Vinculo, Cor.Tinta, Cor.Afundado)',
               RadiusTopLeft=16, RadiusTopRight=16, RadiusBottomLeft=16, RadiusBottomRight=16, Size=10),
    ], wrap=6, ShowScrollbar=False,
        Visible="CountRows(Filter(Vinculos, Fornecedor.Fornecedor = varForn.Fornecedor)) > 1"))

    # status e índices
    sc_w = "(Parent.Width * 0.62 - 16 - 48) / 5"
    st = [
        label("lblFiSeg", "Upper(varVinc.Segmento.Nome)", 16, 12, 260, 26, size=13, bold="FontWeight.Bold"),
        label("lblFiStatus", "varVinc.StatusCalculado", 280, 14, 120, 22, size=9, bold=True, align="Align.Center",
              color="CorStatus(varVinc.StatusCalculado)", fill="ColorFade(CorStatus(varVinc.StatusCalculado), 0.85)"),
        label("lblFiEspec", '"Especializado"', 406, 14, 120, 22, size=9, bold=True, align="Align.Center",
              color="Cor.Espec", fill="ColorFade(Cor.Espec, 0.85)", Visible="varVinc.Especializado"),
        ctl("chkEspecializado", "Classic/CheckBox", {
            "Text": '"Especializado (manual)"', "Default": "varVinc.Especializado",
            "X": "Parent.Width * 0.62 - 16 - 230", "Y": 10, "Width": 230, "Height": 32, "Size": 10, "Font": "Fonte",
            "DisplayMode": "If(PodeRegistrar, DisplayMode.Edit, DisplayMode.View)",
            "CheckboxBorderColor": "Cor.Suave", "CheckmarkFill": "Cor.Superficie", "CheckboxBackgroundFill": "Cor.Espec",
            "OnCheck": "If(!varVinc.Especializado, Set(varVinc, Patch(Vinculos, LookUp(Vinculos, Vinculo = varVinc.Vinculo), {Especializado: true})); Notify(\"Selo Especializado marcado.\", NotificationType.Success))",
            "OnUncheck": "If(varVinc.Especializado, Set(varVinc, Patch(Vinculos, LookUp(Vinculos, Vinculo = varVinc.Vinculo), {Especializado: false})); Notify(\"Selo Especializado removido.\", NotificationType.Success))",
        }),
        label("lblFiMotivo", '"Status calculado automaticamente: " & Motivo(Coalesce(varVinc.QtdServicos, 0), varVinc.IndiceGlobal) & "."',
              16, 44, "Parent.Width * 0.62 - 32", 20, size=10, color="Cor.Suave"),
    ]
    scores = [("Cap", "CAPACIDADE", "varVinc.NotaCapacidade"), ("Q", "QUALIDADE", "varVinc.MediaQualidade"),
              ("P", "PRAZO", "varVinc.MediaPrazo"), ("C", "CUSTO", "varVinc.MediaCusto"),
              ("G", "ÍNDICE GLOBAL", "varVinc.IndiceGlobal")]
    for i, (k, rot, val) in enumerate(scores):
        x = f"16 + {i} * ({sc_w} + 12)"
        filhos = [
            label(f"lblSc{k}Rot", q(rot), 10, 8, "Parent.Width - 20", 14, size=8, bold=True, color="Cor.Suave"),
            label(f"lblSc{k}Val", f"FmtNota({val})", 10, 24, "Parent.Width - 20", 30, size=18, bold="FontWeight.Bold"),
        ]
        if k == "G":
            filhos += estrelas("lblScG", val, 10, 60, size=12)
        else:
            filhos += barra(f"recSc{k}", val, 10, 66, "Parent.Width - 20")
        st.append(card(f"conSc{k}", x, 74, sc_w, 92, filhos,
                       BorderColor="Cor.Destaque" if k == "G" else "Cor.Linha"))
    st += [
        rect("recFiSep", "Parent.Width * 0.62", 12, 1, 156, "Cor.Linha"),
        label("lblFiTLRot", '"MUDANÇAS DE STATUS"', "Parent.Width * 0.62 + 16", 12, "Parent.Width * 0.38 - 32", 16,
              size=8, bold=True, color="Cor.Suave"),
        label("lblFiTL",
              """With({mud: Filter(colTL As t, t.st <> If(t.i = 1, "Em avaliação", Index(colTL, t.i - 1).st))},
    If(CountRows(mud) = 0, "Nenhuma mudança: o fornecedor está em avaliação desde o cadastro.",
        Concat(Sort(mud, i, SortOrder.Descending),
            Text(data, "dd/mm/yyyy") & "  ·  " & st & "  (ao chegar a " & i & " serviços, global " & FmtNota(g) & ")",
            Char(10))))""",
              "Parent.Width * 0.62 + 16", 32, "Parent.Width * 0.38 - 32", 136, size=10, wrap=True,
              VerticalAlign="VerticalAlign.Top"),
    ]
    kids.append(card("conFiStatus", m, 282, f"Parent.Width - {2 * m}", 180, st))

    # capacidade técnica
    cap_row = [
        label("lblCapNome", "ThisItem.Nome", 0, 4, "Parent.TemplateWidth - 270", 22, size=11),
        label("lblCapPeso", '"peso " & Text(ThisItem.Peso, "0.0", "pt-BR")', 0, 26, 120, 16, size=8, color="Cor.Suave"),
        rect("recCapLinha", 0, 47, "Parent.TemplateWidth", 1, "Cor.Linha"),
    ]
    atual = "LookUp(colAval, Capacidade.Capacidade = ThisItem.Capacidade).Atendimento"
    for i, (v, t, cor) in enumerate([("atende", "Atende", "Cor.Ok"), ("parcial", "Parcial", "Cor.Alerta"),
                                     ("nao", "Não atende", "Cor.Tinta")]):
        on = f'{atual} = "{v}"'
        cap_row.append(button(f"btnCap{t.replace(' ', '').replace('ã', 'a')}", q(t),
                              f"Parent.TemplateWidth - 264 + {i} * 88", 8, 84, 30, marcar(v),
                              Fill=f"If({on}, ColorFade({cor}, 0.82), Cor.Superficie)",
                              Color=f"If({on}, {cor}, Cor.Suave)", HoverColor=f"If({on}, {cor}, Cor.Tinta)",
                              HoverFill=f"If({on}, ColorFade({cor}, 0.75), Cor.Afundado)",
                              FontWeight=f"If({on}, FontWeight.Semibold, FontWeight.Normal)", Size=9,
                              DisplayMode="If(PodeRegistrar, DisplayMode.Edit, DisplayMode.View)"))
    capw = "(Parent.Width - 48 - 16) * 0.42"
    kids.append(card("conFiCap", m, 474, capw, "Parent.Height - 474 - 24", [
        label("lblCapTit", '"CAPACIDADE TÉCNICA"', 16, 12, 260, 22, size=11, bold="FontWeight.Bold"),
        label("lblCapTot", 'FmtNota1(varVinc.NotaCapacidade) & " / 5"', "Parent.Width - 16 - 100", 12, 100, 22, size=10,
              color="Cor.Suave", align="Align.Right"),
        gallery("galCapacidades", "Sort(Filter(Capacidades, Segmento.Segmento = varVinc.Segmento.Segmento && Ativa), Ordem)",
                16, 44, "Parent.Width - 32", "Parent.Height - 44 - 36", 48, cap_row),
        label("lblCapLegenda", '"Atende = peso cheio · Parcial = metade do peso · Não atende = 0"', 16,
              "Parent.Height - 28", "Parent.Width - 32", 18, size=8, color="Cor.Suave"),
    ]))

    # histórico de serviços
    W = "Parent.TemplateWidth"
    def nota_col(k, col, dim, x):
        return [
            label(f"lblHi{k}", f"ThisItem.{col}", x, 6, 30, 22, size=12, bold="FontWeight.Bold"),
            label(f"lblHi{k}Desc",
                  f'LookUp(Criterios, Dimensao = "{dim}" && Nota = ThisItem.{col}'
                  + (' && Segmento.Segmento = varVinc.Segmento.Segmento' if dim == "Qualidade" else ' && IsBlank(Segmento)')
                  + ').Descricao',
                  x, 28, f"{W} * 0.17", 36, size=8, color="Cor.Suave", wrap=True, VerticalAlign="VerticalAlign.Top"),
        ]
    hi_row = [
        label("lblHiData", 'Text(ThisItem.DataOrcamento, "dd/mm/yyyy")', 0, 6, f"{W} * 0.14", 22, size=10),
        label("lblHiProjeto", "ThisItem.Projeto", f"{W} * 0.14", 6, f"{W} * 0.25", 22, size=11, bold=True),
        label("lblHiProjetista", "ThisItem.Projetista", f"{W} * 0.14", 28, f"{W} * 0.25", 18, size=9, color="Cor.Suave"),
        *nota_col("Q", "NotaQualidade", "Qualidade", f"{W} * 0.40"),
        *nota_col("P", "NotaPrazo", "Prazo", f"{W} * 0.58"),
        *nota_col("C", "NotaCusto", "Custo", f"{W} * 0.76"),
        button("btnHiExcluir", 'If(locConfirmaServ = ThisItem.Servico, "Confirmar", "Excluir")', f"{W} - 84", 10, 80, 28,
               """If(locConfirmaServ = ThisItem.Servico,
    Remove(Servicos, LookUp(Servicos, Servico = ThisItem.Servico)); UpdateContext({locConfirmaServ: Blank()}); Select(btnRecalcServ);
    Notify("Serviço excluído.", NotificationType.Success),
    UpdateContext({locConfirmaServ: ThisItem.Servico})
)""", danger=True, Size=9, Visible="PodeRegistrar"),
        rect("recHiLinha", 0, 67, W, 1, "Cor.Linha"),
    ]
    hix = f"{m} + {capw} + 16"
    hiw = "(Parent.Width - 48 - 16) * 0.58"
    kids.append(card("conFiHist", hix, 474, hiw, "Parent.Height - 474 - 24", [
        label("lblHiTit", '"HISTÓRICO DE SERVIÇOS"', 16, 12, 300, 22, size=11, bold="FontWeight.Bold"),
        button("btnRegistrar", '"Registrar serviço"', "Parent.Width - 16 - 170", 8, 170, 34,
               "Reset(txtSvProjeto); Reset(dpSvOrc); Reset(txtSvProjetista); Reset(txtSvValor); Reset(dpSvPrev); "
               "Reset(dpSvEnt); Reset(cbSvQ); Reset(cbSvP); Reset(cbSvC); Reset(txtSvRelato); "
               "UpdateContext({locPainelServ: true})", primary=True, Visible="PodeRegistrar"),
        label("lblHiVazio", '"Nenhum serviço registrado. Ao concluir um serviço, registre o projeto e escolha a situação de qualidade, prazo e custo; as médias e o status se atualizam sozinhos."',
              16, 52, "Parent.Width - 32", 44, size=10, color="Cor.Suave", wrap=True,
              Visible="CountRows(colHist) = 0"),
        gallery("galHistorico", "Sort(colHist, DataOrcamento, SortOrder.Descending)", 16, 48, "Parent.Width - 32",
                "Parent.Height - 56", 68, hi_row),
    ]))

    # painel "Registrar serviço" (sobreposto)
    crit = lambda dim, extra="": (f'AddColumns(Sort(Filter(Criterios, Dimensao = "{dim}"{extra}), Nota, SortOrder.Descending), '
                                  f'Rotulo, Nota & " – " & Descricao)')
    sug_prazo = """If(IsBlank(dpSvPrev.SelectedDate) || IsBlank(dpSvEnt.SelectedDate), Blank(),
    With({d: DateDiff(dpSvPrev.SelectedDate, dpSvEnt.SelectedDate, TimeUnit.Days)},
        [LookUp(""" + crit("Prazo") + """, Nota = If(d <= 0, 5, d = 1, 4, d <= 3, 3, d <= 7, 2, 1))]))"""
    fw2 = "(Parent.Width - 48 - 16) / 2"
    fx2 = f"24 + {fw2} + 16"
    form = [
        label("lblSvTit", '"Registrar serviço"', 24, 16, "Parent.Width - 48", 30, size=16, bold="FontWeight.Bold"),
        label("lblSvSub", 'varForn.Empresa & " · " & varVinc.Segmento.Nome', 24, 46, "Parent.Width - 48", 18, size=10,
              color="Cor.Suave"),
    ]
    fields = [
        ("Projeto *", textinput("txtSvProjeto", '""', 24, 92, fw2, hint="Ex.: CORAL-SOL"), 24, 72, fw2),
        ("Data do orçamento *", datepicker("dpSvOrc", "Today()", fx2, 92, fw2), fx2, 72, fw2),
        ("Projetista", textinput("txtSvProjetista", "User().FullName", 24, 156, fw2), 24, 136, fw2),
        ("Valor orçado (R$)", textinput("txtSvValor", '""', fx2, 156, fw2, Format="TextFormat.Number"), fx2, 136, fw2),
        ("Entrega prevista", datepicker("dpSvPrev", "Blank()", 24, 220, fw2), 24, 200, fw2),
        ("Entrega real", datepicker("dpSvEnt", "Blank()", fx2, 220, fw2), fx2, 200, fw2),
        ("Índice de qualidade *", combobox("cbSvQ", crit("Qualidade", " && Segmento.Segmento = varVinc.Segmento.Segmento"),
                                           "Rotulo", 24, 284, "Parent.Width - 48", placeholder="Escolha a situação"),
         24, 264, "Parent.Width - 48"),
        ("Índice de prazo *", combobox("cbSvP", crit("Prazo"), "Rotulo", 24, 348, "Parent.Width - 48",
                                       placeholder="Escolha a situação (sugerido pelas datas)",
                                       DefaultSelectedItems=sug_prazo), 24, 328, "Parent.Width - 48"),
        ("Índice de custo *", combobox("cbSvC", crit("Custo"), "Rotulo", 24, 412, "Parent.Width - 48",
                                       placeholder="Escolha a situação"), 24, 392, "Parent.Width - 48"),
        ("Relato", textinput("txtSvRelato", '""', 24, 476, "Parent.Width - 48", 72, Mode="TextMode.MultiLine",
                             hint="O que aconteceu no serviço, ajustes necessários, contato com o fornecedor…"),
         24, 456, "Parent.Width - 48"),
    ]
    for i, (rot, control, x, y, w) in enumerate(fields):
        form += [label(f"lblSv{i}", q(rot), x, y, w, 18, size=9, bold=True, color="Cor.Suave"), control]
    pode_salvar = ("!IsBlank(Trim(txtSvProjeto.Text)) && !IsBlank(dpSvOrc.SelectedDate) && "
                   "!IsBlank(cbSvQ.Selected) && !IsBlank(cbSvP.Selected) && !IsBlank(cbSvC.Selected)")
    form += [
        button("btnSvCancelar", '"Cancelar"', "Parent.Width - 24 - 140 - 12 - 120", 564, 120, 38,
               "UpdateContext({locPainelServ: false})"),
        button("btnSvSalvar", '"Registrar"', "Parent.Width - 24 - 140", 564, 140, 38, """Patch(Servicos, Defaults(Servicos), {
    Projeto: Trim(txtSvProjeto.Text),
    Vinculo: varVinc,
    DataOrcamento: dpSvOrc.SelectedDate,
    Projetista: txtSvProjetista.Text,
    Relato: txtSvRelato.Text,
    ValorOrcado: If(IsBlank(txtSvValor.Text), Blank(), Value(txtSvValor.Text)),
    DataPrevista: dpSvPrev.SelectedDate,
    DataEntrega: dpSvEnt.SelectedDate,
    NotaQualidade: cbSvQ.Selected.Nota,
    NotaPrazo: cbSvP.Selected.Nota,
    NotaCusto: cbSvC.Selected.Nota
});
UpdateContext({locPainelServ: false});
Select(btnRecalcServ);
Notify("Serviço registrado.", NotificationType.Success)""", primary=True,
               DisplayMode=f"If({pode_salvar}, DisplayMode.Edit, DisplayMode.Disabled)"),
    ]
    kids.append(ctl("conPainelServ", "GroupContainer", {
        "X": 0, "Y": 0, "Width": "Parent.Width", "Height": "Parent.Height", "Visible": "locPainelServ",
        "Fill": "RGBA(10, 12, 18, 0.45)", "DropShadow": "DropShadow.None"}, [
        card("conPainelServCard", "(Parent.Width - Min(720, Parent.Width - 32)) / 2", "Max(16, (Parent.Height - 620) / 2)",
             "Min(720, Parent.Width - 32)", 620, form, DropShadow="DropShadow.Bold", RadiusTopLeft=10,
             RadiusTopRight=10, RadiusBottomLeft=10, RadiusBottomRight=10),
    ], variant="ManualLayout"))
    return tela("scrFicha", kids, {
        "OnVisible": "UpdateContext({locPainelServ: false, locConfirmaServ: Blank()});\n" + CARREGAR.lstrip("=")})


# ------------------------------------------------------------------ Metodologia
RECALC_SEG = """=ClearCollect(colVincSeg, Filter(Vinculos, Segmento.Segmento = locSeg.Segmento));
With({caps: Filter(Capacidades, Segmento.Segmento = locSeg.Segmento && Ativa)},
    With({pesos: Sum(caps, Peso)},
        ForAll(colVincSeg As v,
            With({av: Filter(AvaliacoesCapacidade, Vinculo.Vinculo = v.Vinculo)},
                Patch(Vinculos, LookUp(Vinculos, Vinculo = v.Vinculo), {
                    NotaCapacidade: If(pesos > 0 && CountRows(av) > 0,
                        Round(Sum(caps As k,
                            Switch(LookUp(av, Capacidade.Capacidade = k.Capacidade).Atendimento,
                                "atende", k.Peso, "parcial", k.Peso / 2, 0)) / pesos * 5, 2))
                })
            )
        )
    )
)"""


def crit_editor(prefix, dim, seg_expr, x, y, w):
    """Tabela Nota 5..0 com a descrição editável de cada situação."""
    filtro = (f'Dimensao = "{dim}" && Nota = ThisItem.Value && '
              + (f"Segmento.Segmento = {seg_expr}.Segmento" if seg_expr else "IsBlank(Segmento)"))
    row = [
        label(f"lbl{prefix}Nota", "ThisItem.Value", 0, 0, 40, 40, size=12, bold="FontWeight.Bold", align="Align.Center"),
        textinput(f"txt{prefix}Desc", f"LookUp(Criterios, {filtro}).Descricao", 48, 4, "Parent.TemplateWidth - 52", 32,
                  hint="Descreva a situação que vale esta nota",
                  DisplayMode="If(PodeEditarMetodologia, DisplayMode.Edit, DisplayMode.View)",
                  OnChange=f"""With({{ex: LookUp(Criterios, {filtro})}},
    If(IsBlank(ex),
        If(!IsBlank(Trim(Self.Text)),
            Patch(Criterios, Defaults(Criterios), {{Descricao: Trim(Self.Text), Dimensao: "{dim}", Nota: ThisItem.Value"""
                           + (f", Segmento: {seg_expr}" if seg_expr else "") + """})),
        Patch(Criterios, ex, {Descricao: Trim(Self.Text)})
    )
)"""),
    ]
    return gallery(f"gal{prefix}", "Sort(Sequence(6, 0), Value, SortOrder.Descending)", x, y, w, 6 * 40, 40, row,
                   ShowScrollbar=False)


def scr_metodologia():
    m = 24
    kids = cabecalho("M", 2)
    kids.append(button("btnRecalcSeg", '"recalc seg"', 0, 0, 10, 10, RECALC_SEG, Visible=False))

    # lista de segmentos (esquerda)
    seg_row = [
        button("btnSegItem", "ThisItem.Nome", 0, 0, "Parent.TemplateWidth", 40,
               "UpdateContext({locSeg: ThisItem, locConfirmaSeg: false})",
               Fill='If(ThisItem.Segmento = locSeg.Segmento, Cor.Tinta, Cor.Superficie)',
               Color='If(ThisItem.Segmento = locSeg.Segmento, Cor.Superficie, Cor.Tinta)',
               HoverColor='If(ThisItem.Segmento = locSeg.Segmento, Cor.Superficie, Cor.Tinta)',
               HoverFill='If(ThisItem.Segmento = locSeg.Segmento, Cor.Tinta, Cor.Afundado)',
               Align="Align.Left", PaddingLeft=12, BorderThickness=0),
    ]
    lw = 280
    kids.append(card("conMetSegs", m, 92, lw, "Parent.Height - 92 - 24", [
        label("lblMetSegsTit", '"SEGMENTOS"', 16, 14, 200, 20, size=10, bold="FontWeight.Bold"),
        gallery("galMetSegs", "Sort(Segmentos, Ordem)", 12, 44, "Parent.Width - 24", "Parent.Height - 44 - 110", 44,
                seg_row, ShowScrollbar=False),
        label("lblNovoSegRot", '"Novo segmento"', 16, "Parent.Height - 100", 200, 18, size=9, bold=True,
              color="Cor.Suave", Visible="PodeEditarMetodologia"),
        textinput("txtNovoSeg", '""', 16, "Parent.Height - 80", "Parent.Width - 32", hint="Ex.: Corte a laser",
                  Visible="PodeEditarMetodologia"),
        button("btnNovoSeg", '"Adicionar segmento"', 16, "Parent.Height - 40", "Parent.Width - 32", 32, """If(!IsBlank(Trim(txtNovoSeg.Text)),
    UpdateContext({locSeg: Patch(Segmentos, Defaults(Segmentos), {Nome: Trim(txtNovoSeg.Text), Ordem: CountRows(Segmentos) + 1})});
    Reset(txtNovoSeg)
)""", Visible="PodeEditarMetodologia"),
    ]))

    # detalhe do segmento (direita)
    cap_row = [
        textinput("txtCapNome", "ThisItem.Nome", 0, 4, "Parent.TemplateWidth - 220", 34,
                  DisplayMode="If(PodeEditarMetodologia, DisplayMode.Edit, DisplayMode.View)",
                  OnChange="If(!IsBlank(Trim(Self.Text)), Patch(Capacidades, ThisItem, {Nome: Trim(Self.Text)}))"),
        dropdown("drpCapPeso", "[0.5, 1, 1.5, 2]", "ThisItem.Peso", "Parent.TemplateWidth - 208", 4, 96, 34,
                 DisplayMode="If(PodeEditarMetodologia, DisplayMode.Edit, DisplayMode.View)",
                 OnChange="Patch(Capacidades, ThisItem, {Peso: Self.Selected.Value}); Select(btnRecalcSeg)"),
        button("btnCapRemover", '"Remover"', "Parent.TemplateWidth - 100", 6, 96, 30,
               "Patch(Capacidades, ThisItem, {Ativa: false}); Select(btnRecalcSeg)", Size=9,
               Visible="PodeEditarMetodologia"),
    ]
    rx = f"{m} + {lw} + 16"
    rw = f"Parent.Width - {m} - {lw} - 16 - {m}"
    half = "(Parent.Width - 48) / 2"
    detalhe = [
        label("lblMetSeg", 'If(IsBlank(locSeg), "Escolha um segmento", Upper(locSeg.Nome))', 16, 14, 400, 28, size=14,
              bold="FontWeight.Bold"),
        label("lblMetPesos", '"soma dos pesos: " & Text(Sum(Filter(Capacidades, Segmento.Segmento = locSeg.Segmento && Ativa), Peso), "0.0", "pt-BR")',
              "Parent.Width - 16 - 150 - 12 - 220", 18, 220, 20, size=10, color="Cor.Suave", align="Align.Right",
              Visible="!IsBlank(locSeg)"),
        button("btnExcluirSeg", '"Excluir segmento"', "Parent.Width - 16 - 150", 12, 150, 32,
               "UpdateContext({locConfirmaSeg: true})", danger=True,
               Visible="PodeEditarMetodologia && !IsBlank(locSeg) && !locConfirmaSeg"),
        # confirmação de exclusão
        ctl("conConfirmaSeg", "GroupContainer", {
            "X": 16, "Y": 52, "Width": "Parent.Width - 32", "Height": 96, "Visible": "locConfirmaSeg",
            "Fill": "ColorFade(Cor.Ruim, 0.9)", "BorderColor": "ColorFade(Cor.Ruim, 0.5)", "BorderThickness": 1,
            "RadiusTopLeft": 6, "RadiusTopRight": 6, "RadiusBottomLeft": 6, "RadiusBottomRight": 6,
            "DropShadow": "DropShadow.None"}, [
            label("lblConfirmaSeg",
                  """With({vs: Filter(Vinculos, Segmento.Segmento = locSeg.Segmento)},
    "Excluir o segmento " & locSeg.Nome & "? Isto apaga também " &
    CountRows(Filter(Capacidades, Segmento.Segmento = locSeg.Segmento)) & " capacidades, " &
    CountRows(Filter(Criterios, Segmento.Segmento = locSeg.Segmento)) & " critérios de qualidade, a ligação de " &
    CountRows(vs) & " fornecedores com este segmento e os serviços registrados nele. Os fornecedores continuam cadastrados. Não dá para desfazer."
)""", 14, 8, "Parent.Width - 28", 44, size=10, wrap=True, VerticalAlign="VerticalAlign.Top"),
            button("btnConfirmaSeg", '"Excluir " & locSeg.Nome', 14, 54, 200, 32, """ForAll(Filter(Vinculos, Segmento.Segmento = locSeg.Segmento) As v,
    RemoveIf(Servicos, Vinculo.Vinculo = v.Vinculo);
    RemoveIf(AvaliacoesCapacidade, Vinculo.Vinculo = v.Vinculo)
);
RemoveIf(Vinculos, Segmento.Segmento = locSeg.Segmento);
RemoveIf(Capacidades, Segmento.Segmento = locSeg.Segmento);
RemoveIf(Criterios, Segmento.Segmento = locSeg.Segmento);
Remove(Segmentos, locSeg);
If(varSegFiltro.Segmento = locSeg.Segmento, Set(varSegFiltro, Blank()));
UpdateContext({locSeg: First(Sort(Segmentos, Ordem)), locConfirmaSeg: false});
Notify("Segmento excluído.", NotificationType.Success)""", danger=True),
            button("btnCancelaSeg", '"Cancelar"', 226, 54, 110, 32, "UpdateContext({locConfirmaSeg: false})"),
        ], variant="ManualLayout"),
        label("lblMetCapTit", '"CAPACIDADES EXIGIDAS"', 16, "If(locConfirmaSeg, 160, 56)", half, 18, size=9, bold=True,
              color="Cor.Suave"),
        gallery("galMetCaps", "Sort(Filter(Capacidades, Segmento.Segmento = locSeg.Segmento && Ativa), Ordem)", 16,
                "If(locConfirmaSeg, 180, 78)", half, 7 * 42, 42, cap_row, ShowScrollbar=True),
        textinput("txtNovaCap", '""', 16, "If(locConfirmaSeg, 180, 78) + 7 * 42 + 8", f"{half} - 120",
                  hint="Nova capacidade", Visible="PodeEditarMetodologia && !IsBlank(locSeg)"),
        button("btnNovaCap", '"Adicionar"', f"16 + {half} - 110", "If(locConfirmaSeg, 180, 78) + 7 * 42 + 8", 110, 36,
               """If(!IsBlank(Trim(txtNovaCap.Text)),
    Patch(Capacidades, Defaults(Capacidades), {
        Nome: Trim(txtNovaCap.Text), Segmento: locSeg, Peso: 1, Ativa: true,
        Ordem: Max(Filter(Capacidades, Segmento.Segmento = locSeg.Segmento), Ordem) + 1
    });
    Reset(txtNovaCap);
    Select(btnRecalcSeg)
)""", Visible="PodeEditarMetodologia && !IsBlank(locSeg)"),
        label("lblMetQTit", '"ÍNDICE DE QUALIDADE (deste segmento)"', f"32 + {half}", "If(locConfirmaSeg, 160, 56)", half, 18,
              size=9, bold=True, color="Cor.Suave"),
        crit_editor("CritQ", "Qualidade", "locSeg", f"32 + {half}", "If(locConfirmaSeg, 180, 78)", half),
        rect("recMetSep", 16, "If(locConfirmaSeg, 180, 78) + 7 * 42 + 60", "Parent.Width - 32", 1, "Cor.Linha"),
        label("lblMetPTit", '"ÍNDICE DE PRAZO (todos os segmentos)"', 16, "If(locConfirmaSeg, 180, 78) + 7 * 42 + 76", half,
              18, size=9, bold=True, color="Cor.Suave"),
        crit_editor("CritP", "Prazo", None, 16, "If(locConfirmaSeg, 180, 78) + 7 * 42 + 98", half),
        label("lblMetCTit", '"ÍNDICE DE CUSTO (todos os segmentos)"', f"32 + {half}", "If(locConfirmaSeg, 180, 78) + 7 * 42 + 76",
              half, 18, size=9, bold=True, color="Cor.Suave"),
        crit_editor("CritC", "Custo", None, f"32 + {half}", "If(locConfirmaSeg, 180, 78) + 7 * 42 + 98", half),
        label("lblMetRegra",
              '"Status (automático): menos de 2 serviços → Em avaliação · índice global abaixo de 2 → Bloqueado · '
              '5 ou mais serviços e global acima de 2 → Homologado · demais casos → Em avaliação. '
              'Especializado é um selo manual na ficha do fornecedor."',
              16, "If(locConfirmaSeg, 180, 78) + 7 * 42 + 98 + 6 * 40 + 12", "Parent.Width - 32", 40, size=9,
              color="Cor.Alerta", wrap=True),
    ]
    kids.append(card("conMetDetalhe", rx, 92, rw, "Parent.Height - 92 - 24", detalhe))
    return tela("scrMetodologia", kids, {
        "OnVisible": "If(IsBlank(locSeg), UpdateContext({locSeg: First(Sort(Segmentos, Ordem)), locConfirmaSeg: false}))"})


# ------------------------------------------------------------------ saída
def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "controles").mkdir(exist_ok=True)
    for doc in (scr_painel(), scr_fornecedores(), scr_form(), scr_ficha(), scr_metodologia()):
        (nome, corpo), = doc["Screens"].items()
        txt = yaml.dump(doc, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=1000)
        (OUT / f"{nome}.pa.yaml").write_text(txt, encoding="utf-8")
        ctl_txt = yaml.dump(corpo["Children"], Dumper=Dumper, sort_keys=False, allow_unicode=True, width=1000)
        (OUT / "controles" / f"{nome}.yaml").write_text(ctl_txt, encoding="utf-8")
        print(nome, txt.count("Control:"), "controles")


if __name__ == "__main__":
    main()
