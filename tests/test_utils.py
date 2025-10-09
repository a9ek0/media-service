from django.test import TestCase
from news.models import Category
from news.utils import get_category_and_descendants_ids


class CategoryUtilsLogicTest(TestCase):
    """Тесты логики кастомных утилит"""

    def test_category_descendants_logic(self):
        """Тест логики получения всех потомков категории"""
        root = Category.objects.create(name="Root", slug="root")
        child1 = Category.objects.create(name="Child1", slug="child1", parent=root)
        child2 = Category.objects.create(name="Child2", slug="child2", parent=root)
        grandchild = Category.objects.create(name="Grandchild", slug="grandchild", parent=child1)

        result_ids = get_category_and_descendants_ids(root.id)
        expected_ids = {root.id, child1.id, child2.id, grandchild.id}

        self.assertEqual(set(result_ids), expected_ids)
