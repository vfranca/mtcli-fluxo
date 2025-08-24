import click
import MetaTrader5 as mt5
import pandas as pd
from .conecta import conectar, shutdown
from mtcli.logger import setup_logger


logger = setup_logger("fluxo")


@click.command()
@click.option(
    "--symbol", "-s", default="WIN$N", help="Símbolo do ativo (default WIN$N)."
)
@click.option("--dias", "-d", default=1, help="Dias de dados (default 1).")
@click.option("--periodo", "-p", default=1, help="Período em minutos (default 1).")
@click.option(
    "--neutro",
    "-n",
    default=0.01,
    help='Valor mínimo absoluto do saldo para ser considerado não neutro. Abaixo disso será classificado como "Neutra" (default 0.01).',
)
@click.option("--salvar", is_flag=True, help="Salvar em CSV.")
def agressao(symbol, dias, periodo, neutro, salvar):
    """Calcula o saldo estimado da agressao para o ativo symbol."""
    conectar()
    logger.info(
        f"Iniciando cálculo da agressão para o{symbol} dias {dias} período {periodo}."
    )

    ticks = mt5.copy_ticks_from(
        symbol,
        pd.Timestamp.now() - pd.Timedelta(days=dias),
        1000000,
        mt5.COPY_TICKS_ALL,
    )
    df = pd.DataFrame(ticks)
    if df.empty:
        click.echo(f"Sem dados de tick para {symbol}.")
        logger.info(f"Sem dados de tick para o ativo {symbol}.")
        return

    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)

    if "type" in df.columns:
        df["sentido"] = df["type"].apply(lambda x: 1 if x == 1 else -1)
    else:
        df["prev_bid"] = df["bid"].shift(1)
        df["sentido"] = (df["bid"] > df["prev_bid"]).astype(int) - (
            df["bid"] < df["prev_bid"]
        ).astype(int)

    df["agressao"] = df["volume"] * df["bid"] * df["sentido"]
    saldo = df["agressao"].resample(f"{periodo}min").sum().rename("saldo")

    resultado = saldo.to_frame()
    resultado["direcao"] = resultado["saldo"].apply(
        lambda x: (
            "Neutra" if abs(x) < neutro else ("Compradora" if x > 0 else "Vendedora")
        )
    )

    click.echo(f"\nTop 5 saldos agressivos ({periodo}min):")
    click.echo(resultado.sort_values(by="saldo", ascending=False).head(5))

    if salvar:
        df.to_csv(f"{symbol}_agressao_ticks.csv")
        resultado.to_csv(f"{ativo}agressao_saldo{periodo}min.csv")
        click.echo("Dados salvos.")

    shutdown()


if __name__ == "__main__":
    agressao()
