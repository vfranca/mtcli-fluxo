import click
import MetaTrader5 as mt5
import pandas as pd
from .conecta import conectar, shutdown


@click.command()
@click.option('--ativo', default='WINQ25', help='Símbolo do ativo.')
@click.option('--dias', default=1, help='Dias de dados.')
@click.option('--periodo', default=1, help='Período em minutos.')
@click.option('--neutro', default=0.01, help='Valor mínimo absoluto do saldo para ser considerado não neutro. Abaixo disso será classificado como "Neutra".')
@click.option('--salvar', is_flag=True, help='Salvar em CSV.')
def agressao(ativo, dias, periodo, neutro, salvar):
    conectar()

    ticks = mt5.copy_ticks_from(ativo, pd.Timestamp.now() - pd.Timedelta(days=dias), 1000000, mt5.COPY_TICKS_ALL)
    df = pd.DataFrame(ticks)
    if df.empty:
        click.echo("Sem dados de tick.")
        return

    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    if 'type' in df.columns:
        df['sentido'] = df['type'].apply(lambda x: 1 if x == 1 else -1)
    else:
        df['prev_bid'] = df['bid'].shift(1)
        df['sentido'] = (df['bid'] > df['prev_bid']).astype(int) - (df['bid'] < df['prev_bid']).astype(int)

    df['agressao'] = df['volume'] * df['bid'] * df['sentido']
    saldo = df['agressao'].resample(f'{periodo}min').sum().rename("saldo")

    resultado = saldo.to_frame()
    resultado['direcao'] = resultado['saldo'].apply(
        lambda x: 'Neutra' if abs(x) < neutro else ('Compradora' if x > 0 else 'Vendedora')
    )

    click.echo(f'\nTop 5 saldos agressivos ({periodo}min):')
    click.echo(resultado.sort_values(by='saldo', ascending=False).head(5))

    if salvar:
        df.to_csv(f'{ativo}_agressao_ticks.csv')
        resultado.to_csv(f'{ativo}agressao_saldo{periodo}min.csv')
        click.echo("Dados salvos.")

    shutdown()


if __name__ == '__main__':
    agressao()
