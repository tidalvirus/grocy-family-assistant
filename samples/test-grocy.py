from pygrocy import Grocy

# Obtain a grocy instance
grocy = Grocy("host", "key", port = 443)

# Get users and chores
users = grocy.users()
chores = grocy.chores(get_details=True)

for user in users:
    print(user.display_name)

for chore in chores:
    print(chore.name)