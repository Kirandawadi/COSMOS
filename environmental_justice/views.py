from rest_framework import permissions, viewsets

from .models import EnvironmentalJusticeRow
from .serializers import EnvironmentalJusticeRowSerializer


class EnvironmentalJusticeRowViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows environmental justice rows to be read.
    """

    queryset = EnvironmentalJusticeRow.objects.all()
    serializer_class = EnvironmentalJusticeRowSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = [
        "get",
    ]
