from rest_framework import serializers
from .models import Place
from .models import Rating

class RatingSerializer(serializers.Serializer):
    place = serializers.UUIDField()
    rating = serializers.IntegerField(min_value = 1, max_value= 5)
    review = serializers.CharField(required=False, allow_blank=True)

    def validate(self,data):
        try:

            place = Place.objects.get(uuid=data['place'])

        except Place.DoesNotExist:
            raise serializers.ValidationError({ 
                'error': "A place with that id does not exist!"
            })
        data['place'] = place
        return data

    def create(self, validated_data):

        rating = Rating()
        rating.user = validated_data['user']
        rating.place = validated_data['place']
        rating.rating = validated_data['rating']
        rating.review = validated_data.get('review','')
        rating.save()
        return rating

    def update(self, instance, validated_data):
        instance.rating = validated_data['rating']
        instance.review = validated_data.get('review', instance.review)
        instance.save()
        return instance