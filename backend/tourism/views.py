from rest_framework.views import APIView
from core.permissions import IsPassenger
from .models import Rating
from .serializers import RatingSerializer
from rest_framework import status
from rest_framework.response import Response
"""
class RatingView(APIView):
    permission_classes = [IsPassenger]

    def post(self,request):

        serializer = RatingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user.passenger_profile)
            return Response({"message":"Rating added successfully"},status=status.HTTP_201_CREATED)
        return Response({"error":serializer.errors},status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, rating_id):
        try:
            rating = Rating.objects.get(id=rating_id)
            if request.user.passenger_profile != rating.user:
                return Response({"error":"You are not authorized to do this!"}, status=status.HTTP_403_FORBIDDEN)
            serializer = RatingSerializer(instance = rating, data = request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message":"Rating updated successfully!"},status=status.HTTP_200_OK)
            return Response({"error":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        except Rating.DoesNotExist:
            return Response({'error':"rating does not exist"}, status=status.HTTP_404_NOT_FOUND)
    

"""