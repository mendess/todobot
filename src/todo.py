import discord
from discord.ext import commands
import pickle
from copy import deepcopy


TEXT_CHANNEL_CAT_ID = 769885792038289446

class TodoList:
    @staticmethod
    async def create_list(guild, user):
        user_id = user.id
        nick = user.name.replace(' ', '-')
        channel = await guild.get_channel(TEXT_CHANNEL_CAT_ID).create_text_channel(f'{nick}-todo')
        done = await channel.send('**DONE**')
        todo = await channel.send('**TODO**')
        return TodoList(user_id, channel.id, done.id, todo.id)

    def __init__(self, user_id, channel_id, done_id, todo_id):
        self.user_id = user_id
        self.channel_id = channel_id
        self.done_id = done_id
        self.todo_id = todo_id
        self.todo = {}
        self.done = {}


class Todos(commands.Cog):
    def __init__(self):
        try:
            with open('files/todo_lists.pik', 'rb') as f:
                self.todo_lists = pickle.load(f)
        except FileNotFoundError:
            self.todo_lists = {}

    def save_todo_list(self):
        with open('files/todo_lists.pik', 'wb') as f:
            pickle.dump(self.todo_lists, f)


    @commands.command(pass_context=True)
    async def done(self, ctx, number: int):
        try:
            tdl = deepcopy(self.todo_lists[ctx.author.id])
            tdl.done[number] = tdl.todo[number]
            del tdl.todo[number]
            await edit_message(ctx, tdl.done_id, 'DONE', tdl.done)
            await edit_message(ctx, tdl.todo_id, 'TODO', tdl.todo)
            self.todo_lists[ctx.author.id] = tdl
            self.save_todo_list()
            await ctx.message.delete()
        except Exception as e:
            await ctx.channel.send(f'Failed to move todo to done: {e}')


    @commands.command(pass_context=True)
    async def add(self, ctx, *text):
        try:
            tdl = deepcopy(self.todo_lists[ctx.author.id])
            if len(tdl.todo.keys()) == 0:
                m = 0
            else:
                m = max(tdl.todo.keys()) + 1
            tdl.todo[m] = ' '.join(text)
            await edit_message(ctx, tdl.todo_id, 'TODO', tdl.todo)
            self.todo_lists[ctx.author.id] = tdl
            self.save_todo_list()
            await ctx.message.delete()
        except Exception as e:
            await ctx.channel.send(f'Failed to add new todo: {e}')


    @commands.command(pass_context=True)
    async def edit(self, ctx, number: int, *text):
        try:
            tdl = deepcopy(self.todo_lists[ctx.author.id])
            if number in tdl.todo:
                tdl.todo[number] = ' '.join(text)
                await edit_message(ctx, tdl.todo_id, 'TODO', tdl.todo)
            elif number in tdl.done:
                tdl.done[number] = ' '.join(text)
                await edit_message(ctx, tdl.done_id, 'DONE', tdl.done)
            else:
                await ctx.channel.send('No such todo item')
            self.todo_lists[ctx.author.id] = tdl
            await ctx.message.delete()
        except Exception as e:
            await ctx.channel.send(f'Failed to edit todo: {e}')


    @commands.command(pass_context=True)
    async def make_todo_list(self, ctx):
        if ctx.author.id in self.todo_lists:
            await ctx.channel.send('You already have a todo list')
        else:
            self.todo_lists[ctx.author.id] = await TodoList.create_list(ctx.guild, ctx.author)
            await ctx.channel.send('Todo list created')


async def edit_message(ctx, msg_id, title, todos):
    await (await
           ctx.fetch_message(msg_id
                             )).edit(content=make_todo_list_msg(title, todos))



def make_todo_list_msg(title, todos) -> str:
    return f'**{title}**' + \
    '```' + \
    '\n'.join(map(lambda x: f'{x}: {todos[x]}', sorted(todos.keys()))) + \
    '```'

