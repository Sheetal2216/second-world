from pypdf import PdfReader


def parse_pdf(file_path: str) -> dict:
    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    full_text = "\n".join(pages)

    return {
        "text": full_text,
        "page_count": len(reader.pages),
        "character_count": len(full_text),
    }