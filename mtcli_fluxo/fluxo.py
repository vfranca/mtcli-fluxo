import click
import MetaTrader5 as mt5
import pandas as pd
from .agressao import agressao
from .absorcao import absorcao


@click.group()
def fluxo():
    pass


fluxo.add_command(agressao, name="agressao")
fluxo.add_command(absorcao, name="absorcao")


if __name__ == '__main__':
    fluxo()
