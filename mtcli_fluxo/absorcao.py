import click
import MetaTrader5 as mt5
import pandas as pd
from mtcli.conecta import conectar, shutdown
from mtcli.logger import setup_logger


logger = setup_logger("fluxo")


@click.command()
@click.option(
    "--symbol", "-s", default="WIN$N", help="Símbolo do ativo (default WIN$N)."
)
@click.option("--dias", default=1, help="Dias de candles.")
@click.option(
    "--neutro",
    default=10,
    help="Variação mínima de candle em pontos para não ser classificado como Neutro.",
)
@click.option("--salvar", is_flag=True, help="Salvar em CSV.")
def absorcao(symbol, dias, neutro, salvar):
    """Calcula saldo estimado da absorcao do ativo symbol."""
    conectar()

    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, dias * 24 * 60)
    df = pd.DataFrame(rates)
    if df.empty:
        logger.info(f"Sem dados de candle para {symbol}.")
        click.echo(f"Sem dados de candle para {symbol}.")
        return

    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    df["range"] = df["high"] - df["low"]
    df["media_range"] = df["range"].rolling(10).mean()
    df["volume_ma"] = df["volume"].rolling(10).mean()

    limite_volume = df["volume"].quantile(0.8)
    df["absorvido"] = (df["volume"] > limite_volume) & (df["range"] < df["media_range"])

    df["variacao"] = df["close"] - df["open"]
    df["direcao"] = df["variacao"].apply(
        lambda x: "Neutra" if abs(x) < neutro else ("Alta" if x > 0 else "Baixa")
    )

    absorcoes = df[df["absorvido"]]
    click.echo("\nCandles com possível absorção:")
    click.echo(absorcoes[["open", "high", "low", "close", "volume", "direcao"]].tail(5))

    if salvar:
        df.to_csv(f"{symbol}_absorcoes.csv")
        click.echo("Arquivo salvo.")

    shutdown()


if __name__ == "__main__":
    absorcao()
