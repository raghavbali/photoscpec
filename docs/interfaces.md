# Public interfaces

Import PhotoScpecService from photoscpec.services.photoscpec_service. Request/response dataclasses live in photoscpec.interfaces.models; PhotoScpecError lives in photoscpec.interfaces.errors. PhotoSpec lives in photoscpec.config.models.

Construct PhotoScpecService(config_dir=None) to load the checkout's configs directory, or pass an explicit directory. config_errors is a list of loading diagnostics. The constructor does not hold uploaded images. list_specs/get_spec return config data, not government-specific behavior.

## Types and units

- DimensionsRequest(width, height, unit="mm", dpi=300) → DimensionsResult(width_mm, height_mm, width_px, height_px, dpi).
- ImageInfo(width_px, height_px, format, orientation, aspect_ratio) describes the EXIF-normalized source. All byte operations accept JPG/PNG.
- CropRect(x,y,width,height) uses normalized 0–1 coordinates of the image **after EXIF transpose and requested rotation**; origin top-left; x+width and y+height cannot exceed 1.
- CropFrameRequest(image,output_width_px,output_height_px,zoom=1,pan_x=.5,pan_y=.5,rotation_degrees=0). Pan spans available travel; center .5. Quarter turns are clockwise.
- CropRequest(image,crop,output_width_px,output_height_px,rotation_degrees=0) → CropResult(image,width_px,height_px,warnings). image is clean PNG bytes.
- GuideRequest(spec_id=None) → GuideResult(guides). Each Guide has type/id and either position for horizontal/vertical lines or x/y/width/height for a box, all normalized top-left.
- ValidationRequest(image,width_px,height_px) → ValidationResult(valid,warnings). Checks basic output dimensions/decodability; no facial or government certification.
- LayoutRequest(photo_width_mm,photo_height_mm,paper_width_mm,paper_height_mm,copies,spacing_mm=2,margin_mm=3,layout_mode="auto",orientation=None,rows=None,columns=None,allow_rotate=True).
- LayoutResult(rows,columns,capacity,copies_rendered,orientation,paper_width_mm,paper_height_mm,positions,warnings). PhotoPlacement(x_mm,y_mm,width_mm,height_mm,rotated) uses page top-left, with clockwise 90° image rotation when rotated.
- PhotoExportRequest(image,format="PNG",dpi=300) exports supplied image pixels without resizing.
- SheetExportRequest(image,layout,format="PDF",dpi=300,cutting_guides=False) recalculates authoritative layout rather than trusting arbitrary placements.
- ExportResult(data,mime_type,filename) contains bytes ready for download.

Physical units are millimeters internally. Unit aliases are mm/inch/in/px. Conversion uses 25.4 mm/inch and nearest-pixel half-up rounding. Pixel dimensions must be positive. Printing preserves physical geometry; tiny raster rounding differences are unavoidable. Errors reject malformed or excessive inputs instead of allocating unbounded images.

## Method contracts

The examples below use `svc = PhotoScpecService()`, `source` as JPG/PNG bytes, `dims` as a DimensionsResult, `photo` as CropResult and `page` as LayoutRequest.

| Method | Inputs and validation | Output / units | Errors | Example |
| --- | --- | --- | --- | --- |
| list_specs | None; validated startup catalog | list[PhotoSpec], dimensions mm | Loading diagnostics in config_errors | svc.list_specs() |
| get_spec | Known unique string ID | PhotoSpec, dimensions mm | SPEC_NOT_FOUND | svc.get_spec("india_birth_registration") |
| resolve_dimensions | DimensionsRequest; finite positive width/height, valid unit and integer DPI | DimensionsResult, mm and px | INVALID_DIMENSIONS, INVALID_DPI | svc.resolve_dimensions(DimensionsRequest(35,45,"mm",300)) |
| inspect_image | Nonempty bounded image bytes; valid JPG/PNG | ImageInfo, source px after EXIF transpose | UNSUPPORTED_IMAGE | svc.inspect_image(source) |
| calculate_crop | CropFrameRequest; zoom≥1, pan 0–1, valid output and quarter-turn rotation | CropRect, normalized coordinates after rotation | INVALID_CROP, INVALID_DIMENSIONS, UNSUPPORTED_IMAGE | svc.calculate_crop(CropFrameRequest(source,413,531,zoom=1.2)) |
| create_crop | CropRequest; finite in-bounds normalized rectangle with matching target ratio | CropResult, PNG bytes and exact output px; upscaling warnings | INVALID_CROP, INVALID_DIMENSIONS, UNSUPPORTED_IMAGE | svc.create_crop(CropRequest(source,frame,413,531)) |
| get_guides | GuideRequest; existing ID or None for generic visual aids | GuideResult, normalized guide data | SPEC_NOT_FOUND | svc.get_guides(GuideRequest("india_birth_registration")) |
| validate_photo | ValidationRequest; valid expected pixel dimensions and decodable image | ValidationResult, exact-size checks and warnings | INVALID_DIMENSIONS, UNSUPPORTED_IMAGE | svc.validate_photo(ValidationRequest(photo.image,413,531)) |
| calculate_layout | LayoutRequest; finite positive sizes/copies, nonnegative spacing/margins; auto or grid mode; positive rows/columns for grid | LayoutResult, physical mm; exact copy count | INVALID_DIMENSIONS, LAYOUT_DOES_NOT_FIT | svc.calculate_layout(LayoutRequest(35,45,210,297,7)) |
| export_photo | PhotoExportRequest; decodable image, PNG/JPG/JPEG and valid DPI | ExportResult; existing px plus DPI metadata | UNSUPPORTED_IMAGE, INVALID_DPI, EXPORT_FAILED | svc.export_photo(PhotoExportRequest(photo.image,"JPG",300)) |
| export_sheet | SheetExportRequest; image ratio matches physical photo within rounding tolerance, valid layout/DPI, PNG/JPG/PDF | ExportResult; exact PDF geometry or rounded raster geometry | Layout/image errors, INVALID_DPI, EXPORT_FAILED | svc.export_sheet(SheetExportRequest(photo.image,page,"PDF")) |

orientation is None (auto), portrait or landscape. In grid mode rows/columns define the complete grid and it must fit. copies defines how many positions are emitted. Auto compares both paper orientations and uniform photo rotations; ties prefer unrotated photos and portrait paper. No mixed packing or silent scaling.

## End-to-end example

```python
from photoscpec.services.photoscpec_service import PhotoScpecService
from photoscpec.interfaces.models import (
    DimensionsRequest, CropFrameRequest, CropRequest, LayoutRequest, SheetExportRequest,
)
svc = PhotoScpecService()
with open("portrait.jpg", "rb") as handle:
    source = handle.read()
dims = svc.resolve_dimensions(DimensionsRequest(35, 45, "mm", 300))
frame = svc.calculate_crop(CropFrameRequest(source, dims.width_px, dims.height_px))
photo = svc.create_crop(CropRequest(source, frame, dims.width_px, dims.height_px))
page = LayoutRequest(35, 45, 210, 297, copies=7)
result = svc.export_sheet(SheetExportRequest(photo.image, page, "PDF", 300, True))
with open(result.filename, "wb") as handle:
    handle.write(result.data)
```

This example explicitly saves at the caller's request; the service itself does not write photos.

## Errors and serialization

PhotoScpecError is an Exception dataclass: code, message, details. Catch it and decide presentation in the adapter. LAYOUT_DOES_NOT_FIT details include requested copies and maximum_capacity; offer fewer copies, smaller margins/spacing or larger paper. INVALID_CONFIG is reserved for future strict config APIs; current catalog loading exposes per-entry diagnostics and keeps valid formats.

Use dataclasses.asdict for metadata JSON. Dataclass type hints are not a general HTTP schema validator: an HTTP adapter must validate JSON types and construct nested dataclasses. bytes are not JSON-serializable; use binary/multipart transport or explicitly base64-encode. No PIL or Streamlit objects cross the interface. See adapters/http/README.md.

FaceAnalyzer is an optional protocol in core/face_analysis.py; NoOpFaceAnalyzer returns no detection. The MVP does not load a facial model. Optional config face/background metadata is descriptive, not validated against the pixels.
