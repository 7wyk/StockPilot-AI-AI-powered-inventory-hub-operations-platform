from rest_framework import serializers


class ChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)


class ConversationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    created_at = serializers.CharField()
    updated_at = serializers.CharField()
    message_count = serializers.IntegerField()
