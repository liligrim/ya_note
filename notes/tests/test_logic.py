from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()
WARNING_FOR_SLUG = 'Убедитесь, что это значение содержит не более 100 символов'


class TestNoteCreation(TestCase):
    SLUG_TEXT = 'zagolovok-zametki'
    TITLE_TEXT = 'Заголовок заметки'
    TEXT_TEXT = 'Какой-то текст заметки'

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create(username='Автор')
        cls.url_add = reverse('notes:add')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.url = reverse('notes:add')
        cls.url_redirect = reverse('notes:success')
        cls.form_data = {
            'title': cls.TITLE_TEXT,
            'text': cls.TEXT_TEXT,
            # 'slug': cls.SLUG_TEXT,
        }

    def test_user_can_create_note_and_create_with_empty_slug(self):
        """Проверка на создание заметки и присвоение ей имени заголовка, если нет слага"""
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.url_redirect)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.text, self.TEXT_TEXT)
        self.assertEqual(note.slug, self.SLUG_TEXT)
        self.assertEqual(note.title, self.TITLE_TEXT)


class TestNoteEditDelete(TestCase):
    SLUG_TEXT = 'zagolovok'
    NEW_SLUG = 'novyi-zagolovok'
    NEW_TITLE_TEXT = 'Новый заголовок заметки'
    NEW_NOTE_TEXT = 'Какой-то новый текст заметки'
    SLUG_MORE_THAN_100_SYMBOLS = ('zagolovok-zametki-bolee-chem-100-simvolov-'
                                  'sozdannyj-polzovatelem-dlya-proverki-'
                                  'korrektnosti-vvoda-i-vyvoda-informacii')

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.notes = Note.objects.create(
            author=cls.author,
            text='Текст заметки',
            title='Заголовок',
            slug=cls.SLUG_TEXT,
        )

        cls.reader = User.objects.create(username='Не автор заметки')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.edit_url = reverse('notes:edit', args=(cls.notes.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.notes.slug,))
        cls.form_data = {
            'text': cls.NEW_NOTE_TEXT,
            'title': cls.NEW_TITLE_TEXT,
            'slug': cls.NEW_SLUG,
        }
        cls.list_url = reverse('notes:list')
        cls.url_success = reverse('notes:success')
        cls.url_add = reverse('notes:add')

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.url_success)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.url_success)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.slug, self.SLUG_TEXT)

    def test_user_cant_use_no_unique_slug(self):
        new_note = {'slug': self.SLUG_TEXT}
        response = self.author_client.post(self.url_add, data=new_note)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f'{self.SLUG_TEXT}{WARNING}'
        )
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)

    def test_slug_max_length(self):
        new_note = {'slug': self.SLUG_MORE_THAN_100_SYMBOLS}
        response = self.author_client.post(self.url_add, data=new_note)
        length_for_slug = len(self.SLUG_MORE_THAN_100_SYMBOLS)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f'{WARNING_FOR_SLUG} (сейчас {length_for_slug}).'
        )
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
