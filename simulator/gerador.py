import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


random.seed(42)


VACINAS = {
    "Febre Aftosa": 180,
    "Brucelose": 365,
    "Clostridiose": 180,
    "Raiva": 365,
    "IBR e BVD": 180
}

RACAS = [
    "Nelore",
    "Angus",
    "Girolando",
    "Holandês",
    "Guzerá",
    "Brahman"
]

SEXOS = [
    "Macho",
    "Fêmea"
]

QUANTIDADE_REGISTROS = 10000


def gerar_dados(quantidade):
    data_atual = datetime.now()
    dados = []

    for i in range(1, quantidade + 1):

        animal_id = f"AN{i:06d}"
        brinco = f"BR{i:06d}"

        raca = random.choice(RACAS)
        sexo = random.choice(SEXOS)

        dias_nascimento = random.randint(365, 3650)
        data_nascimento = data_atual - timedelta(days=dias_nascimento)

        vacina = random.choice(list(VACINAS.keys()))
        intervalo = VACINAS[vacina]

        lote_vacina = f"LOT-{random.randint(10000, 99999)}"

        dias_desde_vacinacao = random.randint(30, 400)
        ultima_vacinacao = data_atual - timedelta(
            days=dias_desde_vacinacao
        )

        proxima_vacinacao = ultima_vacinacao + timedelta(
            days=intervalo
        )

        validade_vacina = data_atual + timedelta(
            days=random.randint(-60, 730)
        )

        estoque_minimo = random.randint(20, 100)
        estoque_atual = random.randint(0, 200)

        dias_para_vacina = (
            proxima_vacinacao - data_atual
        ).days

        if dias_para_vacina < 0:
            status_vacinacao = "Atrasada"
        elif dias_para_vacina <= 30:
            status_vacinacao = "Próxima"
        else:
            status_vacinacao = "Em dia"

        if estoque_atual <= estoque_minimo:
            status_estoque = "Estoque baixo"
        else:
            status_estoque = "Normal"

        dados.append({
            "animal_id": animal_id,
            "brinco": brinco,
            "raca": raca,
            "sexo": sexo,
            "data_nascimento": data_nascimento.strftime("%Y-%m-%d"),
            "vacina": vacina,
            "lote_vacina": lote_vacina,
            "validade_vacina": validade_vacina.strftime("%Y-%m-%d"),
            "ultima_vacinacao": ultima_vacinacao.strftime("%Y-%m-%d"),
            "proxima_vacinacao": proxima_vacinacao.strftime("%Y-%m-%d"),
            "estoque_atual": estoque_atual,
            "estoque_minimo": estoque_minimo,
            "status_vacinacao": status_vacinacao,
            "status_estoque": status_estoque
        })

    return pd.DataFrame(dados)


def main():
    parser = argparse.ArgumentParser(
        description="Gerador de dados do projeto de Agronegócio"
    )

    parser.add_argument(
        "--output",
        default="dados",
        help="Diretório onde o CSV será salvo"
    )

    parser.add_argument(
        "--quantidade",
        type=int,
        default=QUANTIDADE_REGISTROS,
        help="Quantidade de registros a serem gerados"
    )

    args = parser.parse_args()

    pasta_saida = Path(args.output)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    arquivo_saida = (
        pasta_saida / "dados_foco.csv"
    )

    df = gerar_dados(args.quantidade)

    df.to_csv(
        arquivo_saida,
        index=False,
        encoding="utf-8-sig"
    )

    print("=" * 60)
    print("GERADOR DE DADOS - AGRONEGÓCIO")
    print("=" * 60)
    print(f"Registros gerados: {len(df)}")
    print(f"Arquivo criado: {arquivo_saida}")

    print("\nDistribuição das vacinas:")
    print(df["vacina"].value_counts())

    print("\nStatus das vacinações:")
    print(df["status_vacinacao"].value_counts())

    print("\nStatus dos estoques:")
    print(df["status_estoque"].value_counts())

    print("\nPrimeiros registros:")
    print(df.head())

    print("\nGerador executado com sucesso!")


if __name__ == "_main_":
    main()