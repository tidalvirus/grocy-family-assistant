#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Callable, List
from dotenv import dotenv_values
from nicegui import ui

import requests

config = dotenv_values(".env")
headers = {'GROCY-API-KEY': f'{config["GROCY_API_KEY"]}'}
grocy_host = config["GROCY_HOST"]

def update_users():
    response = requests.get(f'{grocy_host}/api/users', headers=headers)
    users_json = response.json()
    users = {user['id']: user['display_name'] for user in users_json}
    return users, users_json

def update_chores():
    response = requests.get(f'{grocy_host}/api/chores?order=next_estimated_execution_time', headers=headers)
    chores_json = response.json()
    chores = {chore['id']: chore['chore_name'] for chore in chores_json}
    return chores, chores_json

chores, chores_json = update_chores()
users, users_json = update_users()

@dataclass
class ChoreItem:
    id: int
    name: str
    # done: bool = False


@dataclass
class ChoreList:
    title: str
    on_change: Callable
    items: List[ChoreItem] = field(default_factory=list)

    def add(self, id: int, name: str) -> None:
        self.items.append(ChoreItem(id, name))
        self.on_change()

    def complete(self, item: ChoreItem) -> None:
        pass
        self.on_change()

def show():
    result = dialog
    if result == 'Yes':
        ui.notify('Chore completed')
    else:
        ui.notify('Chore not completed')

def replace(item):
    currentuser=users[usertoggle.value]
    # currentchore=choreslist.item[name]
    dialog.clear()
    with dialog, ui.card():
        ui.label(f'Completing chore as {currentuser}')
        with ui.row():
            ui.button('Yes', on_click=lambda: dialog.submit('Yes'))
            ui.button('No', on_click=lambda: dialog.submit('No'))
    dialog.open()


@ui.refreshable
def chore_ui():
    if not choreslist.items:
        ui.label('List is empty.').classes('mx-auto')
        return
    for item in choreslist.items:
        with ui.row().classes('items-center'):
            # ui.checkbox(value=item.done, on_change=chore_ui.refresh).bind_value(item, 'done')
            ui.button(item.name, on_click=lambda: replace(item)) #.classes('flex-grow').bind_value(item, 'name')
            # ui.button(on_click=lambda item=item: choreslist.remove(item), icon='delete').props('flat fab-mini color=grey')

with ui.dialog() as dialog, ui.card():
    ui.label(f'Completing chore as') #{users[usertoggle.value]}')
    with ui.row():
        ui.button('Yes', on_click=lambda: dialog.submit('Yes'))
        ui.button('No', on_click=lambda: dialog.submit('No'))

usertoggle=ui.toggle(users, on_change=chore_ui.refresh()).props('inline')
# ui.button("Refresh", on_click=lambda: ui.refresh())
# ui.toggle(chores)

# with ui.dialog() as dialog, ui.card():
#     ui.label(f'Completing chore as {users[usertoggle.value]}')
#     with ui.row():
#         ui.button('Yes', on_click=lambda: dialog.submit('Yes'))
#         ui.button('No', on_click=lambda: dialog.submit('No'))



choreslist = ChoreList('Chores', on_change=chore_ui.refresh)
with ui.row():
    for chore in chores:
        choreslist.add(chore, chores[chore])

with ui.card().classes('w-80 items-stretch'):
    # ui.label().bind_text_from(choreslist, 'title').classes('text-semibold text-2xl')
    chore_ui()

ui.run()
