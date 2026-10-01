"""Gera site/seed.json a partir de ../dados/*.csv (os mesmos dados da planilha).

O site usa estes registros como carga inicial. As chaves seguem as tabelas
propostas para o Dataverse, para facilitar a migração depois.
"""
import csv
import json
import re
import unicodedata
from pathlib import Path

DADOS = Path(__file__).parent.parent / "dados"


def ler(nome):
    with open(DADOS / f"{nome}.csv", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


def slug(*partes):
    s = "-".join(partes)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:120]


seg = {r["Title"]: "seg-" + slug(r["Title"]) for r in ler("Segmentos")}
out = {k: {} for k in ("segmentos", "capacidades", "criterios", "fornecedores", "vinculos", "servicos")}

for r in ler("Segmentos"):
    out["segmentos"][seg[r["Title"]]] = {"nome": r["Title"], "ordem": int(r["Ordem"])}

cap = {}
for r in ler("Capacidades"):
    cid = "cap-" + slug(r["Segmento"], r["Title"])
    cap[(r["Segmento"], r["Title"])] = (cid, float(r["Peso"]))
    out["capacidades"][cid] = {"segmentoId": seg[r["Segmento"]], "nome": r["Title"],
                               "peso": float(r["Peso"]), "ordem": int(r["Ordem"]), "ativa": True}

for i, r in enumerate(ler("CriteriosQualificacao")):
    out["criterios"][f"crit-{i + 1:03d}"] = {
        "segmentoId": seg[r["Segmento"]] if r["Segmento"] else None,
        "dimensao": r["Dimensao"], "nota": int(r["Nota"]), "descricao": r["Title"]}

forn = {}
for r in ler("Fornecedores"):
    fid = "f-" + slug(r["Title"])
    forn[r["Title"]] = fid
    out["fornecedores"][fid] = {"empresa": r["Title"], "cnpj": "", "telefone": r["Telefone"], "email": "",
                                "endereco": r["Endereco"], "responsavel": r["Responsavel"], "ativo": True,
                                "observacoes": ""}

vinc = {}
for r in ler("FornecedorSegmento"):
    vid = "v-" + slug(r["Fornecedor"], r["Segmento"])
    vinc[(r["Fornecedor"], r["Segmento"])] = vid
    out["vinculos"][vid] = {"fornecedorId": forn[r["Fornecedor"]], "segmentoId": seg[r["Segmento"]],
                            # "Especializado" é um selo manual, separado do status
                            "status": "Em avaliação" if r["Status"] == "Especializado" else r["Status"],
                            "especializado": r["Status"] == "Especializado",
                            "capacidades": {}, "historicoStatus": []}

for r in ler("AvaliacaoCapacidade"):
    cid, peso = cap[(r["Segmento"], r["Capacidade"])]
    nota = float(r["Nota"])
    out["vinculos"][vinc[(r["Fornecedor"], r["Segmento"])]]["capacidades"][cid] = (
        "nao" if nota == 0 else "parcial" if nota < peso else "atende")

for i, r in enumerate(ler("HistoricoServicos")):
    out["servicos"][f"s-{i + 1:04d}"] = {
        "vinculoId": vinc[(r["Fornecedor"], r["Segmento"])], "data": r["DataOrcamento"], "projeto": r["Projeto"],
        "projetista": r["Projetista"], "relato": "", "valor": None, "dataPrevista": None, "dataEntrega": None,
        "q": int(r["NotaQualidade"]), "p": int(r["NotaPrazo"]), "c": int(r["NotaCusto"])}

(Path(__file__).parent / "seed.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print({k: len(v) for k, v in out.items()})
