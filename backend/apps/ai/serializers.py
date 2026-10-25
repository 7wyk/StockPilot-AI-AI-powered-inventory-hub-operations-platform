from rest_framework import serializers

from .models import Conversation, Message, UserPreference


class ChatInputSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000, required=True)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "role",
            "content",
            "tool_calls",
            "tool_results",
            "metadata",
            "created_at",
        ]


class ConversationListSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "is_active",
            "created_at",
            "updated_at",
            "message_count",
        ]


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "is_active",
            "created_at",
            "updated_at",
            "messages",
        ]


class ConfirmActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[
            "receive_stock",
            "issue_stock",
            "adjust_stock",
            "create_transfer",
            "create_restock_request",
        ]
    )
    parameters = serializers.DictField()


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ["key", "value", "updated_at"]

    def validate_key(self, value):
        if value not in UserPreference.ALLOWED_KEYS:
            raise serializers.ValidationError(
                f"Invalid preference key '{value}'. Allowed keys: {sorted(UserPreference.ALLOWED_KEYS)}"
            )
        return value
