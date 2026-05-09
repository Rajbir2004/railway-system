from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from railway.models import Add_Train, Add_route
import random

class Command(BaseCommand):
    help = 'Seeds the database with sample trains and routes'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # List of realistic Indian train names
        train_names = [
            "Rajdhani Express", "Shatabdi Express", "Vande Bharat Express", 
            "Duronto Express", "Garib Rath Express", "Tejas Express",
            "Sampark Kranti", "Humsafar Express", "Gatimaan Express",
            "Jan Shatabdi", "Vivek Express", "Coromandel Express"
        ]

        cities = ["Delhi", "Mumbai", "Kolkata", "Chennai", "Bengaluru", "Hyderabad", "Ahmedabad", "Pune", "Jaipur", "Lucknow", "Patna", "Chandigarh"]

        # Create trains
        trains_created = 0
        for name in train_names:
            fcity = random.choice(cities)
            tcity = random.choice([c for c in cities if c != fcity])
            
            # Avoid duplicate train numbers easily
            train_num = random.randint(1000, 9999)
            if Add_Train.objects.filter(train_no=train_num).exists():
                continue
                
            train, created = Add_Train.objects.get_or_create(
                train_no=train_num,
                defaults={
                    'trainname': name,
                    'from_city': fcity,
                    'to_city': tcity,
                    'departuretime': f"{random.randint(6, 20):02d}:00",
                    'arrivaltime': f"{random.randint(8, 23):02d}:30",
                    'trevaltime': f"{random.randint(2, 14)} hours",
                    'distance': random.randint(150, 1200)
                }
            )
            
            if created:
                trains_created += 1
                
                # Add 2-4 routes for each train
                num_routes = random.randint(2, 4)
                for _ in range(num_routes):
                    route_city = random.choice(cities)
                    Add_route.objects.get_or_create(
                        train=train,
                        route=route_city,
                        defaults={
                            'distance': random.randint(50, train.distance),
                            'fare': random.randint(25, 300)
                        }
                    )

        self.stdout.write(self.style.SUCCESS(f'Successfully created {trains_created} new trains and their routes.'))
