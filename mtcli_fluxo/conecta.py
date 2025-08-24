import MetaTrader5 as mt5


def conectar():
    if not mt5.initialize():
        click.echo(f"❌ Erro ao conectar ao MT5: {mt5.last_error()}")
        exit()
    return True


def shutdown():
    mt5.shutdown()
