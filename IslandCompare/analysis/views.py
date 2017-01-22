from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from analysis.serializers import AnalysisSerializer, RunAnalysisSerializer
from analysis.models import Analysis
from rest_framework.response import Response
from analysis.pipeline import Pipeline, PipelineSerializer
from analysis.tasks import run_pipeline_wrapper

# Create your views here.


class AnalysisListView(generics.ListAPIView):
    """
    List Analyses
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AnalysisSerializer

    def get_queryset(self):
        return Analysis.objects.filter(owner=self.request.user)


class AnalysisRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or Update Analysis
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AnalysisSerializer

    def get_queryset(self):
        return Analysis.objects.filter(owner=self.request.user)


class AnalysisRunView(APIView):
    """
    Run an Analysis
    """
    permission_classes = [IsAuthenticated]
    run_pipeline_callback = run_pipeline_wrapper

    def post(self, request):
        serializer = RunAnalysisSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        pipeline = Pipeline()
        pipeline.create_database_entry(name=serializer.validated_data['name'],
                                       genomes=serializer.validated_data['genomes'],
                                       owner=self.request.user)

        self.run_pipeline_callback(PipelineSerializer.serialize(pipeline))

        analysis_serializer = AnalysisSerializer(pipeline.analysis)
        return Response(analysis_serializer.data)
