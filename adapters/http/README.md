# Future HTTP adapter (not implemented)

A future FastAPI adapter can instantiate PhotoScpecService(config_dir=...) and map JSON/multipart inputs to the existing dataclasses. No crop, sizing, config, layout or export logic belongs in the adapter.

| HTTP route | Service |
| --- | --- |
| GET /api/v1/specs | list_specs |
| GET /api/v1/specs/{id} | get_spec |
| POST /api/v1/dimensions/resolve | resolve_dimensions |
| POST /api/v1/images/inspect | inspect_image |
| POST /api/v1/photos/frame | calculate_crop |
| POST /api/v1/photos/crop | create_crop |
| POST /api/v1/photos/guides | get_guides |
| POST /api/v1/photos/validate | validate_photo |
| POST /api/v1/layouts/calculate | calculate_layout |
| POST /api/v1/export/photo | export_photo |
| POST /api/v1/export/sheet | export_sheet |

Use multipart file bytes for images and a JSON part for metadata. Reconstruct nested dataclasses such as CropRect/LayoutRequest explicitly. Return image/PDF bytes using ExportResult.mime_type and filename. Dataclass metadata serializes with dataclasses.asdict; bytes require multipart/binary or explicit base64, not implicit JSON encoding. Convert PhotoScpecError to {code,message,details}, with appropriate HTTP 400/404/413/422 responses.

Keep request-size limits and local binding. A future remotely accessible deployment needs its own authentication and privacy design; the MVP includes no HTTP server.
