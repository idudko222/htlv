from results.models import Match
from results.serializers import MatchSerializer
from rest_framework import permissions, viewsets

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    permission_classes = [permissions.AllowAny]