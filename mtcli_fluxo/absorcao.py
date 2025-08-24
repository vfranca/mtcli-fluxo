import click
import MetaTrader5 as mt5
import pandas as pd
from .conecta import conectar, shutdown


@click.command()
@click.option('--ativo', default='WINQ25', help='Símbolo do ativo.')
@click.option('--dias', default=1, help='Dias de candles.')
@click.option('--neutro', default=10, help='Variação mínima de candle em pontos para não ser classificado como Neutro.')
@click.option('--salvar', is_flag=True, help='Salvar em CSV.')
def absorcao(ativo, dias, neutro, salvar):
    conectar()

    rates = mt5.copy_rates_from_pos(ativo, mt5.TIMEFRAME_M1, 0, dias * 24 * 60)
    df = pd.DataFrame(rates)
    if df.empty:
        click.echo("Sem dados de candle.")
        return

    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    df['range'] = df['high'] - df['low']
    df['media_range'] = df['range'].rolling(10).mean()
    df['volume_ma'] = df['volume'].rolling(10).mean()

    limite_volume = df['volume'].quantile(0.8)
    df['absorvido'] = (df['volume'] > limite_volume) & (df['range'] < df['media_range'])

    df['variacao'] = df['close'] - df['open']
    df['direcao'] = df['variacao'].apply(
        lambda x: 'Neutra' if abs(x) < neutro else ('Alta' if x > 0 else 'Baixa')
    )

    absorcoes = df[df['absorvido']]
    click.echo("\nCandles com possível absorção:")
    click.echo(absorcoes[['open', 'high', 'low', 'close', 'volume', 'direcao']].tail(5))

    if salvar:
        df.to_csv(f'{ativo}_absorcoes.csv')
        click.echo("Arquivo salvo.")

    shutdown()


if __name__ == '__main__':
    absorcao()
