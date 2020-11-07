import discord
from discord.ext import commands
import pickle
from copy import deepcopy

TEXT_CHANNEL_CAT_ID = 769885792038289446
TEXT_CHANNEL_CAT_ID = 774423497274687541


class TodoList:
    @staticmethod
    async def create_list(guild, user):
        user_id = user.id
        nick = user.name.replace(' ', '-')
        channel = await guild.get_channel(TEXT_CHANNEL_CAT_ID
                                          ).create_text_channel(f'{nick}-todo')
        done = await channel.send('**DONE**')
        todo = await channel.send('**TODO**')
        return TodoList(user_id, channel.id, done.id, todo.id)

    def __init__(self, user_id, channel_id, done_id, todo_id):
        self.user_id = user_id
        self.channel_id = channel_id
        self.done_id = done_id
        self.todo_id = todo_id
        self.error_id = None
        self.todo = {}
        self.done = {}


class Todos(commands.Cog):
    def __init__(self):
        try:
            with open('files/todo_lists.pik', 'rb') as f:
                self.todo_lists = pickle.load(f)
        except FileNotFoundError:
            self.todo_lists = {}

    async def cog_after_invoke(self, ctx):
        for k in self.todo_lists.keys():
            print('saving list with error id?',
                  hasattr(self.todo_lists[k], 'error_id'))
        with open('files/todo_lists.pik', 'wb') as f:
            pickle.dump(self.todo_lists, f)

    @commands.command(pass_context=True)
    async def done(self, ctx, number: int):
        try:
            # Start transaction
            tdl = deepcopy(self.todo_lists[ctx.author.id])
            tdl.done[number] = tdl.todo[number]
            del tdl.todo[number]
            await edit_message(ctx, tdl.done_id,
                               make_todo_list_msg('DONE', tdl.done))
            await edit_message(ctx, tdl.todo_id,
                               make_todo_list_msg('TODO', tdl.todo))
            # Commit
            self.todo_lists[ctx.author.id] = tdl
        except Exception as e:
            # Abort
            await send_or_edit(ctx, self.todo_lists[ctx.author.id],
                               f'Failed to move todo to done: {e}')
        finally:
            await ctx.message.delete()

    @commands.command(pass_context=True)
    async def add(self, ctx, *text):
        try:
            # Start transaction
            tdl = deepcopy(self.todo_lists[ctx.author.id])
            m = max([-1] + list(tdl.todo.keys()) + list(tdl.done.keys())) + 1
            tdl.todo[m] = ' '.join(text)
            await edit_message(ctx, tdl.todo_id,
                               make_todo_list_msg('TODO', tdl.todo))
            # Commit
            self.todo_lists[ctx.author.id] = tdl
        except Exception as e:
            # Abort
            await send_or_edit(ctx, self.todo_lists[ctx.author.id],
                               f'Failed to add new todo: {e}')
        finally:
            await ctx.message.delete()

    @commands.command(pass_context=True)
    async def edit(self, ctx, number: int, *text):
        try:
            # Start transaction
            tdl = deepcopy(self.todo_lists[ctx.author.id])
            if number in tdl.todo:
                tdl.todo[number] = ' '.join(text)
                await edit_message(ctx, tdl.todo_id,
                                   make_todo_list_msg('TODO', tdl.todo))
            elif number in tdl.done:
                tdl.done[number] = ' '.join(text)
                await edit_message(ctx, tdl.done_id,
                                   make_todo_list_msg('DONE', tdl.done))
            else:
                raise Exception('No such todo')
            # Commit
            self.todo_lists[ctx.author.id] = tdl
        except Exception as e:
            # Abort
            await send_or_edit(ctx, self.todo_lists[ctx.author.id],
                               f'Failed to edit todo: {e}')
        finally:
            await ctx.message.delete()

    @commands.command(pass_context=True)
    async def delete(self, ctx, number: int):
        try:
            # Start transaction
            tdl = deepcopy(self.todo_lists[ctx.author.id])
            del tdl.todo[number]
            await edit_message(ctx, tdl.todo_id,
                               make_todo_list_msg('TODO', tdl.todo))
            # Commit
            self.todo_lists[ctx.author.id] = tdl
        except Exception as e:
            # Abort
            await send_or_edit(ctx, self.todo_lists[ctx.author.id],
                               f'Failed to delete todo: {e}')
        finally:
            await ctx.message.delete()

    @commands.command(pass_context=True)
    async def make_todo_list(self, ctx):
        if ctx.author.id in self.todo_lists:
            await ctx.channel.send('You already have a todo list')
        else:
            self.todo_lists[ctx.author.id] = await TodoList.create_list(
                ctx.guild, ctx.author)
            await ctx.channel.send('Todo list created')


async def edit_message(ctx, msg_id, content):
    await (await ctx.fetch_message(msg_id)).edit(content=content)


async def send_or_edit(ctx, tdl, msg):
    if hasattr(tdl, 'error_id') and tdl.error_id:
        await edit_message(ctx, tdl.error_id, msg)
    else:
        m = await ctx.channel.send(msg)
        tdl.error_id = m.id


def make_todo_list_msg(title, todos) -> str:
    return f'**{title}**' + \
    '```' + \
    '\n'.join(map(lambda x: f'{x}: {todos[x]}', sorted(todos.keys()))) + \
    '```'
