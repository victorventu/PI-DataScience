#!/usr/bin/env python3
"""
gerador_vendas.py
------------------
Gera dados SINTÉTICOS de vendas com a mesma estrutura (mesmas 43 colunas)
do relatório real da empresa parceira do Projeto Integrador (FCA).

Nenhum dado real da empresa é usado. Nomes de clientes, fornecedores,
vendedores e cidades são gerados por algoritmo (biblioteca Faker, com
dados fictícios em português) — não são digitados/copiados de lugar
nenhum, então não têm nenhum vínculo com dados reais ou sensíveis.
Apenas o "formato" (colunas, tipos, faixas de valores, proporção de
campos vazios etc.) foi inspirado no relatório real.

Modos de uso:
    1) Lote (batch): gera um CSV com N pedidos de uma vez.
    2) Contínuo: fica rodando e vai gerando novos pedidos em intervalos
       ESPORÁDICOS (tempo aleatório entre um pedido e outro), simulando
       um sistema de vendas "ao vivo" — útil para a aula de DevOps, para
       testar pipelines que leem dados incrementais.

Dependência externa: Faker (`pip install faker`).

Exemplos:
    python3 gerador_vendas.py --pedidos 500 --saida dados/vendas.csv
    python3 gerador_vendas.py --continuo --intervalo-min 2 --intervalo-max 20 --saida dados/vendas.csv
"""

import argparse
import csv
import os
import random
import sys
import time
from datetime import datetime, timedelta
import pandas as pd

from faker import Faker

# --------------------------------------------------------------------------
# 1. DADOS FICTÍCIOS GERADOS POR ALGORITMO (Faker) — nada digitado à mão
# --------------------------------------------------------------------------
# Clientes, fornecedores, vendedores e cidades NÃO são listas fixas: são
# sorteados por uma biblioteca de geração de dados falsos (Faker, locale
# pt_BR) toda vez que o script roda. Isso garante que não existe nenhuma
# coincidência com nome real de pessoa, empresa ou endereço.

SUFIXOS_EMPRESA = ["LTDA", "ME", "EIRELI", "S.A.", "COMÉRCIO E REPRESENTAÇÕES"]
PREFIXOS_PROPRIEDADE_RURAL = ["FAZENDA", "SÍTIO", "CHÁCARA", "AGROPECUÁRIA"]


def criar_pools_ficticios(fake: Faker, n_vendedores=8, n_fornecedores=5, n_clientes=180, n_cidades=25):
    """Gera, uma única vez por execução, os 'bancos' de nomes fictícios que
    serão sorteados linha a linha. Usar um pool fixo (em vez de gerar um
    nome novo a cada linha) simula melhor a realidade: o mesmo cliente e o
    mesmo vendedor aparecem repetidas vezes ao longo do tempo."""

    vendedores = [fake.name() for _ in range(n_vendedores)]

    fornecedores = [
        f"{fake.company().upper()} {random.choice(SUFIXOS_EMPRESA)}" for _ in range(n_fornecedores)
    ]
    fornecedores.append(None)  # ~30% dos pedidos reais não têm fornecedor preenchido

    clientes = []
    for _ in range(n_clientes):
        if random.random() < 0.45:
            nome = f"{random.choice(PREFIXOS_PROPRIEDADE_RURAL)} {fake.last_name().upper()}"
        else:
            nome = fake.name().upper()
            if random.random() < 0.25:
                nome += " E OUTRO" if random.random() < 0.5 else " E OUTROS"
        clientes.append(nome)

    cidades_estados = [(fake.city().upper(), fake.estado_sigla()) for _ in range(n_cidades)]

    return {
        "vendedores": vendedores,
        "fornecedores": fornecedores,
        "clientes": clientes,
        "cidades_estados": cidades_estados,
    }


CONDICOES_PAGAMENTO = [
    "1-A VISTA", "2-30 DIAS", "27-40 DIAS", "29-50 DIAS", "63-28 DIAS",
    "66-7 DIAS", "77-300/400/500 DIAS", "81-100/200 DIAS", "83-200", "84-120 DIAS",
]

# Catálogo de produtos fictícios: (nome, grupo, unidade, preco_min, preco_max, marca)
CATALOGO_PRODUTOS = [
    ("NUTRIBOI MAX 0,3 (SC 25KG)",          "NUTRIÇÃO",         "SC", 2.20, 3.10, "REPRESENTAÇÃO"),
    ("FOSFANIM 40P - 30KG",                 "NUTRIÇÃO",         "KG", 3.00, 4.20, "INDEFINIDA"),
    ("SUPLEMENTO NOVILHA M (SC 30KG)",      "NUTRIÇÃO",         "SC", 5.00, 6.80, "REPRESENTAÇÃO"),
    ("RACAO MATERNA PREMIUM 25KG",          "NUTRIÇÃO",         "KG", 12.50, 16.90, "INDEFINIDA"),
    ("SAL MINERAL EQUILIBRIO 25KG",         "NUTRIÇÃO",         "KG", 4.50, 5.90, "INDEFINIDA"),
    ("PLACA IDENTIFICACAO ANIMAL",          "GERAL",            "UN", 30.00, 40.00, "INDEFINIDA"),
    ("KIT COLETA DE LEITE",                 "QUALIDADE DE LEITE", "UN", 25.00, 45.00, "INDEFINIDA"),
    ("REAGENTE ANALISE DE LEITE 1L",        "QUALIDADE DE LEITE", "LT", 60.00, 90.00, "INDEFINIDA"),
    ("DESINFETANTE INDUSTRIAL 5L",          "QUIMICOS",         "PC", 35.00, 55.00, "INDEFINIDA"),
    ("DETERGENTE ACIDO CIP 20L",            "QUIMICOS",         "PC", 80.00, 120.00, "INDEFINIDA"),
    ("SERVICO DE CONSULTORIA A CAMPO",      "SERVIÇO",          "UN", 90.00, 300.00, "INDEFINIDA"),
    ("SERVICO DE FRETE / TRANSPORTE",       "SERVIÇO",          "UN", 50.00, 250.00, "INDEFINIDA"),
    ("LUVA DESCARTAVEL (CX 100 UN)",        "USO E CONSUMO",    "PC", 18.00, 28.00, "INDEFINIDA"),
    ("SERINGA DESCARTAVEL 20ML (MIL)",      "USO E CONSUMO",    "MIL", 90.00, 140.00, "INDEFINIDA"),
    ("VERMIFUGO BOVINO INJETAVEL 500ML",    "GERAL",            "UN", 40.00, 65.00, "REPRESENTAÇÃO"),
    ("MINERALIZADOR KM SACO 30KG",          "KM",               "KG", 3.50, 4.80, "INDEFINIDA"),
]

TIPO_VENDA_POR_GRUPO = {
    "SERVIÇO": "SERVIÇOS",
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
# 3. LÓGICA DE GERAÇÃO
# --------------------------------------------------------------------------


class GeradorEstado:
    """Guarda contadores que precisam ser sequenciais/crescentes entre chamadas
    (números de pedido, orçamento, nota fiscal, código de cliente etc.)."""

    def __init__(self, pools, semente_pedido=14600, semente_orcamento=12701, semente_nf=6997):
        self.pools = pools
        self.proximo_pedido = semente_pedido
        self.proximo_orcamento = semente_orcamento
        self.proximo_nf = semente_nf
        self.codigos_cliente = {}
        self.saldo_comissao_vendedor = {v: random.uniform(50, 2000) for v in pools["vendedores"]}

    def codigo_cliente(self, cliente):
        if cliente not in self.codigos_cliente:
            self.codigos_cliente[cliente] = random.randint(100, 5000)
        return self.codigos_cliente[cliente]


def _fmt_data(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _fmt_data_br(dt):
    return dt.strftime("%d/%m/%y")


def gerar_pedido(estado: GeradorEstado, data_pedido: datetime):
    """Gera um pedido completo (1 a 3 itens/linhas) e devolve uma lista de dicts,
    uma por linha, já no formato final das colunas do CSV."""

    numero_pedido = estado.proximo_pedido
    numero_orcamento = estado.proximo_orcamento
    estado.proximo_pedido += 1
    estado.proximo_orcamento += 1

    cliente = random.choice(estado.pools["clientes"])
    vendedor = random.choice(estado.pools["vendedores"])
    condicao = random.choice(CONDICOES_PAGAMENTO)

    # ~47% dos pedidos já têm nota fiscal emitida (igual à proporção observada
    # no relatório real: campos de NF preenchidos em ~47% das linhas)
    faturado = random.random() < 0.47

    if faturado:
        numero_nf = estado.proximo_nf
        estado.proximo_nf += 1
        cidade, uf = random.choice(estado.pools["cidades_estados"])
        dt_nf_lcto = data_pedido + timedelta(minutes=random.randint(1, 10))
        dt_nf_emis = dt_nf_lcto + timedelta(minutes=random.randint(5, 40))
        modelo_nf = 55.0
    else:
        numero_nf = None
        cidade, uf = None, None
        dt_nf_lcto = None
        dt_nf_emis = None
        modelo_nf = None

    venc_pedido = data_pedido + timedelta(days=random.choice([15, 20, 30, 45, 60]))
    emissao_fin = data_pedido

    n_itens = random.choices([1, 2, 3], weights=[0.72, 0.20, 0.08])[0]
    itens_do_pedido = random.sample(CATALOGO_PRODUTOS, k=n_itens)

    linhas = []
    total_pedido_liquido = 0.0

    for produto, grupo, unidade, preco_min, preco_max, marca in itens_do_pedido:
        id_produto = 500 + abs(hash(produto)) % 1500

        vr_unit = round(random.uniform(preco_min, preco_max), 2)

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

        pesa_por_kg = 1 if unidade in ("KG", "SC") else 0
        tot_kg_bruto = qnt if pesa_por_kg else 0
        tot_kg_liq = tot_kg_bruto

        preco_compra = None
        if grupo != "SERVIÇO":
            preco_compra = round(vr_unit * random.uniform(0.55, 0.85), 2)

        tipo_venda = TIPO_VENDA_POR_GRUPO.get(grupo, "PRODUTOS" if marca == "INDEFINIDA" else "REPRESENTAÇÃO")

        fornecedor = random.choice(estado.pools["fornecedores"]) if grupo != "SERVIÇO" else None

        vr_total_nf = total_liquido if faturado else 0

        if numero_nf is not None:
            titulo = f"{numero_nf:06d}-1/{n_itens}"
        else:
            titulo = f"00{numero_pedido}-1/1"

        cod_cliente = estado.codigo_cliente(cliente)
        estado.saldo_comissao_vendedor[vendedor] += total_liquido * 0.03

        linha = {
            "Nº Ped.": numero_pedido,
            "Nº Orc.": numero_orcamento,
            "Dt.Ped.": _fmt_data(data_pedido),
            "Cliente": cliente,
            "Produto": produto,
            "IdProduto": id_produto,
            "Qnt.": qnt,
            "Total Líquido": total_liquido,
            "Vendedor": vendedor,
            "Vr.Unit.": vr_unit,
            "Grupo": grupo,
            "Marca": marca,
            "Fornecedor": fornecedor,
            "Tot.Kg Bruto": tot_kg_bruto,
            "Total Bruto": total_bruto,
            "Peso Br. Un.": pesa_por_kg,
            "Dt.Cup.Sat.": None,
            "Dt.NF Lcto.": _fmt_data(dt_nf_lcto) if dt_nf_lcto else None,
            "N° NF.": numero_nf,
            "Dt.Cupom": None,
            "Cód. NF.": numero_nf,
            "Dt.NF.Emis.": _fmt_data(dt_nf_emis) if dt_nf_emis else None,
            "Nº Cup.": None,
            "Nº Cup.Sat.": None,
            "Peso Líq. Un.": pesa_por_kg,
            "Tot.Desc.": tot_desc,
            "Cód.Cliente": cod_cliente,
            "Vr.Comiss.": round(estado.saldo_comissao_vendedor[vendedor], 2),
            "Un.": unidade,
            "Condição": condicao,
            "Tot.Kg Líq.": tot_kg_liq,
            "SubGrupo": None,
            "Venc. Pedido": _fmt_data_br(venc_pedido),
            "Emissão Fin.": _fmt_data_br(emissao_fin),
            "Vr.Total NF.": vr_total_nf,
            "Venc. Cupom": None,
            "Venc. Nota": _fmt_data_br(venc_pedido) if faturado else None,
            "Título": titulo,
            "Cidade": cidade,
            "Estado": uf,
            "Tipo Venda": tipo_venda,
            "Preço Compra.": preco_compra,
            "Modelo NF": modelo_nf,
        }
        linhas.append(linha)
        total_pedido_liquido += total_liquido

    return linhas


# --------------------------------------------------------------------------
# 4. ESCRITA EM CSV
# --------------------------------------------------------------------------


def escrever_linhas_csv(caminho, linhas, escrever_cabecalho):
    os.makedirs(os.path.dirname(os.path.abspath(caminho)) or ".", exist_ok=True)
    modo = "a" if os.path.exists(caminho) and not escrever_cabecalho else "w"
    with open(caminho, modo, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";")
        if escrever_cabecalho:
            writer.writeheader()
        writer.writerows(linhas)


# --------------------------------------------------------------------------
# 5. MODOS DE EXECUÇÃO
# --------------------------------------------------------------------------


def rodar_lote(args):
    random.seed(args.seed)
    fake = Faker("pt_BR")
    Faker.seed(args.seed)
    estado = GeradorEstado(criar_pools_ficticios(fake))

    data_inicio = datetime.strptime(args.data_inicio, "%Y-%m-%d")
    data_fim = datetime.strptime(args.data_fim, "%Y-%m-%d")
    intervalo_dias = max((data_fim - data_inicio).days, 1)

    ja_existe = os.path.exists(args.saida)
    todas_as_linhas = []

    for i in range(args.pedidos):
        dt = data_inicio + timedelta(
            days=random.randint(0, intervalo_dias),
            hours=random.randint(7, 18),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        todas_as_linhas.extend(gerar_pedido(estado, dt))

    todas_as_linhas.sort(key=lambda l: l["Dt.Ped."])
    escrever_linhas_csv(args.saida, todas_as_linhas, escrever_cabecalho=not ja_existe)

    print(f"[OK] {len(todas_as_linhas)} linhas ({args.pedidos} pedidos) gravadas em '{args.saida}'.")


def rodar_continuo(args):
    random.seed(args.seed)
    fake = Faker("pt_BR")
    Faker.seed(args.seed)
    estado = GeradorEstado(criar_pools_ficticios(fake))
    ja_existe = os.path.exists(args.saida)
    escreveu_cabecalho = ja_existe

    print(
        f"[INFO] Modo contínuo (esporádico): pedidos chegam em intervalos "
        f"aleatórios entre {args.intervalo_min}s e {args.intervalo_max}s. Ctrl+C para parar."
    )
    try:
        while True:
            agora = datetime.now()
            linhas = gerar_pedido(estado, agora)
            escrever_linhas_csv(args.saida, linhas, escrever_cabecalho=not escreveu_cabecalho)
            escreveu_cabecalho = True
            print(f"[{agora:%H:%M:%S}] +{len(linhas)} linha(s) -> {args.saida}")

            espera = random.uniform(args.intervalo_min, args.intervalo_max)
            time.sleep(espera)
    except KeyboardInterrupt:
        print("\n[INFO] Encerrado pelo usuário.")
        sys.exit(0)


# --------------------------------------------------------------------------
# 6. CLI
# --------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Gerador de dados sintéticos de vendas (estrutura do relatório real da FCA)."
    )
    parser.add_argument("--saida", default="dados/vendas.csv", help="Caminho do arquivo CSV de saída.")
    parser.add_argument("--seed", type=int, default=None, help="Semente aleatória (para resultados reprodutíveis).")

    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--pedidos", type=int, default=200, help="Nº de pedidos a gerar no modo lote (padrão: 200).")
    modo.add_argument("--continuo", action="store_true", help="Ativa o modo contínuo (gera pedidos periodicamente).")

    parser.add_argument("--intervalo-min", type=float, default=2.0,
                         help="Tempo mínimo (segundos) entre pedidos no modo contínuo.")
    parser.add_argument("--intervalo-max", type=float, default=20.0,
                         help="Tempo máximo (segundos) entre pedidos no modo contínuo.")
    parser.add_argument("--data-inicio", default="2026-01-01", help="Início do período (modo lote), AAAA-MM-DD.")
    parser.add_argument("--data-fim", default="2026-09-01", help="Fim do período (modo lote), AAAA-MM-DD.")

    args = parser.parse_args()

    if args.continuo:
        rodar_continuo(args)
    else:
        rodar_lote(args)


if __name__ == "__main__":
    main()
