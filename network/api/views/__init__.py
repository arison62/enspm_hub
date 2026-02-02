from ninja import Router
from .mentorship import mentorship_router
from .organisation import organisation_router
from .chat import chat_router

network_router = Router(tags=["Network"])

network_router.add_router("/mentoring/", mentorship_router)
network_router.add_router("/organisations/", organisation_router)
network_router.add_router("/chat/", chat_router)
