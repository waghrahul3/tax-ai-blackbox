def get_extension(format_type):

    mapping = {
        "json": ".json",
        "csv": ".csv",
        "markdown": ".md",
        "table": ".md",
        "code": ".txt",
        "text": ".txt"
    }

    return mapping.get(format_type, ".txt")