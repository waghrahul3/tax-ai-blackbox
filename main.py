import os

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from api.routes import router

app = FastAPI(
    title="LangChain Multi Document Engine",
    openapi_version="3.0.3"
)

app.include_router(router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        routes=app.routes
    )

    for _, methods in openapi_schema.get("paths", {}).items():
        for _, operation in methods.items():
            request_body = operation.get("requestBody", {})
            content = request_body.get("content", {})
            multipart = content.get("multipart/form-data", {})
            schema = multipart.get("schema", {})

            if "$ref" not in schema:
                continue

            ref = schema["$ref"].split("/")[-1]
            component = openapi_schema.get("components", {}).get("schemas", {}).get(ref, {})
            properties = component.get("properties", {})

            for _, prop in properties.items():
                if prop.get("type") != "array":
                    continue

                items = prop.get("items", {})
                if items.get("type") == "string" and "contentMediaType" in items:
                    items["format"] = "binary"
                    items.pop("contentMediaType", None)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/ui")
def chatbot_ui():
    page_path = os.path.join("frontend", "chatbot.html")
    return FileResponse(page_path, media_type="text/html")


@app.get("/")
def health():
    return {"status": "running"}