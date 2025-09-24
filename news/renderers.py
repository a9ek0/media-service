from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from .models import MediaAsset

ALLOWED_BLOCKS = {
    "paragraph", "header", "heading", "image", "quote", "embed", "list", 
    "linkbutton", "table", "checklist", "code", "attaches"
}


def render_block(block):
    block_type = block.get("type")
    data = block.get("data", {})

    if block_type not in ALLOWED_BLOCKS:
        return ""

    if block_type == "paragraph":
        return render_to_string("news/blocks/paragraph.html", {"text": data.get("text", "")})

    if block_type in ["heading", "header"]:
        return render_to_string("news/blocks/heading.html", {
            "text": data.get("text", ""), 
            "level": data.get("level", 2)
        })

    if block_type == "image":
        media_id = data.get("media_id")
        file_data = data.get("file", {})
        file_url = file_data.get("url") if isinstance(file_data, dict) else data.get("file")

        if media_id:
            try:
                media = MediaAsset.objects.get(pk=media_id)
                image_url = media.file.url
                alt_text = data.get("alt") or media.alt or ""
            except MediaAsset.DoesNotExist:
                return render_to_string("news/blocks/missing_image.html", {})
        elif file_url:
            image_url = file_url
            alt_text = data.get("alt", "")
        else:
            return ""

        context = {
            "url": image_url,
            "alt": alt_text,
            "caption": data.get("caption", ""),
            "css_class": data.get("class", ""),
            "size": data.get("size", "medium"),
            "stretched": data.get("stretched", False),
            "withBorder": data.get("withBorder", False),
            "withBackground": data.get("withBackground", False),
        }
        return render_to_string("news/blocks/image.html", context)

    if block_type == "quote":
        return render_to_string("news/blocks/quote.html", {
            "text": data.get("text", ""),
            "caption": data.get("caption", ""),
            "alignment": data.get("alignment", "left")
        })

    if block_type == "list":
        return render_to_string("news/blocks/list.html", {
            "items": data.get("items", []),
            "style": data.get("style", "unordered")
        })

    if block_type == "linkbutton":
        return render_to_string("news/blocks/linkbutton.html", {
            "link": data.get("link", ""),
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "color": data.get("color", "#ffffff"),
            "backgroundColor": data.get("backgroundColor", "#000000"),
            "borderColor": data.get("borderColor", "#000000")
        })

    if block_type == "table":
        return render_to_string("news/blocks/table.html", {
            "content": data.get("content", []),
            "withHeadings": data.get("withHeadings", False),
            "stretched": data.get("stretched", False)
        })

    if block_type == "checklist":
        return render_to_string("news/blocks/checklist.html", {
            "items": data.get("items", [])
        })

    if block_type == "code":
        return render_to_string("news/blocks/code.html", {
            "code": data.get("code", "")
        })

    if block_type == "attaches":
        file_data = data.get("file", {})
        return render_to_string("news/blocks/attaches.html", {
            "url": file_data.get("url", ""),
            "name": file_data.get("name", ""),
            "size": file_data.get("size", 0),
            "extension": file_data.get("extension", ""),
            "title": data.get("title", "")
        })

    return ""


def render_body_from_json(body_json):
    if not body_json:
        return ""

    if isinstance(body_json, dict) and "blocks" in body_json:
        blocks = body_json["blocks"]
    elif isinstance(body_json, list):
        blocks = body_json
    else:
        return ""

    parts = []
    for block in blocks:
        rendered_block = render_block(block)
        if rendered_block:
            parts.append(rendered_block)
    
    return mark_safe("\n".join(parts))