from inertia import render as render_inertia
from django.views import View

def index(request):
    return render_inertia(request, "Home")

class HomeView(View):
    def get(self, request):
        return render_inertia(request, "home/feeds/Feeds")
