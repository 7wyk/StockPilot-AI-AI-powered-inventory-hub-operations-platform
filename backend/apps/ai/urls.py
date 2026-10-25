from django.urls import path

from .views import (
    ChatView,
    ConfirmActionView,
    ConversationDetailView,
    ConversationListView,
    UserPreferenceDetailView,
    UserPreferenceView,
)

urlpatterns = [
    path("ai/chat/", ChatView.as_view(), name="ai-chat"),
    path("ai/conversations/", ConversationListView.as_view(), name="ai-conversations"),
    path("ai/conversations/<int:pk>/", ConversationDetailView.as_view(), name="ai-conversation-detail"),
    path("ai/confirm-action/", ConfirmActionView.as_view(), name="ai-confirm-action"),
    path("ai/preferences/", UserPreferenceView.as_view(), name="ai-preferences"),
    path("ai/preferences/<str:key>/", UserPreferenceDetailView.as_view(), name="ai-preference-detail"),
]
