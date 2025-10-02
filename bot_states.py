from enum import Enum

class BotState(Enum):
    INITIAL = "initial"
    WAITING_FOR_WORKER_DETAILS = "waiting_for_worker_details"
    WAITING_FOR_SHOP_DETAILS = "waiting_for_shop_details"
    WAITING_FOR_DRIVER_DETAILS = "waiting_for_driver_details"
    WAITING_FOR_SUGGESTION = "waiting_for_suggestion"
