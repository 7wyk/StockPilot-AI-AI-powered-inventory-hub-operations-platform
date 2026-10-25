from rest_framework import permissions
from rest_framework.generics import ListAPIView

from .models import Organization
from .serializers import OrganizationSummarySerializer


class OrganizationListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrganizationSummarySerializer

    def get_queryset(self):
        return Organization.objects.filter(memberships__user=self.request.user, memberships__is_active=True).distinct()
