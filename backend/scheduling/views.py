import datetime

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai import generate_schedule
from .models import PointOfSale, Promoter, Schedule, ScheduledVisit
from .serializers import (
    PointOfSaleSerializer,
    PromoterSerializer,
    ScheduleCreateSerializer,
    ScheduledVisitSerializer,
    ScheduleSerializer,
)


class ScheduleListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ScheduleCreateSerializer
        return ScheduleSerializer

    def get_queryset(self):
        qs = Schedule.objects.select_related("created_by").order_by("-period_start")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        out = ScheduleSerializer(serializer.instance, context={"request": request})
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)


class ScheduleDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduleSerializer
    queryset = Schedule.objects.select_related("created_by")


class ScheduleVisitListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduledVisitSerializer

    def get_queryset(self):
        schedule = get_object_or_404(Schedule, pk=self.kwargs["pk"])
        return (
            ScheduledVisit.objects.filter(schedule=schedule)
            .select_related("pos", "promoter")
            .order_by("date", "start_time")
        )


class ScheduleGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not settings.OPENAI_API_KEY:
            return Response(
                {"error": "OPENAI_API_KEY is not configured on the server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        schedule = get_object_or_404(
            Schedule.objects.prefetch_related("included_pos", "included_promoters"),
            pk=pk,
        )

        optimization_goal = request.data.get(
            "optimization_goal", "sales * 10 + interviews"
        )
        user_prompt = request.data.get("user_prompt", "")

        try:
            result = generate_schedule(schedule, optimization_goal, user_prompt)
        except Exception as e:
            return Response(
                {"error": f"AI generation failed: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        pos_map = {p.id: p for p in schedule.included_pos.all()}
        promoter_map = {p.id: p for p in schedule.included_promoters.all()}

        schedule.visits.all().delete()

        created = []
        errors = []
        for v in result["visits"]:
            try:
                pos = pos_map.get(v.get("pos_id"))
                promoter = promoter_map.get(v.get("promoter_id"))
                if pos is None:
                    errors.append(f"Unknown pos_id {v.get('pos_id')} — visit skipped.")
                    continue
                date_obj = datetime.date.fromisoformat(v["date"])
                week_num = (date_obj - schedule.period_start).days // 7 + 1
                visit = ScheduledVisit.objects.create(
                    schedule=schedule,
                    pos=pos,
                    promoter=promoter,
                    date=date_obj,
                    start_time=v["start_time"],
                    end_time=v["end_time"],
                    programme_type=(promoter.programme_type if promoter else "Radical"),
                    week_label=f"W{week_num}",
                    comments=v.get("reason", ""),
                )
                created.append(visit)
            except Exception as e:
                errors.append(str(e))

        serializer = ScheduledVisitSerializer(created, many=True)
        return Response(
            {
                "summary": result["summary"],
                "visits": serializer.data,
                "usage": result["usage"],
                "errors": errors,
            },
            status=status.HTTP_200_OK,
        )


class PointOfSaleListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PointOfSaleSerializer
    queryset = PointOfSale.objects.filter(is_active=True).order_by("name")


class PromoterListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PromoterSerializer
    queryset = Promoter.objects.filter(is_active=True).order_by(
        "last_name", "first_name"
    )
