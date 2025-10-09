from news.models import Category


def get_category_and_descendants_ids(category_id):
    try:
        root = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return []

    ids = [root.id]

    def collect_descendants(category):
        for category_set in category.category_set.all():
            ids.append(category_set.id)
            collect_descendants(category_set)

    collect_descendants(root)
    return ids
