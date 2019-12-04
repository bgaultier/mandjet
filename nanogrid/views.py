from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Vehicle, TimeSlot

import json
from icalendar import Calendar, Event

class IndexView(generic.ListView):
    template_name = 'vehicles/dashboard.html'
    model = Vehicle

class TimeSlotCreateView(generic.CreateView):
    model = TimeSlot
    fields = ['start', 'end']
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle = get_object_or_404(Vehicle, pk=self.kwargs.get('vehicle_id'))
        context['vehicle'] = vehicle

        return context

    def form_valid(self, form):
        vehicle = get_object_or_404(Vehicle, pk=self.kwargs.get('vehicle_id'))
        form.instance.vehicle = vehicle
        form.instance.user = self.request.user

        messages.success(self.request, _(u"Your booking for %s is ok!") % vehicle)
        return super().form_valid(form)

class TimeSlotIndexView(generic.ListView):
    template_name = 'vehicles/calendar.html'
    model = TimeSlot

    def get_queryset(self):
        return TimeSlot.objects.order_by('-start')[:10]

class TimeSlotDeleteView(generic.DeleteView):
    model = TimeSlot
    success_url = '/'

@csrf_exempt
def battery_api_view(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    if request.method == 'POST':
        data = json.loads(request.body)
        if data.get('battery'):
            vehicle.battery = data.get('battery')
            vehicle.save()
    response={
        'id': vehicle.id,
        'battery': vehicle.battery,
    }
    return JsonResponse(response)

@csrf_exempt
def ics_api_view(request):
    timeslots = TimeSlot.objects.all()

    calendar = Calendar()
    calendar.add('prodid', '-//IMT Atlantique//NONSGML Mandjet vehicles calendar//EN')
    calendar.add('version', '2.0')

    for timeslot in timeslots:
        event = Event()
        event.add('summary', str(timeslot.vehicle) + ' - ' + timeslot.user.first_name)
        event.add('dtstart', timeslot.start)
        event.add('dtend', timeslot.end)
        event.add('dtstamp', timeslot.created_date)

        calendar.add_component(event)

    return HttpResponse(calendar.to_ical(), content_type='text/calendar')
