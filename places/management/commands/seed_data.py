from django.core.management.base import BaseCommand
from places.models import State, City, Category as PlacesCategory
from posts.models import Location, Category as PostsCategory

class Command(BaseCommand):
    help = 'Seed both places and posts apps with location and category data.'

    def handle(self, *args, **kwargs):
        state_data = {
            "New South Wales": ["Sydney", "Newcastle", "Wollongong"],
            "Victoria": ["Melbourne", "Geelong", "Ballarat"],
            "Queensland": ["Brisbane", "Cairns", "Gold Coast"],
            "South Australia": ["Adelaide", "Mount Gambier", "Port Augusta"],
            "Western Australia": ["Perth", "Fremantle", "Broome"],
            "Tasmania": ["Hobart", "Launceston"],
            "Northern Territory": ["Darwin", "Alice Springs"],
            "Australian Capital Territory": ["Canberra"]
        }

        categories = [
            "Beaches", "Museums", "Parks", "Historical", "Shopping",
            "Art Galleries", "Natural", "Adventure", "Wildlife",
            "Wine Regions", "Mountains", "Culture", "Desert",
            "Aboriginal Heritage", "Hiking", "Outback", "Government", "Lake"
        ]

        # 填入州與城市（places app）
        for state_name, cities in state_data.items():
            state, _ = State.objects.get_or_create(name=state_name)
            for city_name in cities:
                City.objects.get_or_create(name=city_name, state=state)
                # 同時新增進 posts 的 Location
                Location.objects.get_or_create(name=city_name)

        # 填入分類（兩邊 app）
        for category_name in categories:
            PlacesCategory.objects.get_or_create(name=category_name)
            PostsCategory.objects.get_or_create(name=category_name)

        self.stdout.write(self.style.SUCCESS('✅ Seeded places and posts data successfully.'))
