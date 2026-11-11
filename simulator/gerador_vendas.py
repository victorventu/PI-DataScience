#!/usr/bin/env python3
"""
gerador_vendas.py
------------------
Gera dados SINTÉTICOS de vendas com a mesma estrutura (mesmas 43 colunas)
do relatório real da empresa parceira do Projeto Integrador (FCA).

Nenhum dado real da empresa é usado. Nomes de clientes, fornecedores,
vendedores e cidades são gerados por algoritmo (biblioteca Faker, pt_BR).

DOIS MODOS DE USO
-----------------
1) LOTE (histórico): gera de uma vez todo o histórico de vendas entre duas
   datas (padrão: 01/01/2016 a 31/10/2026) — é a base para EDA, Data
   Warehouse, Machine Learning e Spark.
2) CONTÍNUO (streaming): fica rodando e gera novos pedidos com a data/hora
   de AGORA, em intervalos aleatórios — simula o sistema de vendas "ao vivo"
   e continua a numeração de onde o histórico parou.

O QUE O HISTÓRICO TEM DE REALISTA
---------------------------------
- Sazonalidade: nutrição/mineralização vendem mais na seca (maio a setembro);
  vermífugos e afins mais na época das chuvas; leite tem outro padrão.
- Tendência: o volume de vendas cresce ~6% ao ano; fins de semana vendem bem
  menos que dias úteis.
- Preços reajustados ao longo dos anos (~6% a.a.): o preço de 2016 é bem
  menor que o de 2026.
- Clientes: cada cliente "entra" em uma data (a base de clientes cresce) e
  alguns compram muito mais que outros (poucos clientes grandes).
- Numeração (pedido, orçamento, NF, cupom) SEMPRE crescente em ordem
  cronológica, e IdProduto estável entre execuções.
- Comissão (Vr.Comiss.) acumulada por vendedor DENTRO do mês.
- Sujeira proposital (datas em formatos diferentes, nomes em maiúsculo/
  minúsculo/Title Case) controlada por --pct-sujeira.

ESTADO ENTRE EXECUÇÕES
----------------------
Clientes, vendedores, códigos e contadores são salvos em um arquivo JSON
(padrão: estado_gerador.json, na mesma pasta do CSV). Assim, o modo contínuo
continua exatamente de onde o lote terminou, sem repetir números.

Dependência externa: Faker (`pip install faker`).

EXEMPLOS
--------
    # 1) Histórico completo (jan/2016 a out/2026), recomeçando do zero:
    python3 gerador_vendas.py --pedidos 100000 --seed 42 --sobrescrever \\
            --saida dados/vendas.csv

    # 2) Streaming (continua a numeração do histórico):
    python3 gerador_vendas.py --continuo --intervalo-min 2 --intervalo-max 20 \\
            --saida dados/vendas_live.csv

    # 3) Streaming com limite (bom para cron/testes): gera 20 pedidos e para
    python3 gerador_vendas.py --continuo --limite 20 --intervalo-min 1 \\
            --intervalo-max 3 --saida dados/vendas_live.csv
"""

import argparse
import bisect
import csv
import itertools
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta

from faker import Faker

# --------------------------------------------------------------------------
# 0. PARÂMETROS DO "MUNDO" SIMULADO
# --------------------------------------------------------------------------

INICIO_PADRAO = "2016-01-01"
FIM_PADRAO = "2026-10-31"
PEDIDOS_PADRAO = 100000          # ~140 mil linhas (cada pedido tem ~1,4 item)

CRESCIMENTO_ANUAL = 0.06         # crescimento do volume de vendas por ano
INFLACAO_ANUAL = 0.06            # reajuste anual dos preços
REFERENCIA_PRECOS = datetime(2026, 10, 31)  # os preços do catálogo valem nesta data

PCT_SUJEIRA_PADRAO = 0.15        # 15% dos campos de data/texto saem "fora do padrão"

# Volume geral de pedidos por mês (jan..dez)
SAZ_VOLUME_MES = [1.00, 0.95, 1.00, 1.00, 1.10, 1.15, 1.15, 1.15, 1.05, 1.05, 1.00, 0.85]

# Peso de cada dia da semana (seg..dom): sábado vende pouco, domingo quase nada
FATOR_DIA_SEMANA = [1.0, 1.0, 1.0, 1.0, 1.0, 0.45, 0.03]

# Sazonalidade por GRUPO de produto (jan..dez): qual mês "puxa" qual produto
_SECA = [0.85, 0.80, 0.85, 1.00, 1.20, 1.35, 1.45, 1.50, 1.30, 1.05, 0.90, 0.85]
SAZ_GRUPO = {
    "NUTRIÇÃO":           _SECA,   # suplementação forte na seca
    "KM":                 _SECA,
    "QUALIDADE DE LEITE": [1.15, 1.15, 1.10, 1.00, 0.90, 0.85, 0.80, 0.85, 0.95, 1.10, 1.15, 1.15],
    "GERAL":              [1.20, 1.10, 1.00, 0.90, 0.85, 0.80, 0.80, 0.85, 0.95, 1.20, 1.30, 1.25],
    "QUIMICOS":           [1.00] * 12,
    "USO E CONSUMO":      [1.00] * 12,
    "SERVIÇO":            [1.00] * 12,
}

# --------------------------------------------------------------------------
# 1. CATÁLOGO E LISTAS DE REFERÊNCIA
# --------------------------------------------------------------------------

SUFIXOS_EMPRESA = ["LTDA", "ME", "EIRELI", "S.A.", "Comércio e Representações"]
PREFIXOS_PROPRIEDADE_RURAL = ["Fazenda", "Sítio", "Chácara", "Agropecuária"]

CONDICOES_PAGAMENTO = [
    "1-A VISTA", "2-30 DIAS", "27-40 DIAS", "29-50 DIAS", "63-28 DIAS",
    "66-7 DIAS", "77-300/400/500 DIAS", "81-100/200 DIAS", "83-200", "84-120 DIAS",
]

# (nome, grupo, unidade, preco_min, preco_max, marca) — preços válidos em out/2026
CATALOGO_PRODUTOS = [
    ("NUTRIBOI MAX 0,3 (SC 25KG)",          "NUTRIÇÃO",           "SC", 2.20, 3.10, "REPRESENTAÇÃO"),
    ("FOSFANIM 40P - 30KG",                 "NUTRIÇÃO",           "KG", 3.00, 4.20, "INDEFINIDA"),
    ("SUPLEMENTO NOVILHA M (SC 30KG)",      "NUTRIÇÃO",           "SC", 5.00, 6.80, "REPRESENTAÇÃO"),
    ("RACAO MATERNA PREMIUM 25KG",          "NUTRIÇÃO",           "KG", 12.50, 16.90, "INDEFINIDA"),
    ("SAL MINERAL EQUILIBRIO 25KG",         "NUTRIÇÃO",           "KG", 4.50, 5.90, "INDEFINIDA"),
    ("PLACA IDENTIFICACAO ANIMAL",          "GERAL",              "UN", 30.00, 40.00, "INDEFINIDA"),
    ("KIT COLETA DE LEITE",                 "QUALIDADE DE LEITE", "UN", 25.00, 45.00, "INDEFINIDA"),
    ("REAGENTE ANALISE DE LEITE 1L",        "QUALIDADE DE LEITE", "LT", 60.00, 90.00, "INDEFINIDA"),
    ("DESINFETANTE INDUSTRIAL 5L",          "QUIMICOS",           "PC", 35.00, 55.00, "INDEFINIDA"),
    ("DETERGENTE ACIDO CIP 20L",            "QUIMICOS",           "PC", 80.00, 120.00, "INDEFINIDA"),
    ("SERVICO DE CONSULTORIA A CAMPO",      "SERVIÇO",            "UN", 90.00, 300.00, "INDEFINIDA"),
    ("SERVICO DE FRETE / TRANSPORTE",       "SERVIÇO",            "UN", 50.00, 250.00, "INDEFINIDA"),
    ("LUVA DESCARTAVEL (CX 100 UN)",        "USO E CONSUMO",      "PC", 18.00, 28.00, "INDEFINIDA"),
    ("SERINGA DESCARTAVEL 20ML (MIL)",      "USO E CONSUMO",      "MIL", 90.00, 140.00, "INDEFINIDA"),
    ("VERMIFUGO BOVINO INJETAVEL 500ML",    "GERAL",              "UN", 40.00, 65.00, "REPRESENTAÇÃO"),
    ("MINERALIZADOR KM SACO 30KG",          "KM",                 "KG", 3.50, 4.80, "INDEFINIDA"),
]

# Pesos de sorteio de cada produto, mês a mês (segue a sazonalidade do grupo)
PESOS_ITEM_MES = {
    mes: [SAZ_GRUPO[p[1]][mes - 1] for p in CATALOGO_PRODUTOS] for mes in range(1, 13)
}

TIPO_VENDA_POR_GRUPO = {"SERVIÇO": "SERVIÇOS"}

SUBGRUPOS_POR_GRUPO = {
    "NUTRIÇÃO": ["Ração", "Sal Mineral", "Suplemento", "Concentrado Proteico"],
    "QUALIDADE DE LEITE": ["Higienização", "Análise de Leite", "Coleta"],
    "QUIMICOS": ["Desinfetante", "Detergente", "Sanitizante"],
    "SERVIÇO": ["Consultoria", "Transporte", "Assistência Técnica"],
    "USO E CONSUMO": ["Descartável", "EPI", "Material de Apoio"],
    "GERAL": ["Identificação Animal", "Medicamento", "Diversos"],
    "KM": ["Mineralização"],
}

# --------------------------------------------------------------------------
# 2. CABEÇALHO — precisa ficar EXATAMENTE igual ao relatório real
# --------------------------------------------------------------------------

COLUNAS = [
    "Nº Ped.", "Nº Orc.", "Dt.Ped.", "Cliente", "Produto", "IdProduto", "Qnt.",
    "Total Líquido", "Vendedor", "Vr.Unit.", "Grupo", "Marca", "Fornecedor",
    "Tot.Kg Bruto", "Total Bruto", "Peso Br. Un.", "Dt.Cup.Sat.", "Dt.NF Lcto.",
    "N° NF.", "Dt.Cupom", "Cód. NF.", "Dt.NF.Emis.", "Nº Cup.", "Nº Cup.Sat.",
    "Peso Líq. Un.", "Tot.Desc.", "Cód.Cliente", "Vr.Comiss.", "Un.", "Condição",
    "Tot.Kg Líq.", "SubGrupo", "Venc. Pedido", "Emissão Fin.", "Vr.Total NF.",
    "Venc. Cupom", "Venc. Nota", "Título", "Cidade", "Estado", "Tipo Venda",
    "Preço Compra.", "Modelo NF",
]

# --------------------------------------------------------------------------
# 3. "SUJEIRA" PROPOSITAL (formatos de data e capitalização)
# --------------------------------------------------------------------------

FORMATOS_DATA_HORA = [
    "%Y-%m-%d %H:%M:%S",   # padrão do sistema
    "%d/%m/%Y %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
]

FORMATOS_DATA_CURTA = [
    "%d/%m/%y",            # padrão do sistema
    "%d-%m-%y",
    "%d/%m/%Y",
    "%Y-%m-%d",
]


def _fmt_data(dt, pct_sujeira=PCT_SUJEIRA_PADRAO):
    if dt is None:
        return None
    if random.random() < pct_sujeira:
        return dt.strftime(random.choice(FORMATOS_DATA_HORA[1:]))
    return dt.strftime(FORMATOS_DATA_HORA[0])


def _fmt_data_br(dt, pct_sujeira=PCT_SUJEIRA_PADRAO):
    if dt is None:
        return None
    if random.random() < pct_sujeira:
        return dt.strftime(random.choice(FORMATOS_DATA_CURTA[1:]))
    return dt.strftime(FORMATOS_DATA_CURTA[0])


def _variar_caixa(texto, pct_sujeira=PCT_SUJEIRA_PADRAO):
    """Maioria em MAIÚSCULO (padrão do relatório real); o resto varia entre
    Title Case e minúsculo, simulando digitação manual."""
    if texto is None:
        return None
    if random.random() >= pct_sujeira:
        return texto.upper()
    return texto.title() if random.random() < 0.5 else texto.lower()


# --------------------------------------------------------------------------
# 4. POOLS FICTÍCIOS (clientes, vendedores, fornecedores, cidades)
# --------------------------------------------------------------------------


def criar_pools_ficticios(fake, data_inicio, data_fim, n_vendedores=4,
                          n_fornecedores=5, n_clientes=400, n_cidades=25):
    """Cria, uma única vez, os nomes fictícios usados em todo o histórico.

    Clientes: ~30% já existem em `data_inicio`; os demais "entram" em datas
    sorteadas ao longo do período (a carteira cresce). Cada cliente tem um
    peso de compra (poucos clientes grandes, muitos pequenos)."""

    vendedores = [fake.name() for _ in range(n_vendedores)]

    fornecedores = [
        f"{fake.company()} {random.choice(SUFIXOS_EMPRESA)}" for _ in range(n_fornecedores)
    ]
    fornecedores.append(None)  # ~1/6 dos itens ficam sem fornecedor preenchido

    total_dias = max((data_fim - data_inicio).days, 1)
    n_iniciais = int(n_clientes * 0.30)
    clientes = []
    for i in range(n_clientes):
        if random.random() < 0.45:
            nome = f"{random.choice(PREFIXOS_PROPRIEDADE_RURAL)} {fake.last_name()}"
        else:
            nome = fake.name()
            if random.random() < 0.25:
                nome += " e Outro" if random.random() < 0.5 else " e Outros"
        inicio = data_inicio if i < n_iniciais else data_inicio + timedelta(days=random.randint(0, total_dias))
        peso = min(random.paretovariate(1.4), 30.0)
        clientes.append({"nome": nome, "inicio": inicio, "peso": peso})

    cidades_estados = [(fake.city(), fake.estado_sigla()) for _ in range(n_cidades)]

    return {
        "vendedores": vendedores,
        "fornecedores": fornecedores,
        "clientes": clientes,
        "cidades_estados": cidades_estados,
    }


# --------------------------------------------------------------------------
# 5. ESTADO (contadores + pools) — persistido em JSON entre execuções
# --------------------------------------------------------------------------


class GeradorEstado:
    def __init__(self, pools, contadores=None, codigos_cliente=None,
                 saldo_comissao=None, pct_sujeira=PCT_SUJEIRA_PADRAO):
        self.pools = pools
        c = contadores or {}
        self.proximo_pedido = c.get("pedido", 14600)
        self.proximo_orcamento = c.get("orcamento", 12701)
        self.proximo_nf = c.get("nf", 6997)
        self.proximo_cupom = c.get("cupom", 8800)
        self.codigos_cliente = codigos_cliente or {}
        self.saldo_comissao = saldo_comissao or {}   # {vendedor: [ano-mes, valor]}
        self.pct_sujeira = pct_sujeira

        # Clientes ordenados por data de entrada (para sortear só quem já existia)
        self.pools["clientes"].sort(key=lambda cl: cl["inicio"])
        self._inicios = [cl["inicio"] for cl in self.pools["clientes"]]
        self._cum_pesos = list(itertools.accumulate(cl["peso"] for cl in self.pools["clientes"]))

    def sortear_cliente(self, dt):
        k = max(bisect.bisect_right(self._inicios, dt), 1)
        return random.choices(self.pools["clientes"][:k], cum_weights=self._cum_pesos[:k])[0]["nome"]

    def codigo_cliente(self, cliente):
        if cliente not in self.codigos_cliente:
            self.codigos_cliente[cliente] = random.randint(100, 5000)
        return self.codigos_cliente[cliente]

    def acumular_comissao(self, vendedor, dt, valor_venda):
        """Comissão acumulada do vendedor dentro do mês (zera na virada do mês)."""
        ano_mes = dt.strftime("%Y-%m")
        ref = self.saldo_comissao.get(vendedor)
        if ref is None or ref[0] != ano_mes:
            ref = [ano_mes, 0.0]
        ref[1] += valor_venda * 0.03
        self.saldo_comissao[vendedor] = ref
        return round(ref[1], 2)


def salvar_estado(estado, caminho):
    dados = {
        "versao": 2,
        "contadores": {
            "pedido": estado.proximo_pedido,
            "orcamento": estado.proximo_orcamento,
            "nf": estado.proximo_nf,
            "cupom": estado.proximo_cupom,
        },
        "vendedores": estado.pools["vendedores"],
        "fornecedores": estado.pools["fornecedores"],
        "cidades_estados": [list(ce) for ce in estado.pools["cidades_estados"]],
        "clientes": [
            {"nome": c["nome"], "inicio": c["inicio"].isoformat(), "peso": c["peso"]}
            for c in estado.pools["clientes"]
        ],
        "codigos_cliente": estado.codigos_cliente,
        "saldo_comissao": estado.saldo_comissao,
    }
    os.makedirs(os.path.dirname(os.path.abspath(caminho)) or ".", exist_ok=True)
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)
    os.replace(tmp, caminho)


def carregar_estado(caminho, pct_sujeira):
    with open(caminho, encoding="utf-8") as f:
        d = json.load(f)
    pools = {
        "vendedores": d["vendedores"],
        "fornecedores": d["fornecedores"],
        "cidades_estados": [tuple(ce) for ce in d["cidades_estados"]],
        "clientes": [
            {"nome": c["nome"], "inicio": datetime.fromisoformat(c["inicio"]), "peso": c["peso"]}
            for c in d["clientes"]
        ],
    }
    return GeradorEstado(pools, d["contadores"], d["codigos_cliente"], d["saldo_comissao"], pct_sujeira)


def caminho_do_estado(args):
    if args.estado:
        return args.estado
    pasta = os.path.dirname(os.path.abspath(args.saida))
    return os.path.join(pasta, "estado_gerador.json")


def obter_estado(args):
    """Carrega o estado salvo (se existir) ou cria um novo."""
    caminho = caminho_do_estado(args)
    if os.path.exists(caminho):
        print(f"[INFO] Continuando a partir do estado salvo em '{caminho}'.")
        return carregar_estado(caminho, args.pct_sujeira), caminho

    fake = Faker("pt_BR")
    if args.seed is not None:
        Faker.seed(args.seed)
    data_inicio = datetime.strptime(args.data_inicio, "%Y-%m-%d")
    data_fim = datetime.strptime(args.data_fim, "%Y-%m-%d")
    pools = criar_pools_ficticios(
        fake, data_inicio, data_fim,
        n_vendedores=args.vendedores, n_fornecedores=args.fornecedores,
        n_clientes=args.clientes, n_cidades=args.cidades,
    )
    return GeradorEstado(pools, pct_sujeira=args.pct_sujeira), caminho


# --------------------------------------------------------------------------
# 6. GERAÇÃO DE UM PEDIDO
# --------------------------------------------------------------------------


def fator_preco(dt):
    """Preço relativo à data de referência (out/2026): antes dela, mais barato."""
    anos = (dt - REFERENCIA_PRECOS).total_seconds() / (365.25 * 86400)
    return (1 + INFLACAO_ANUAL) ** anos


def sortear_itens(mes, k):
    """Sorteia k produtos distintos, com peso conforme a sazonalidade do mês."""
    indices = list(range(len(CATALOGO_PRODUTOS)))
    pesos = list(PESOS_ITEM_MES[mes])
    escolhidos = []
    for _ in range(k):
        pos = random.choices(range(len(indices)), weights=pesos)[0]
        escolhidos.append(indices.pop(pos))
        pesos.pop(pos)
    return escolhidos


def gerar_pedido(estado, data_pedido):
    """Gera um pedido completo (1 a 3 itens) e devolve uma lista de dicts,
    uma por linha do CSV."""

    s = estado.pct_sujeira
    fp = fator_preco(data_pedido)

    numero_pedido = estado.proximo_pedido
    numero_orcamento = estado.proximo_orcamento
    estado.proximo_pedido += 1
    estado.proximo_orcamento += 1

    cliente = estado.sortear_cliente(data_pedido)
    vendedor = random.choice(estado.pools["vendedores"])
    condicao = random.choice(CONDICOES_PAGAMENTO)

    # Documento do pedido: Nota Fiscal (47%), Cupom Fiscal (23%) ou nenhum (30%)
    documento = random.choices(["nf", "cupom", "nenhum"], weights=[0.47, 0.23, 0.30])[0]
    faturado = documento == "nf"
    com_cupom = documento == "cupom"

    numero_nf = dt_nf_lcto = dt_nf_emis = modelo_nf = None
    numero_cupom = numero_cupom_sat = dt_cupom = dt_cup_sat = venc_cupom = None
    cidade = uf = None

    if faturado:
        numero_nf = estado.proximo_nf
        estado.proximo_nf += 1
        cidade, uf = random.choice(estado.pools["cidades_estados"])
        dt_nf_lcto = data_pedido + timedelta(minutes=random.randint(1, 10))
        dt_nf_emis = dt_nf_lcto + timedelta(minutes=random.randint(5, 40))
        modelo_nf = 55
    elif com_cupom:
        numero_cupom = estado.proximo_cupom
        numero_cupom_sat = numero_cupom + random.randint(0, 3)
        estado.proximo_cupom += 1
        dt_cupom = data_pedido + timedelta(minutes=random.randint(0, 3))
        dt_cup_sat = dt_cupom + timedelta(seconds=random.randint(5, 90))
        if random.random() < 0.08:  # inconsistência: cupom (à vista) com vencimento
            venc_cupom = data_pedido + timedelta(days=random.choice([7, 15, 30]))

    venc_pedido = data_pedido + timedelta(days=random.choice([15, 20, 30, 45, 60]))
    emissao_fin = data_pedido

    n_itens = random.choices([1, 2, 3], weights=[0.72, 0.20, 0.08])[0]
    indices_itens = sortear_itens(data_pedido.month, n_itens)

    linhas = []
    for pos, idx_prod in enumerate(indices_itens, start=1):
        produto, grupo, unidade, preco_min, preco_max, marca = CATALOGO_PRODUTOS[idx_prod]
        id_produto = 1000 + idx_prod * 13   # estável entre execuções

        vr_unit = round(random.uniform(preco_min, preco_max) * fp, 2)

        if unidade in ("KG", "SC"):
            qnt = random.choice([25, 30, 50, 100, 200, 500, 1000, 3000])
        elif unidade == "MIL":
            qnt = random.choice([1, 2, 5, 10])
        elif unidade == "LT":
            qnt = random.choice([1, 2, 5, 10, 20])
        else:
            qnt = random.choice([1, 2, 5, 8, 16, 25, 30])

        total_liquido = round(qnt * vr_unit, 2)
        tot_desc = round(total_liquido * random.choice([0, 0, 0, 0.02, 0.05]), 2)
        total_bruto = round(total_liquido + tot_desc, 2)

        if unidade in ("KG", "SC"):
            peso_br_un = 1.0
            peso_liq_un = round(peso_br_un * random.uniform(0.96, 1.0), 3)
        elif unidade == "LT":
            peso_br_un = round(random.uniform(1.0, 1.1), 3)
            peso_liq_un = round(peso_br_un * 0.98, 3)
        elif unidade == "MIL":
            peso_br_un = round(random.uniform(0.001, 0.01), 4)
            peso_liq_un = peso_br_un
        else:
            peso_br_un = round(random.uniform(0.05, 2.0), 3)
            peso_liq_un = round(peso_br_un * random.uniform(0.95, 1.0), 3)

        tot_kg_bruto = round(qnt * peso_br_un, 3)
        tot_kg_liq = round(qnt * peso_liq_un, 3)

        preco_compra = None
        if grupo != "SERVIÇO":
            preco_compra = round(vr_unit * random.uniform(0.55, 0.85), 2)

        tipo_venda = TIPO_VENDA_POR_GRUPO.get(grupo, "PRODUTOS" if marca == "INDEFINIDA" else "REPRESENTAÇÃO")
        fornecedor = random.choice(estado.pools["fornecedores"]) if grupo != "SERVIÇO" else None

        subgrupo = None
        opcoes = SUBGRUPOS_POR_GRUPO.get(grupo)
        if opcoes and random.random() < 0.85:
            subgrupo = random.choice(opcoes)

        vr_total_nf = total_liquido if faturado else 0

        if numero_nf is not None:
            titulo = f"{numero_nf:06d}-{pos}/{n_itens}"
        elif numero_cupom is not None:
            titulo = f"CUP{numero_cupom:05d}-{pos}/{n_itens}"
        else:
            titulo = f"00{numero_pedido}-{pos}/{n_itens}"

        cod_cliente = estado.codigo_cliente(cliente)
        comissao = estado.acumular_comissao(vendedor, data_pedido, total_liquido)

        linhas.append({
            "Nº Ped.": numero_pedido,
            "Nº Orc.": numero_orcamento,
            "Dt.Ped.": _fmt_data(data_pedido, s),
            "Cliente": _variar_caixa(cliente, s),
            "Produto": produto,
            "IdProduto": id_produto,
            "Qnt.": qnt,
            "Total Líquido": total_liquido,
            "Vendedor": _variar_caixa(vendedor, s),
            "Vr.Unit.": vr_unit,
            "Grupo": grupo,
            "Marca": marca,
            "Fornecedor": _variar_caixa(fornecedor, s) if fornecedor else None,
            "Tot.Kg Bruto": tot_kg_bruto,
            "Total Bruto": total_bruto,
            "Peso Br. Un.": peso_br_un,
            "Dt.Cup.Sat.": _fmt_data(dt_cup_sat, s),
            "Dt.NF Lcto.": _fmt_data(dt_nf_lcto, s),
            "N° NF.": numero_nf,
            "Dt.Cupom": _fmt_data(dt_cupom, s),
            "Cód. NF.": numero_nf,
            "Dt.NF.Emis.": _fmt_data(dt_nf_emis, s),
            "Nº Cup.": numero_cupom,
            "Nº Cup.Sat.": numero_cupom_sat,
            "Peso Líq. Un.": peso_liq_un,
            "Tot.Desc.": tot_desc,
            "Cód.Cliente": cod_cliente,
            "Vr.Comiss.": comissao,
            "Un.": unidade,
            "Condição": condicao,
            "Tot.Kg Líq.": tot_kg_liq,
            "SubGrupo": subgrupo,
            "Venc. Pedido": _fmt_data_br(venc_pedido, s),
            "Emissão Fin.": _fmt_data_br(emissao_fin, s),
            "Vr.Total NF.": vr_total_nf,
            "Venc. Cupom": _fmt_data_br(venc_cupom, s) if venc_cupom else None,
            "Venc. Nota": _fmt_data_br(venc_pedido, s) if faturado else None,
            "Título": titulo,
            "Cidade": _variar_caixa(cidade, s) if cidade else None,
            "Estado": uf,
            "Tipo Venda": tipo_venda,
            "Preço Compra.": preco_compra,
            "Modelo NF": modelo_nf,
        })

    return linhas


# --------------------------------------------------------------------------
# 7. ESCRITA EM CSV
# --------------------------------------------------------------------------


def _precisa_cabecalho(caminho):
    return not os.path.exists(caminho) or os.path.getsize(caminho) == 0


def escrever_linhas_csv(caminho, linhas):
    os.makedirs(os.path.dirname(os.path.abspath(caminho)) or ".", exist_ok=True)
    cabecalho = _precisa_cabecalho(caminho)
    with open(caminho, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";")
        if cabecalho:
            writer.writeheader()
        writer.writerows(linhas)


# --------------------------------------------------------------------------
# 8. MODO LOTE (histórico)
# --------------------------------------------------------------------------


def montar_calendario(inicio, fim):
    """Lista de dias e o 'peso' de cada um (tendência × mês × dia da semana)."""
    dias, pesos = [], []
    d = inicio
    while d <= fim:
        anos = (d - inicio).days / 365.25
        peso = ((1 + CRESCIMENTO_ANUAL) ** anos) * SAZ_VOLUME_MES[d.month - 1] * FATOR_DIA_SEMANA[d.weekday()]
        dias.append(d)
        pesos.append(peso)
        d += timedelta(days=1)
    return dias, pesos


def sortear_horario(dia):
    """Horário comercial: seg-sex 7h-17h, sábado 7h-11h."""
    hora_max = 11 if dia.weekday() == 5 else 17
    return dia + timedelta(hours=random.randint(7, hora_max),
                           minutes=random.randint(0, 59),
                           seconds=random.randint(0, 59))


def rodar_lote(args):
    if args.seed is not None:
        random.seed(args.seed)

    caminho_estado = caminho_do_estado(args)
    if args.sobrescrever:
        for caminho in (args.saida, caminho_estado):
            if os.path.exists(caminho):
                os.remove(caminho)

    estado, caminho_estado = obter_estado(args)

    data_inicio = datetime.strptime(args.data_inicio, "%Y-%m-%d")
    data_fim = datetime.strptime(args.data_fim, "%Y-%m-%d")
    if data_fim < data_inicio:
        sys.exit("[ERRO] --data-fim anterior a --data-inicio.")

    dias, pesos = montar_calendario(data_inicio, data_fim)
    dias_sorteados = random.choices(dias, weights=pesos, k=args.pedidos)
    # Ordena ANTES de gerar: assim a numeração cresce junto com a data
    datas = sorted(sortear_horario(d) for d in dias_sorteados)

    os.makedirs(os.path.dirname(os.path.abspath(args.saida)) or ".", exist_ok=True)
    cabecalho = _precisa_cabecalho(args.saida)
    total_linhas = 0
    with open(args.saida, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";")
        if cabecalho:
            writer.writeheader()
        for i, dt in enumerate(datas, start=1):
            linhas = gerar_pedido(estado, dt)
            writer.writerows(linhas)
            total_linhas += len(linhas)
            if i % 20000 == 0:
                print(f"[...] {i}/{args.pedidos} pedidos gerados")

    salvar_estado(estado, caminho_estado)
    print(f"[OK] {total_linhas} linhas ({args.pedidos} pedidos) de {args.data_inicio} a "
          f"{args.data_fim} gravadas em '{args.saida}'.")
    print(f"[OK] Estado salvo em '{caminho_estado}' (o modo contínuo continua daqui).")


# --------------------------------------------------------------------------
# 9. MODO CONTÍNUO (streaming)
# --------------------------------------------------------------------------


def rodar_continuo(args):
    if args.seed is not None:
        random.seed(args.seed)

    estado, caminho_estado = obter_estado(args)

    limite_txt = f"{args.limite} pedidos" if args.limite else "até Ctrl+C"
    print(f"[INFO] Modo contínuo: um pedido a cada {args.intervalo_min}s a {args.intervalo_max}s "
          f"({limite_txt}). Saída: '{args.saida}'.")

    gerados = 0
    try:
        while not args.limite or gerados < args.limite:
            agora = datetime.now()
            linhas = gerar_pedido(estado, agora)
            escrever_linhas_csv(args.saida, linhas)
            gerados += 1
            print(f"[{agora:%H:%M:%S}] pedido {linhas[0]['Nº Ped.']}: +{len(linhas)} linha(s) -> {args.saida}")
            if gerados % 5 == 0:
                salvar_estado(estado, caminho_estado)
            if args.limite and gerados >= args.limite:
                break
            time.sleep(random.uniform(args.intervalo_min, args.intervalo_max))
    except KeyboardInterrupt:
        print("\n[INFO] Encerrado pelo usuário.")
    finally:
        salvar_estado(estado, caminho_estado)


# --------------------------------------------------------------------------
# 10. CLI
# --------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Gerador de dados sintéticos de vendas (estrutura do relatório real da FCA)."
    )
    parser.add_argument("--saida", default="dados/vendas.csv", help="Caminho do CSV de saída.")
    parser.add_argument("--estado", default=None,
                         help="Arquivo JSON de estado (padrão: estado_gerador.json na pasta do CSV).")
    parser.add_argument("--seed", type=int, default=None, help="Semente aleatória (resultados reprodutíveis).")

    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--pedidos", type=int, default=PEDIDOS_PADRAO,
                       help=f"Nº de pedidos no modo lote (padrão: {PEDIDOS_PADRAO}).")
    modo.add_argument("--continuo", action="store_true", help="Ativa o modo contínuo (streaming).")

    parser.add_argument("--data-inicio", default=INICIO_PADRAO, help="Início do histórico (AAAA-MM-DD).")
    parser.add_argument("--data-fim", default=FIM_PADRAO, help="Fim do histórico (AAAA-MM-DD).")
    parser.add_argument("--sobrescrever", action="store_true",
                         help="Lote: apaga CSV e estado anteriores e recomeça do zero.")

    parser.add_argument("--intervalo-min", type=float, default=2.0,
                         help="Contínuo: tempo mínimo (s) entre pedidos.")
    parser.add_argument("--intervalo-max", type=float, default=20.0,
                         help="Contínuo: tempo máximo (s) entre pedidos.")
    parser.add_argument("--limite", type=int, default=0,
                         help="Contínuo: para após N pedidos (0 = roda até Ctrl+C).")

    parser.add_argument("--vendedores", type=int, default=4, help="Nº de vendedores (padrão: 4).")
    parser.add_argument("--fornecedores", type=int, default=5, help="Nº de fornecedores.")
    parser.add_argument("--clientes", type=int, default=400, help="Nº de clientes no histórico.")
    parser.add_argument("--cidades", type=int, default=25, help="Nº de cidades.")
    parser.add_argument("--pct-sujeira", type=float, default=PCT_SUJEIRA_PADRAO,
                         help="Proporção (0 a 1) de datas/textos fora do padrão (padrão: 0.15).")

    args = parser.parse_args()

    if args.continuo:
        rodar_continuo(args)
    else:
        rodar_lote(args)


if __name__ == "__main__":
    main()
