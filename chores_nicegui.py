#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Callable, List
from dotenv import dotenv_values
from nicegui import ui

import requests
import json
from typing import Callable, List
from nicegui import ui
from datetime import datetime, date
from datetime import timedelta

config = dotenv_values(".env")
headers = {
    "GROCY-API-KEY": f'{config["GROCY_API_KEY"]}',
    "Content-Type": "application/json",
}
grocy_host = config["GROCY_HOST"]
complete_chore_url = "/api/chores/"


def update_users():
    response = requests.get(f"{grocy_host}/api/users", headers=headers)
    users_json = response.json()
    users = {user["id"]: user["display_name"] for user in users_json}
    return users  # , users_json


def update_chores():
    response = requests.get(
        f"{grocy_host}/api/chores?order=next_estimated_execution_time", headers=headers
    )
    chores_json = response.json()
    return chores_json


@dataclass
class ChoreItem:
    id: int
    name: str
    assigned_user: int
    next_estimated_execution_time: str = None

    def complete(self) -> None:
        execute_chore(self)
        ui.notify(f"Chore {self.name} completed by {users[state.selected_user]}")


def execute_chore(item: ChoreItem):
    # Get the current date and time
    current_time = datetime.now()

    # Format the datetime object as a string
    time_string = current_time.strftime("%Y-%m-%dT%H:%M:%S")

    print(
        f"Trying to execute chore id: {item.id} with {grocy_host}{complete_chore_url}{item.id}/execute"
    )
    try:
        response = requests.post(
            f"{grocy_host}{complete_chore_url}{item.id}/execute",
            headers=headers,
            json={
                "tracked_time": time_string,
                "done_by": state.selected_user,
                "skipped": "false",
            },
        )
        print(f"chore id: {item.id} executed")
    except Exception as e:
        print(f"An error occurred: {e}")
        return
    if response.status_code == 200:
        ui.notify("Successfully executed chore")
        refresh_chores()
    elif response.status_code == 400:
        ui.notify(f"Error creating: {response.json().get('error_message')}")
        print(f"Error creating: {response.json().get('error_message')}")
        return
    elif response.status_code == 500:
        ui.notify(f"Error creating: {response.json().get('error_message')}")
        print(f"Error creating: {response.json().get('error_message')}")
        return
    else:
        ui.notify(f"Unclear what occurred, response: {response.status_code}")
        print(f"Unclear what occurred, response: {response.status_code}")
        return


users = update_users()


userlist = []
for user in users:
    userlist.append(user)


def refresh_chores():
    choreslist.clear()
    for chore in update_chores():
        choreslist.add(
            chore["id"],
            chore["chore_name"],
            chore["next_execution_assigned_to_user_id"],
            chore["next_estimated_execution_time"],
        )


@dataclass
class State:
    selected_user: int = 0

    def update_selected_user(self, id):
        self.selected_user = id


state = State()


@dataclass
class ChoreList:
    title: str
    on_change: Callable
    items: List[ChoreItem] = field(default_factory=list)

    def add(
        self, id: int, name: str, assigned_user: int, next_estimated_execution_time: str
    ) -> None:
        self.items.append(
            ChoreItem(
                id,
                name,
                assigned_user,
                next_estimated_execution_time,
            )
        )
        self.on_change()

    def complete(self, item: ChoreItem):
        item.complete()
        # self.items.remove(item)
        self.on_change()

    def clear(self):
        self.items.clear()
        if self.on_change:
            self.on_change()


def replace(chore_item, state):
    if state.selected_user < 1:
        ui.notify(f"Pick a user!  {state.selected_user}")
        return
    dialog.clear()
    with dialog, ui.card():
        ui.label(f"Completing chore {chore_item.name} as {users[state.selected_user]}")
        with ui.row():
            ui.button(
                "Yes",
                on_click=lambda: (
                    dialog.submit("Yes"),
                    choreslist.complete(chore_item),
                    dialog.close(),
                ),
            )
            ui.button("No", on_click=dialog.close)
    dialog.open()


@ui.refreshable
def chore_ui():
    if not choreslist.items:
        ui.label("List is empty.").classes("mx-auto")
        return
    time_now = datetime.now()
    # if in the past
    ui.label("PAST DUE")
    for chore_item in choreslist.items:
        execute_time = datetime.strptime(
            chore_item.next_estimated_execution_time, "%Y-%m-%d %H:%M:%S"
        )
        if execute_time < time_now:
            with ui.row().classes("items-center"):
                ui.button(
                    f"{users[chore_item.assigned_user].upper()} - {chore_item.name}",
                    on_click=lambda chore_item=chore_item: replace(chore_item, state),
                ).props("no-caps color=deep-orange text-color=white")

    # if between now and 24 hours
    ui.label("< 24 hours")
    for chore_item in choreslist.items:
        execute_time = datetime.strptime(
            chore_item.next_estimated_execution_time, "%Y-%m-%d %H:%M:%S"
        )

        if execute_time > time_now and execute_time <= time_now + timedelta(hours=24):
            with ui.row().classes("items-center"):
                ui.button(
                    f"{users[chore_item.assigned_user].upper()} - {chore_item.name}",
                    on_click=lambda chore_item=chore_item: replace(chore_item, state),
                ).props("no-caps color=amber text-color=black")
    # if <48 hours
    ui.label("< 48 hours")
    for chore_item in choreslist.items:
        execute_time = datetime.strptime(
            chore_item.next_estimated_execution_time, "%Y-%m-%d %H:%M:%S"
        )

        if execute_time >= time_now + timedelta(
            hours=24
        ) and execute_time <= time_now + timedelta(hours=48):
            with ui.row().classes("items-center"):
                ui.button(
                    f"{users[chore_item.assigned_user].upper()} - {chore_item.name}",
                    on_click=lambda chore_item=chore_item: replace(chore_item, state),
                ).props("no-caps")
    # if <168 hours (1 week)
    ui.label("< 1 week")
    for chore_item in choreslist.items:
        execute_time = datetime.strptime(
            chore_item.next_estimated_execution_time, "%Y-%m-%d %H:%M:%S"
        )

        if execute_time >= time_now + timedelta(
            hours=48
        ) and execute_time <= time_now + timedelta(days=7):
            with ui.row().classes("items-center"):
                ui.button(
                    f"{users[chore_item.assigned_user].upper()} - {chore_item.name}",
                    on_click=lambda chore_item=chore_item: replace(chore_item, state),
                ).props("no-caps color=green")


# This seems to be needed, so that we can replace the dialog when completing chores.
with ui.dialog() as dialog, ui.card():
    ui.label(f"Completing chore as")  # {users[usertoggle.value]}')
    with ui.row():
        ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
        ui.button("No", on_click=dialog.close)


def get_key(my_dict, val):
    for key, value in my_dict.items():
        if val == value:
            return key
    return 0


usertoggle = ui.toggle(
    users, on_change=lambda: (set_current_user(), chore_ui.refresh())
).props("inline")


def set_current_user():
    print(usertoggle.value)
    state.update_selected_user(usertoggle.value)


choreslist = ChoreList("Chores", on_change=chore_ui.refresh)
today = date.today()
for chore in update_chores():
    choreslist.add(
        chore["id"],
        chore["chore_name"],
        chore["next_execution_assigned_to_user_id"],
        chore["next_estimated_execution_time"],
    )

with ui.card().classes("w-80 items-stretch"):
    chore_ui()

with ui.row().classes("items-center"):
    ui.button("Refresh", on_click=refresh_chores)

ui.run()
