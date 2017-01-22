from rest_framework.test import APIRequestFactory, force_authenticate, APITestCase
from django.contrib.auth.models import User
from analysis.models import Analysis
from genomes.models import Genome
from rest_framework.reverse import reverse
from analysis.views import AnalysisListView, AnalysisRunView
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest import mock

# Create your tests here.


class ListAnalysisTestCase(APITestCase):
    test_username = "test_user"
    test_user = None

    test_celery_task_id = "1"
    test_name = "test_analysis"
    test_genomes = None
    test_submit_time = timezone.now()
    test_analysis = None

    def setUp(self):
        self.factory = APIRequestFactory()

        self.test_user = User(username=self.test_username)
        self.test_user.save()

        self.test_analysis = Analysis(celery_task_id=self.test_celery_task_id,
                                      name=self.test_name,
                                      submit_time=self.test_submit_time,
                                      owner=self.test_user)
        self.test_analysis.save()

    def test_authenticated_list_analysis(self):
        url = reverse('analysis')

        request = self.factory.get(url)
        force_authenticate(request, self.test_user)
        response = AnalysisListView.as_view()(request)

        self.assertEqual(200, response.status_code)
        self.assertEqual(self.test_analysis.id, response.data[0]['id'])
        self.assertEqual(self.test_name, response.data[0]['name'])
        self.assertEqual(self.test_submit_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'), response.data[0]['submit_time'])

    def test_unauthenticated_list_analysis(self):
        url = reverse('analysis')

        request = self.factory.get(url)
        response = AnalysisListView.as_view()(request)

        self.assertEqual(403, response.status_code)


class RetrieveAnalysisTestCase(APITestCase):
    test_username = "test_user"
    test_user = None

    test_celery_task_id = "1"
    test_name = "test_analysis"
    test_genomes = None
    test_submit_time = timezone.now()
    test_analysis = None

    def setUp(self):
        self.factory = APIRequestFactory()

        self.test_user = User(username=self.test_username)
        self.test_user.save()

        self.test_analysis = Analysis(celery_task_id=self.test_celery_task_id,
                                      name=self.test_name,
                                      submit_time=self.test_submit_time,
                                      owner=self.test_user)
        self.test_analysis.save()

    def test_authenticated_retrieve_analysis(self):
        url = reverse('analysis_details', kwargs={'pk': self.test_analysis.id})

        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertEqual(self.test_name, response.data['name'])
        self.assertEqual(self.test_submit_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'), response.data['submit_time'])

    def test_unauthenticated_retrieve_analysis(self):
        url = reverse('analysis_details', kwargs={'pk': self.test_analysis.id})

        response = self.client.get(url)

        self.assertEqual(403, response.status_code)

    def test_incorrect_user_retrieve_analysis(self):
        url = reverse('analysis_details', kwargs={'pk': self.test_analysis.id})

        incorrect_user = User(username="incorrect_user")
        incorrect_user.save()

        self.client.force_authenticate(user=incorrect_user)
        response = self.client.get(url)

        self.assertEqual(404, response.status_code)

    def test_retrieve_analysis_does_not_exist(self):
        url = reverse('analysis_details', kwargs={'pk': self.test_analysis.id+1})

        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(url)

        self.assertEqual(404, response.status_code)


class UpdateAnalysisTestCase(APITestCase):
    test_username = "test_user"
    test_user = None

    test_celery_task_id = "1"
    test_name = "test_analysis"
    test_genomes = None
    test_submit_time = timezone.now()
    test_analysis = None

    def setUp(self):
        self.factory = APIRequestFactory()

        self.test_user = User(username=self.test_username)
        self.test_user.save()

        self.test_analysis = Analysis(celery_task_id=self.test_celery_task_id,
                                      name=self.test_name,
                                      submit_time=self.test_submit_time,
                                      owner=self.test_user)
        self.test_analysis.save()

    def test_authenticated_update_analysis(self):
        updated_name = "updated_name"

        url = reverse('analysis_details', kwargs={'pk': self.test_analysis.id})

        self.client.force_authenticate(user=self.test_user)
        response = self.client.put(url,
                                   {'name': updated_name})

        updated_analysis = Analysis.objects.get(id=self.test_analysis.id)

        self.assertEqual(200, response.status_code)
        self.assertEqual(updated_name, updated_analysis.name)

    def test_unauthenticated_update_analysis(self):
        updated_name = "updated_name"

        url = reverse('analysis_details', kwargs={'pk': self.test_analysis.id})

        response = self.client.put(url,
                                   {'name': updated_name})

        updated_analysis = Analysis.objects.get(id=self.test_analysis.id)

        self.assertEqual(403, response.status_code)
        self.assertEqual(self.test_name, updated_analysis.name)


class RunAnalysisTestCase(APITestCase):
    test_username = "test_user"
    test_user = None

    test_analysis_name = "test_analysis"

    test_genome_1 = None
    test_genome_1_name = "genome_1"
    test_genome_1_gbk_name = "test.gbk"
    test_genome_1_gbk_contents = bytes("test", 'utf-8')
    test_genome_1_gbk = SimpleUploadedFile(test_genome_1_gbk_name, test_genome_1_gbk_contents)

    test_genome_2 = None
    test_genome_2_name = "genome_2"
    test_genome_2_gbk_name = "test_2.gbk"
    test_genome_2_gbk_contents = bytes("test2", 'utf-8')
    test_genome_2_gbk = SimpleUploadedFile(test_genome_1_gbk_name, test_genome_1_gbk_contents)

    def setUp(self):
        self.factory = APIRequestFactory()

        self.test_user = User(username=self.test_username)
        self.test_user.save()

        self.test_genome_1 = Genome.objects.create(name=self.test_genome_1_name,
                                                   owner=self.test_user,
                                                   gbk=self.test_genome_1_gbk)

        self.test_genome_2 = Genome.objects.create(name=self.test_genome_2_name,
                                                   owner=self.test_user,
                                                   gbk=self.test_genome_2_gbk)

    def test_authenticated_run_analysis(self):
        url = reverse('analysis_run')

        request = self.factory.post(url,
                                    {'name': self.test_analysis_name,
                                     'genomes': [self.test_genome_1.id, self.test_genome_2.id]})
        force_authenticate(request, self.test_user)

        run_pipeline_callback = mock.MagicMock()
        response = AnalysisRunView.as_view(run_pipeline_callback=run_pipeline_callback)(request)

        self.assertEqual(200, response.status_code)
        self.assertTrue(Analysis.objects.filter(id=response.data['id']).exists())

        analysis = Analysis.objects.get(id=response.data['id'])
        self.assertEqual(self.test_analysis_name, analysis.name)
        self.assertTrue(analysis.genomes.filter(id=self.test_genome_1.id).exists())
        self.assertTrue(analysis.genomes.filter(id=self.test_genome_2.id).exists())

        run_pipeline_callback.assert_called_once()

    def test_incorrect_owner_run_analysis(self):
        url = reverse('analysis_run')

        incorrect_user = User(username="incorrect_user")
        incorrect_user.save()

        request = self.factory.post(url,
                                    {'genomes': [self.test_genome_1.id, self.test_genome_2.id]})
        force_authenticate(request, incorrect_user)

        response = AnalysisRunView.as_view()(request)

        self.assertEqual(400, response.status_code)

    def test_only_1_genome_run_analysis(self):
        url = reverse('analysis_run')

        request = self.factory.post(url,
                                    {'genomes': [self.test_genome_1.id]})
        force_authenticate(request, self.test_user)

        response = AnalysisRunView.as_view()(request)

        self.assertEqual(400, response.status_code)

    def test_unauthenticated_run_analysis(self):
        url = reverse('analysis_run')

        request = self.factory.post(url,
                                    {'genomes': [self.test_genome_1.id, self.test_genome_2.id]})

        response = AnalysisRunView.as_view()(request)

        self.assertEqual(403, response.status_code)

    def tearDown(self):
        for genome in Genome.objects.all():
            genome.delete()
