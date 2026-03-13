"""Тестирование (pytest) контента проекта yanote."""

import pytest
from pytest_lazyfixture import lazy_fixture as lf
from django.urls import reverse

from notes.forms import NoteForm


@pytest.mark.parametrize(
    # Задаём названия для параметров.
    'parametrized_client, note_in_list',
    (
        # Передаём фикстуры в параметры при помощи "ленивых фикстур".
        (lf('author_client'), True),
        (lf('not_author_client'), False),
    )
)
# Используем фикстуру заметки и параметры из декоратора.
def test_notes_list_for_different_users(
    note, parametrized_client, note_in_list
):
    """В списке отображаются только заметки автора и проверка контекста."""
    url = reverse('notes:list')
    # Выполняем запрос от имени параметризованного клиента.
    response = parametrized_client.get(url)
    object_list = response.context['object_list']
    # Проверяем истинность утверждения "заметка есть в списке".
    assert (note in object_list) is note_in_list


@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:add', None),
        ('notes:edit', lf('slug_for_args'))
    )
)
def test_pages_contains_form(author_client, name, args):
    """При создании и редактировании заметки автору передается форма."""
    # Формируем URL.
    url = reverse(name, args=args)
    # Запрашиваем нужную страницу.
    response = author_client.get(url)
    # Проверяем, есть ли объект формы в словаре контекста.
    assert 'form' in response.context
    # Проверяем, что объект формы относится к нужному классу.
    assert isinstance(response.context['form'], NoteForm)


def test_detail_note(author_client, slug_for_args, note):
    """Контекст на странице заметки."""
    # Сохраняем в переменную адрес страницы с заметкой.
    url = reverse('notes:detail', args=slug_for_args)
    # Загружаем страницу с заметкой.
    response = author_client.get(url)
    # Получаем объект из контекста.
    object = response.context['object']
    # Сравниваем объект с заметкой фикстуры.
    assert object == note


def test_delete_note(author_client, slug_for_args):
    """Автору передается контекст при удалении заметки."""
    # Сохраняем в переменную адрес страницы удаления заметки.
    url = reverse('notes:detail', args=slug_for_args)
    # Загружаем страницу с заметкой.
    response = author_client.get(url)
    # Проверяем, что контент передается.
    assert response.context


@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:add', None),
        ('notes:edit', lf('slug_for_args')),
        ('notes:detail', lf('slug_for_args')),
        ('notes:delete', lf('slug_for_args')),
        ('notes:list', None),
    ),
)
def test_anonymous_client_has_not_form(client, name, args):
    """Анонимному пользователю контекст не передается."""
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.context is None
