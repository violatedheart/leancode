from pagination import paginate


def list_items(items, page_size, cursor=None):
    page, next_cursor = paginate(items, page_size, cursor)
    return {"items": page, "next_cursor": next_cursor}
