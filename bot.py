#!/usr/bin/python
# -*- coding: utf-8 -*-

import discord
from discord.ext import commands
from discord_slash import SlashCommand
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle
from enum import Enum

ticket_manager_role_name = "›› Developer ‹‹"



class ReturnCodes(Enum):
    SUCCESS = 0
    ERROR = 1
    TIMEOUT = 2
    EXISTS = 3
    NOT_FOUND = 4
    CANCELLED = 5
    FORBIDDEN = 6


class TicketTypes(Enum):
    TICKET = 0
    IDEA = 1
    BUG = 2


bot = commands.Bot(command_prefix="*", help_command=None)
slash = SlashCommand(bot, sync_commands=True)


@bot.event
async def on_ready():
    print(f"bot successfully booted up as {bot.user}")


async def get_open_tickets_category(guild):
    category_name = "tickets"
    open_category = discord.utils.get(guild.categories, name=category_name)
    if open_category is None:
        open_category = await guild.create_category(name=category_name)
    return open_category


async def get_archived_tickets_category(guild):
    category_name = "tickets-archived"
    archived_category = discord.utils.get(guild.categories, name=category_name)
    if archived_category is None:
        archived_category = await guild.create_category(name=category_name)
    return archived_category


@bot.command(name="close", aliases=["archive"])
async def close_cmd(ctx):

    if ctx.channel.category.name != "tickets":
        await ctx.send(
            embed=discord.Embed(
                title=f"Kein Ticket",
                description="Du befindest dich nicht in einem Ticket, oder es ist bereits geschlossen.",
                colour=discord.Colour.dark_red()
            )
        )
        return

    await ctx.channel.edit(category=await get_archived_tickets_category(ctx.guild))

    await ctx.send(
        embed=discord.Embed(
            title=f"Ticket geschlossen",
            description=f"Das Ticket wurde von {ctx.author} geschlossen",
            colour=discord.Colour.dark_red()
        )
    )


@bot.command(name="label")
async def assign_cmd(ctx, *args):
    if len(args) == 0:
        return

    if discord.utils.get(ctx.guild.roles, name=ticket_manager_role_name) not in ctx.author.roles:
        await ctx.send(
            embed=discord.Embed(
                title="Fehlende Berechtigung",
                description="Dir fehlt die Berechtigung, diesem Ticket ein Label zuzuweisen",
                colour=discord.Colour.dark_red()
            )
        )

    label = args[0]

    await ctx.send(
        embed=discord.Embed(
            title=f"Label hinzugefügt",
            description=f"Diesem Ticket wurde das Label {label} zugewiesen",
            colour=discord.Colour.blue()
        )
    )


@bot.command(name="assign")
async def assign_cmd(ctx):
    if discord.utils.get(ctx.guild.roles, name=ticket_manager_role_name) not in ctx.author.roles:
        await ctx.send(
            embed=discord.Embed(
                title="Fehlende Berechtigung",
                description="Dir fehlt die Berechtigung, diesem Ticket einen Nutzer zuzuweisen",
                colour=discord.Colour.dark_red()
            )
        )

    assigned_user = ctx.message.mentions[0]
    if len(ctx.message.mentions) == 0:
        assigned_user = ctx.author

    await ctx.send(
        embed=discord.Embed(
            title=f"Ticket zugewiesen",
            description=f"Dein Anliegen wurde {assigned_user.mention} zugewiesen",
            colour=discord.Colour.dark_green()
        )
    )


async def create_ticket(ctx, ticket_type=TicketTypes.TICKET):
    from random import randint
    ticket_id = randint(1000, 9999)
    if ticket_type == TicketTypes.IDEA:
        channel_name = f"vorschlag-{str(ticket_id)}"
        ticket_type_name = "suggestion"

    elif ticket_type == TicketTypes.BUG:
        channel_name = f"bug-{str(ticket_id)}"
        ticket_type_name = "bug report"

    else:
        channel_name = f"ticket-{str(ticket_id)}"
        ticket_type_name = "ticket"

    ticket_channel = await ctx.guild.create_text_channel(
        name=channel_name,
        category=await get_open_tickets_category(ctx.guild)
    )
    await ticket_channel.set_permissions(
        ctx.author,
        read_messages=True,
        send_messages=True
    )

    welcome_embed = discord.Embed(
        title=
        f"{ticket_type_name} von {ctx.author.name}",
        description=
        f"Thank you for contacting us, {ctx.author.mention}!\n"
        "We will handle your request as soon as possible.\n"
        f"In this text channel, you can explain to us in detail what your problem is."
    )
    welcome_message = await ticket_channel.send(
        embed=welcome_embed,
        components=[
            create_actionrow(
                create_button(
                    style=ButtonStyle.blue,
                    label="Close ticket",
                    custom_id="close-ticket"
                )
            )
        ]
    )
    return ReturnCodes.SUCCESS


@bot.event
async def on_component(ctx):
    custom_id = ctx.component["custom_id"]
    if custom_id == "close-ticket":
        if ctx.channel.category.name != "tickets":
            await ctx.send(
                embed=discord.Embed(
                    title="No ticket",
                    description="You are not in a ticket, or it is already closed.",
                    colour=discord.Colour.dark_red()
                )
            )
            return

        await ctx.channel.edit(category=await get_archived_tickets_category(ctx.guild))
        await ctx.send(
            embed=discord.Embed(
                title=f"Ticket closed",
                description=f"The ticket was closed by {ctx.author}.",
                colour=discord.Colour.dark_red()
            )
        )
        return

    if custom_id == "create-support-ticket-bug":
        ticket_type = TicketTypes.BUG

    elif custom_id == "create-support-ticket-idea":
        ticket_type = TicketTypes.IDEA

    else:
        ticket_type = TicketTypes.TICKET

    setup_process = await create_ticket(ctx, ticket_type=ticket_type)
    if setup_process == ReturnCodes.SUCCESS:
        await ctx.send(
            "Ticket erfolgreich erstellt",
            hidden=True
        )


@bot.command(name="createbugmsg")
async def createbugmsg(ctx):
    await ctx.send(
        embed=discord.Embed(
            title="Submit a bug report",
            description="To submit a bug report, press the button below"
        ).set_footer(
            text="Audrey Ticket System",
            icon_url="https://cdn.discordapp.com/attachments/855038999483777034/880417992620507217/Ticket.png"
        ),
        components=[
            create_actionrow(
                create_button(
                    style=ButtonStyle.green,
                    label="Report a bug",
                    custom_id="create-support-ticket-bug"
                )
            )
        ]
    )


@bot.command(name="createideamsg")
async def createideamsg(ctx):
    await ctx.send(
        embed=discord.Embed(
            title="Submit a suggestion",
            description="To submit a suggestion, press the button below"
        ).set_footer(
            text="Audrey Ticket System",
            icon_url="https://cdn.discordapp.com/attachments/855038999483777034/880417992620507217/Ticket.png"
        ),
        components=[
            create_actionrow(
                create_button(
                    style=ButtonStyle.green,
                    label="Submit a suggestion",
                    custom_id="create-support-ticket-idea"
                )
            )
        ]
    )


bot.run("TOKEN")
