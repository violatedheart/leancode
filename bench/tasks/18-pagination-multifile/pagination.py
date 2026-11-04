def paginate(items, page_size, cursor=None):
    offset = int(cursor or 1)
    page = items[offset:offset + page_size + 1]
    next_cursor = str(offset + page_size) if len(page) > page_size else None
    return page[:page_size], next_cursor
