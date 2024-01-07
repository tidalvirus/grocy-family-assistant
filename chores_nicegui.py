#!/usr/bin/env python3
"""Simple example of a nicegui app that uses a refreshable
UI element to show a list of chores from grocy."""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Callable, List

import requests
from dotenv import dotenv_values
from nicegui import ui

config = dotenv_values(".env")
headers = {
    "GROCY-API-KEY": f'{config["GROCY_API_KEY"]}',
    "Content-Type": "application/json",
}
grocy_host = config["GROCY_HOST"]
CHORES_URL = "/api/chores/"


def update_users():
    """
    Fetches the list of users from the grocy API and returns a dictionary
    mapping user IDs to their display names.

    Returns:
        dict: A dictionary mapping user IDs to display names.
    """
    response = requests.get(f"{grocy_host}/api/users", headers=headers, timeout=5)
    users_json = response.json()
    local_users = {user["id"]: user["display_name"] for user in users_json}
    return local_users  # , users_json


def update_chores():
    """
    Retrieves the list of chores from the grocy API and returns it as a JSON object.

    Returns:
        dict: A JSON object containing the list of chores.
    """
    response = requests.get(
        f"{grocy_host}/api/chores?order=next_estimated_execution_time",
        headers=headers,
        timeout=5,
    )
    chores_json = response.json()
    return chores_json


def time_diff(execute_time: datetime) -> str:
    """
    Calculates the time difference between the execute_time and the current time.

    Args:
        execute_time (datetime): The time to compare against the current time.

    Returns:
        str: The formatted time difference in hours or days.
    """
    # Calculate the time difference in seconds
    time_difference = (execute_time - datetime.now()).total_seconds()

    # Convert the time difference to hours or days
    if time_difference < 60 * 60 * 24:  # less than 24 hours
        due_time = f"{int(time_difference / (60 * 60))}h"  # convert to hours
    else:
        due_time = f"{int(time_difference / (60 * 60 * 24))}d"  # convert to days

    return due_time


@dataclass
class ChoreItem:
    """
    Represents a chore item.

    Attributes:
        id (int): The unique identifier of the chore item.
        name (str): The name of the chore item.
        assigned_user (int): The ID of the user assigned to the chore item.
        next_estimated_execution_time (str, optional): The next
        estimated execution time of the chore item.
    """

    id: int
    name: str
    assigned_user: int
    next_estimated_execution_time: str = ""

    def complete(self) -> None:
        """
        Completes the chore item.

        This method executes the chore and notifies the user about the completion.

        Returns:
            None
        """
        execute_chore(self)
        ui.notify(f"Chore {self.name} completed by {users[state.selected_user]}")


def execute_chore(item: ChoreItem):
    """
    Executes a chore by sending a POST request to the grocy API.

    Args:
        item (ChoreItem): The chore item to be executed.

    Returns:
        None
    """
    # Get the current date and time
    current_time = datetime.now()

    # Format the datetime object as a string
    time_string = current_time.strftime("%Y-%m-%dT%H:%M:%S")

    print(
        f"Trying to execute chore id: {item.id} with ",
        " {grocy_host}{CHORES_URL}{item.id}/execute",
    )
    try:
        response = requests.post(
            f"{grocy_host}{CHORES_URL}{item.id}/execute",
            headers=headers,
            data={
                "tracked_time": time_string,
                "done_by": state.selected_user,
                "skipped": "false",
            },
            timeout=5,  # Add timeout argument
        )
        print(f"chore id: {item.id} executed")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return
    if response.status_code == 200:
        ui.notify("Successfully executed chore")
        refresh_chores()
    elif response.status_code == 400:
        # Handle the error case
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
    """
    Refreshes the list of chores by clearing the existing list and adding updated
    chores.

    Parameters:
    None

    Returns:
    None
    """
    choreslist.clear()
    for local_chore in update_chores():
        choreslist.add(
            local_chore["id"],
            local_chore["chore_name"],
            local_chore["next_execution_assigned_to_user_id"],
            local_chore["next_estimated_execution_time"],
        )


@dataclass
class State:
    """
    Represents the state of the application.

    Attributes:
        selected_user (int): The ID of the selected user.
    """

    selected_user: int = 0

    def update_selected_user(self, user_id):
        """
        Updates the selected user ID.

        Args:
            user_id (int): The ID of the user to be selected.
        """
        self.selected_user = user_id


state = State()


@dataclass
class ChoreList:
    """
    Represents a list of chores.

    Attributes:
        title (str): The title of the chore list.
        on_change (Callable): A callback function to be called when the chore list changes.
        items (List[ChoreItem]): A list of ChoreItem objects representing the chores in the list.
    """

    title: str
    on_change: Callable
    items: List[ChoreItem] = field(default_factory=list)

    def add(
        self,
        chore_id: int,
        name: str,
        assigned_user: int,
        next_estimated_execution_time: str,
    ) -> None:
        """
        Adds a new chore to the list.

        Args:
            chore_id (int): The ID of the chore.
            name (str): The name of the chore.
            assigned_user (int): The ID of the user assigned to the chore.
            next_estimated_execution_time (str): The next estimated execution time of the chore.

        Returns:
            None
        """
        self.items.append(
            ChoreItem(
                chore_id,
                name,
                assigned_user,
                next_estimated_execution_time,
            )
        )
        self.on_change()

    def complete(self, item: ChoreItem):
        """
        Marks a chore as complete.

        Args:
            item (ChoreItem): The ChoreItem object representing the chore to be marked as complete.

        Returns:
            None
        """
        item.complete()
        self.on_change()

    def clear(self):
        """
        Clears all the chores from the list.

        Returns:
            None
        """
        self.items.clear()
        if self.on_change:
            self.on_change()


def replace(chore_item, local_state):
    """
    Replaces the ui.dialog with a new one based on the user and chore selected.

    Args:
        chore_item (ChoreItem): The chore item to be replaced.
        local_state (LocalState): The local state object containing the selected user.

    Returns:
        None
    """
    if local_state.selected_user < 1:
        ui.notify(f"Pick a user!  {local_state.selected_user}")
        return
    dialog.clear()
    with dialog, ui.card():
        ui.label(
            f"Completing chore {chore_item.name} as {users[local_state.selected_user]}"
        )
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
    """
    Displays the chore items categorized by their due dates.

    The function categorizes the chore items based on their due dates and displays them using a
    user interface.
    Chore items that are past due are displayed first, followed by items due within the
    next 24 hours, items due within the next 48 hours, and items due within the next week.

    Args:
        None

    Returns:
        None
    """
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
        # Create the user and chore name string
        user_chore_str = (
            f"{users[chore_item.assigned_user].upper()} - {chore_item.name}"
        )

        # Create the time difference string
        time_diff_str = f" - ~{time_diff(execute_time)}"

        # Combine the strings
        message = user_chore_str + time_diff_str

        if execute_time > time_now and execute_time <= time_now + timedelta(hours=24):
            with ui.row().classes("items-center"):
                ui.button(
                    message,
                    on_click=lambda chore_item=chore_item: replace(chore_item, state),
                ).props("no-caps color=amber text-color=black")
    # if <48 hours
    ui.label("< 48 hours")
    for chore_item in choreslist.items:
        execute_time = datetime.strptime(
            chore_item.next_estimated_execution_time, "%Y-%m-%d %H:%M:%S"
        )
        # Create the user and chore name string
        user_chore_str = (
            f"{users[chore_item.assigned_user].upper()} - {chore_item.name}"
        )

        # Create the time difference string
        time_diff_str = f" - ~{time_diff(execute_time)}"

        # Combine the strings
        message = user_chore_str + time_diff_str

        if execute_time >= time_now + timedelta(
            hours=24
        ) and execute_time <= time_now + timedelta(hours=48):
            with ui.row().classes("items-center"):
                ui.button(
                    message,
                    on_click=lambda chore_item=chore_item: replace(chore_item, state),
                ).props("no-caps")
    # if <168 hours (1 week)
    ui.label("< 1 week")
    for chore_item in choreslist.items:
        execute_time = datetime.strptime(
            chore_item.next_estimated_execution_time, "%Y-%m-%d %H:%M:%S"
        )
        # Create the user and chore name string
        user_chore_str = (
            f"{users[chore_item.assigned_user].upper()} - {chore_item.name}"
        )

        # Create the time difference string
        time_diff_str = f" - ~{time_diff(execute_time)}"

        # Combine the strings
        message = user_chore_str + time_diff_str

        if execute_time >= time_now + timedelta(
            hours=48
        ) and execute_time <= time_now + timedelta(days=7):
            with ui.row().classes("items-center"):
                ui.button(
                    message,
                    on_click=lambda chore_item=chore_item: replace(chore_item, state),
                ).props("no-caps color=green")
    # Add a collapsible section for the final list of chores
    with ui.expansion("Future chores"):
        # as final_list:
        for chore_item in choreslist.items:
            execute_time = datetime.strptime(
                chore_item.next_estimated_execution_time, "%Y-%m-%d %H:%M:%S"
            )
            # Create the user and chore name string
            user_chore_str = (
                f"{users[chore_item.assigned_user].upper()} - {chore_item.name}"
            )

            # Create the time difference string
            time_diff_str = f" - ~{time_diff(execute_time)}"

            # Combine the strings
            message = user_chore_str + time_diff_str

            if execute_time > time_now + timedelta(days=7):
                # Add each chore to the final list
                with ui.row().classes("items-center"):
                    ui.button(
                        message,
                        on_click=lambda chore_item=chore_item: replace(
                            chore_item, state
                        ),
                    ).props("no-caps color=green")


# This seems to be needed, so that we can replace the dialog when completing chores.
with ui.dialog() as dialog, ui.card():
    ui.label("Completing chore as")  # {users[usertoggle.value]}')
    with ui.row():
        ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
        ui.button("No", on_click=dialog.close)


def get_key(my_dict, val):
    """
    Returns the key of a given value in a dictionary.

    Args:
        my_dict (dict): The dictionary to search in.
        val: The value to search for.

    Returns:
        The key corresponding to the given value, or 0 if the value is not found.
    """
    for key, value in my_dict.items():
        if val == value:
            return key
    return 0


# pylint: disable-next=unnecessary-lambda
usertoggle = ui.toggle(users, on_change=lambda: set_current_user()).props("inline")


def set_current_user():
    """
    Sets the current user based on the value of `usertoggle`.

    This function updates the selected user in the global `state` object based on the value of
    `usertoggle`.

    Parameters:
        None

    Returns:
        None
    """
    state.update_selected_user(usertoggle.value)
    chore_ui.refresh()


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
