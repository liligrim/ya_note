from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestNoteList(TestCase):
    NOTE_LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = User.objects.create(username='Создатель')
        cls.notes = Note.objects.create(
            author=cls.author,
            text='Текст заметки',
            title='Заголовок'
        )
        cls.reader = User.objects.create(username='Не автор заметки')
        cls.url = reverse('notes:list')
        cls.detail_url = reverse('notes:add')

    def test_note_list(self):
        self.client.force_login(self.author)
        response = self.client.get(self.NOTE_LIST_URL)
        object_list = response.context['object_list']
        count_note = len(object_list)
        self.assertEqual(count_note, 1)

    def test_note_list_for_another_user(self):
        self.client.force_login(self.reader)
        response = self.client.get(self.NOTE_LIST_URL)
        object_list = response.context['object_list']
        count_note = len(object_list)
        self.assertEqual(count_note, 0)

    def test_authorized_client_has_form(self):
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertIn('form', response.context)