from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        'message': 'Bienvenido a la API del Sistema de Gestión de Encomiendas',
        'version': 'v1',
        'endpoints': {
            'auth': {
                'token': reverse('token_obtain', request=request),
                'refresh': reverse('token_refresh', request=request),
            },
            'documentacion': {
                'swagger': reverse('swagger', request=request),
                'schema': reverse('schema', request=request),
            },
        }
    })

from rest_framework_simplejwt.views import TokenObtainPairView
from api.throttles import LoginRateThrottle

class EncomiendaTokenView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]
