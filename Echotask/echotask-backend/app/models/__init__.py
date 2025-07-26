from .user import User
from .area import Area
from .building import Building
from .supply_item import SupplyItem
from .supply_request import SupplyRequest
from .supply_request_item import SupplyRequestItem

# 1) A folder with an __init__.py becomes a Python package/module
# 2) This allows Python to treat that folder like a module you can import.
# 3) It’s also where you can control what gets imported when other files use from something import *

# e.g. 'from models import User, Area'
#   -> instead of: 'from models.user import User' or 'from models.area import Area'