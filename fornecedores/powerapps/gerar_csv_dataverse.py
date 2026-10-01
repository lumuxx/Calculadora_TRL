"""Gera os CSVs para importar nas tabelas do Dataverse, a partir de ../site/seed.json
(os dados da planilha). Colunas de pesquisa (lookup) vêm com o nome do registro
relacionado, que é como o assistente de importação do Dataverse faz a ligação.

Uso: python3 gerar_csv_dataverse.py
"""
import csv
import json
from pathlib import Path

BASE = Path(__file__).parent
S = json.loads((BASE.parent / "site" / "seed.json").read_text(encoding="utf-8"))
OUT = BASE / "dataverse"
SIM, NAO = "Sim", "Não"


def write(nome, header, rows):
    with open(OUT / f"{nome}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{nome}.csv: {len(rows)} linhas")


def status_por(n, g):
    if n < 2:
        return "Em avaliação"
    if g < 2:
        return "Bloqueado"
    return "Homologado" if n >= 5 and g > 2 else "Em avaliação"


seg = {k: v["nome"] for k, v in S["segmentos"].items()}
cap = S["capacidades"]
forn = S["fornecedores"]
nome_vinc = {k: f'{forn[v["fornecedorId"]]["empresa"]} — {seg[v["segmentoId"]]}' for k, v in S["vinculos"].items()}

# nomes de capacidade precisam ser únicos para a importação ligar a pesquisa
nomes_cap = [c["nome"] for c in cap.values()]
assert len(nomes_cap) == len(set(nomes_cap)), "capacidades com nome repetido entre segmentos"

write("1-Segmentos", ["Nome", "Ordem"], [[v["nome"], v["ordem"]] for v in S["segmentos"].values()])
write("2-Capacidades", ["Nome", "Segmento", "Peso", "Ordem", "Ativa"],
      [[c["nome"], seg[c["segmentoId"]], c["peso"], c["ordem"], SIM if c.get("ativa", True) else NAO] for c in cap.values()])
write("3-Criterios", ["Descricao", "Segmento", "Dimensao", "Nota"],
      [[c["descricao"], seg.get(c["segmentoId"], ""), c["dimensao"], c["nota"]] for c in S["criterios"].values()])
write("4-Fornecedores", ["Empresa", "CNPJ", "Telefone", "Email", "Endereco", "Responsavel", "Ativo", "Observacoes"],
      [[f["empresa"], f["cnpj"], f["telefone"], f["email"], f["endereco"], f["responsavel"],
        SIM if f.get("ativo", True) else NAO, f["observacoes"]] for f in forn.values()])

vrows = []
for vid, v in S["vinculos"].items():
    caps = [c for c in cap.values() if c["segmentoId"] == v["segmentoId"] and c.get("ativa", True)]
    av = v.get("capacidades", {})
    pesos = sum(c["peso"] for c in caps)
    ids = {k for k, c in cap.items() if c["segmentoId"] == v["segmentoId"]}
    pts = sum(c["peso"] if av.get(k) == "atende" else c["peso"] / 2 if av.get(k) == "parcial" else 0
              for k, c in cap.items() if k in ids and c.get("ativa", True))
    ncap = round(pts / pesos * 5, 2) if pesos and av else ""
    h = [s for s in S["servicos"].values() if s["vinculoId"] == vid]
    n = len(h)
    if n:
        q, p, c = (sum(s[k] for s in h) / n for k in "qpc")
        g = (q + p + c) / 3
        med = [round(q, 2), round(p, 2), round(c, 2), round(g, 2)]
        ult = max(s["data"] for s in h)
    else:
        g, med, ult = 0, ["", "", "", ""], ""
    vrows.append([nome_vinc[vid], forn[v["fornecedorId"]]["empresa"], seg[v["segmentoId"]], status_por(n, g),
                  SIM if v.get("especializado") else NAO, ncap, *med, n, ult])
write("5-Vinculos", ["Nome", "Fornecedor", "Segmento", "StatusCalculado", "Especializado", "NotaCapacidade", "MediaQualidade",
                     "MediaPrazo", "MediaCusto", "IndiceGlobal", "QtdServicos", "UltimoServico"], vrows)

arows = []
for vid, v in S["vinculos"].items():
    for cid, at in v.get("capacidades", {}).items():
        arows.append([f'{forn[v["fornecedorId"]]["empresa"]} — {cap[cid]["nome"]}', nome_vinc[vid], cap[cid]["nome"], at])
write("6-AvaliacoesCapacidade", ["Nome", "Vinculo", "Capacidade", "Atendimento"], arows)

write("7-Servicos", ["Projeto", "Vinculo", "DataOrcamento", "Projetista", "Relato", "ValorOrcado", "DataPrevista",
                     "DataEntrega", "NotaQualidade", "NotaPrazo", "NotaCusto"],
      [[s["projeto"], nome_vinc[s["vinculoId"]], s["data"], s["projetista"], s["relato"], s["valor"] or "",
        s["dataPrevista"] or "", s["dataEntrega"] or "", s["q"], s["p"], s["c"]] for s in S["servicos"].values()])
