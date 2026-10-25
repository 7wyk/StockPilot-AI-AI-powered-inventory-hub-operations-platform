"""
AI assistant API views for StockPilot AI.

All endpoints strictly enforce:
- Authenticated user
- Active organization membership
- Tenant boundary isolation
- Server-side role authorization
"""

from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.services import InventoryOperationError
from apps.organizations.permissions import (
    OrganizationPermission,
    get_active_membership,
    has_organization_permission,
    organization_permission_class,
)

from . import services
from .models import Conversation, Message, UserPreference
from .serializers import (
    ChatInputSerializer,
    ConfirmActionSerializer,
    ConversationDetailSerializer,
    ConversationListSerializer,
    UserPreferenceSerializer,
)
from .tools import execute_confirmed_write_action


class ChatView(APIView):
    """
    POST /api/v1/ai/chat/
    Send a message to the AI operations assistant.
    Returns response with conversation ID, updated title, and message with any tool results.
    """
    permission_classes = [organization_permission_class(OrganizationPermission.USE_AI)]

    def post(self, request):
        serializer = ChatInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = get_active_membership(request.user)
        organization = membership.organization

        data = serializer.validated_data
        result = services.chat(
            organization=organization,
            user=request.user,
            message=data["message"],
            conversation_id=data.get("conversation_id"),
        )
        return Response(result, status=status.HTTP_200_OK)


class ConversationListView(APIView):
    """
    GET /api/v1/ai/conversations/ — list conversations for user in active org.
    POST /api/v1/ai/conversations/ — create a new empty conversation.
    """
    permission_classes = [organization_permission_class(OrganizationPermission.USE_AI)]

    def get(self, request):
        membership = get_active_membership(request.user)
        convs = (
            Conversation.objects.filter(
                organization=membership.organization,
                user=request.user,
                is_active=True,
            )
            .annotate(message_count=Count("messages"))
            .order_by("-updated_at")[:50]
        )
        serializer = ConversationListSerializer(convs, many=True)
        return Response(serializer.data)

    def post(self, request):
        membership = get_active_membership(request.user)
        title = request.data.get("title", "New conversation")
        conv = Conversation.objects.create(
            organization=membership.organization,
            user=request.user,
            title=title[:200],
        )
        serializer = ConversationDetailSerializer(conv)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    """
    GET /api/v1/ai/conversations/<pk>/ — fetch message history for conversation.
    DELETE /api/v1/ai/conversations/<pk>/ — delete/archive conversation.
    """
    permission_classes = [organization_permission_class(OrganizationPermission.USE_AI)]

    def _get_conversation(self, request, pk):
        membership = get_active_membership(request.user)
        return Conversation.objects.filter(
            pk=pk,
            organization=membership.organization,
            user=request.user,
            is_active=True,
        ).first()

    def get(self, request, pk):
        conv = self._get_conversation(request, pk)
        if not conv:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ConversationDetailSerializer(conv)
        return Response(serializer.data)

    def delete(self, request, pk):
        conv = self._get_conversation(request, pk)
        if not conv:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        conv.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConfirmActionView(APIView):
    """
    POST /api/v1/ai/confirm-action/
    Execute a proposed write operation after explicit user review and confirmation.
    Re-validates permissions and database constraints; reuses transactional services.
    """
    permission_classes = [organization_permission_class(OrganizationPermission.USE_AI)]

    def post(self, request):
        serializer = ConfirmActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = get_active_membership(request.user)
        organization = membership.organization

        action = serializer.validated_data["action"]
        parameters = serializer.validated_data["parameters"]

        try:
            result = execute_confirmed_write_action(
                action=action,
                parameters=parameters,
                organization=organization,
                user=request.user,
            )
            return Response(result, status=status.HTTP_200_OK)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except (ValueError, InventoryOperationError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"Failed to execute confirmed action: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserPreferenceView(APIView):
    """
    GET /api/v1/ai/preferences/ — get user's preferences for this organization.
    PUT /api/v1/ai/preferences/ — set/update a preference key-value pair.
    """
    permission_classes = [organization_permission_class(OrganizationPermission.USE_AI)]

    def get(self, request):
        membership = get_active_membership(request.user)
        prefs = UserPreference.objects.filter(
            organization=membership.organization,
            user=request.user,
        )
        serializer = UserPreferenceSerializer(prefs, many=True)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserPreferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = get_active_membership(request.user)
        key = serializer.validated_data["key"]
        value = serializer.validated_data["value"]

        pref, _ = UserPreference.objects.update_or_create(
            organization=membership.organization,
            user=request.user,
            key=key,
            defaults={"value": value},
        )
        return Response(UserPreferenceSerializer(pref).data, status=status.HTTP_200_OK)


class UserPreferenceDetailView(APIView):
    """DELETE /api/v1/ai/preferences/<key>/ — delete a specific preference."""
    permission_classes = [organization_permission_class(OrganizationPermission.USE_AI)]

    def delete(self, request, key):
        membership = get_active_membership(request.user)
        deleted, _ = UserPreference.objects.filter(
            organization=membership.organization,
            user=request.user,
            key=key,
        ).delete()
        if not deleted:
            return Response({"detail": "Preference not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
