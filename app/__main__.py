import asyncio
import logging
import sys

import click

from app import bot


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    if ctx.invoked_subcommand is None:
        run()


@cli.command()
def run():
    asyncio.run(bot.run())


@cli.command()
@click.argument("url")
def set_webhook(url: str):
    asyncio.run(bot.set_webhook(url))
    click.echo("Webhook set")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s,%(msecs)03d %(name)-16s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    cli()
