"""Тестирование (pytest) логики проекта yanote."""

from http import HTTPStatus
import pytest
from pytest_django.asserts import assertRedirects, assertFormError
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING

# Страница редиректа:
REDIRECT_URL = reverse('notes:success')
# Страница создания заметки:
ADD_URL = reverse('notes:add')


def test_empty_slug(author_client, form_data):
    """Проверка генерации slug из title."""
    # Фиксируем в переменной, количество заметок до запроса:
    count_notes_before = Note.objects.count()
    # Убираем поле slug из словаря:
    form_data.pop('slug')
    # POST запрос на создание заметки без slug:
    response = author_client.post(ADD_URL, data=form_data)
    # Проверяем, что даже без slug заметка была создана.
    # Проверяем, что был выполнен редирект на страницу 'успешно':
    assertRedirects(response, REDIRECT_URL)
    # Получаем количество заметок из БД после запроса:
    count_notes_after = Note.objects.count()
    # Проверяем количество заметок:
    assert count_notes_before != count_notes_after
    # Получаем созданную заметку из базы:
    new_note = Note.objects.get()
    # Формируем ожидаемый slug:
    expected_slug = slugify(form_data['title'])
    # Проверяем, что slug заметки соответствует ожидаемому:
    assert new_note.slug == expected_slug


# Вызываем фикстуру отдельной заметки, чтобы в базе появилась запись.
def test_not_unique_slug(author_client, note, form_data):
    """Проверка уникальности slug."""
    # Фиксируем в переменной, количество заметок до запроса:
    count_notes_before = Note.objects.count()
    # Подменяем slug новой заметки на slug уже существующей записи:
    form_data['slug'] = note.slug
    # Пытаемся создать новую заметку:
    response = author_client.post(ADD_URL, data=form_data)
    # Проверяем, что в ответе содержится ошибка формы для поля slug:
    assertFormError(response.context['form'], 'slug',
                    errors=(note.slug + WARNING))
    # Получаем количество заметок из БД после запроса:
    count_notes_after = Note.objects.count()
    # Убеждаемся, что заметка не создана:
    assert count_notes_before == count_notes_after


def test_user_can_create_note(author_client, author, form_data):
    """Авторизованный пользователь может создавать заметку."""
    # Фиксируем в переменной, количество заметок до запроса:
    count_notes_before = Note.objects.count()
    # В POST-запросе отправляем данные, полученные из фикстуры form_data:
    response = author_client.post(ADD_URL, data=form_data)
    # Проверяем, что был выполнен редирект на страницу 'успешно':
    assertRedirects(response, REDIRECT_URL)
    # Получаем количество заметок из БД после запроса:
    note_count_after = Note.objects.count()
    # Убеждаемся, что заметка создана:
    assert count_notes_before != note_count_after
    # Получаем объект заметки из БД:
    new_note = Note.objects.get()
    # Сверяем атрибуты объекта с ожидаемыми.
    assert new_note.title == form_data['title']
    assert new_note.text == form_data['text']
    assert new_note.slug == form_data['slug']
    assert new_note.author == author


@pytest.mark.django_db
def test_anonymous_user_cant_create_note(client, form_data):
    """Анонимный пользователь не может создавать заметку."""
    # Фиксируем в переменной, количество заметок до запроса:
    count_notes_before = Note.objects.count()
    # Через анонимного клиента пытаемся создать заметку:
    response = client.post(ADD_URL, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={ADD_URL}'
    # Проверяем, что редирект привёл к странице логина:
    assertRedirects(response, expected_url)
    # Получаем количество заметок из БД после запроса:
    note_count_after = Note.objects.count()
    # Убеждаемся, что заметка не создана:
    assert count_notes_before == note_count_after


# В параметрах вызвана фикстура note: значит, в БД создана заметка.
def test_author_can_edit_note(author_client, form_data, note):
    """Автор может редактировать свою заметку."""
    # Страница редактирования заметки:
    url = reverse('notes:edit', args=(note.slug,))
    # Выполняем POST запрос на редактирование от имени автора заметки:
    response = author_client.post(url, form_data)
    # Проверяем, что был выполнен редирект на страницу 'успешно':
    assertRedirects(response, REDIRECT_URL)
    # Обновляем объект заметки note: получаем обновлённые данные из БД:
    note.refresh_from_db()
    # Проверяем, что атрибуты заметки соответствуют обновлённым:
    assert note.title == form_data['title']
    assert note.text == form_data['text']
    assert note.slug == form_data['slug']


def test_other_user_cant_edit_note(not_author_client, form_data, note):
    """Пользователь не может редактировать заметку другого автора."""
    # Страница редактирования заметки:
    url = reverse('notes:edit', args=(note.slug,))
    # Выполняем запрос на редактирование от имени другого пользователя.
    response = not_author_client.post(url, form_data)
    # Проверяем, что страница не найдена:
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Получаем объект запросом из БД:
    note_from_db = Note.objects.get(pk=note.pk)
    # Проверяем, что атрибуты объекта из БД и из фикстуры равны:
    assert note.title == note_from_db.title
    assert note.text == note_from_db.text
    assert note.slug == note_from_db.slug


def test_author_can_delete_note(author_client, slug_for_args):
    """Автор может удалить свою заметку."""
    # Страница удаления заметки:
    url = reverse('notes:delete', args=slug_for_args)
    # Фиксируем в переменной, количество заметок до запроса:
    count_notes_before = Note.objects.count()
    # От имени автора заметки отправляем DELETE-запрос на удаление:
    response = author_client.delete(url)
    # Проверяем, что был выполнен редирект на страницу 'успешно':
    assertRedirects(response, REDIRECT_URL)
    # Проверяем статус-код ответа:
    assert response.status_code == HTTPStatus.FOUND
    # Получаем количество заметок из БД после запроса:
    note_count_after = Note.objects.count()
    # Убеждаемся, что заметка удалена:
    assert count_notes_before != note_count_after


def test_other_user_cant_delete_note(not_author_client, slug_for_args):
    """Пользователь не может удалить заметку другого автора."""
    # Страница удаления заметки:
    url = reverse('notes:delete', args=slug_for_args)
    # Фиксируем в переменной, количество заметок до запроса:
    count_notes_before = Note.objects.count()
    # От имени не автора заметки отправляем DELETE-запрос на удаление:
    response = not_author_client.post(url)
    # Проверяем статус-код ответа:
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Получаем количество заметок из БД после запроса:
    note_count_after = Note.objects.count()
    # Убеждаемся, что заметка не удалена:
    assert count_notes_before == note_count_after
