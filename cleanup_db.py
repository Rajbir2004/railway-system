import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RailwayDjango.settings')
django.setup()

from railway.models import Add_Train, Add_route

def cleanup():
    print("Starting database cleanup...")
    
    # 1. Remove duplicate trains (keeping only the one with the lowest ID)
    train_nos = Add_Train.objects.values_list('train_no', flat=True).distinct()
    for t_no in train_nos:
        trains = Add_Train.objects.filter(train_no=t_no).order_by('id')
        if trains.count() > 1:
            print(f"Removing {trains.count() - 1} duplicates for Train No: {t_no}")
            for t in trains[1:]:
                t.delete()

    print("Cleanup complete!")

if __name__ == "__main__":
    cleanup()
