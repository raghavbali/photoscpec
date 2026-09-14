# Printing at the intended size

1. Choose the physical photo dimensions, independent of the paper size.
2. Select the exact paper size loaded into the printer: 4 × 6, 5 × 7, 6 × 8 inches, A4, Letter or Custom.
3. Set copies, spacing and outer margins. Auto fit can rotate the page/photos. It never shrinks a photo to increase capacity.
4. Prefer PDF for printing. In the print dialog select **Actual Size / 100%**.
5. Disable **Fit to Page**, automatic scaling and borderless enlargement. Select the same paper size and orientation shown by PhotoScpec.
6. Print a trial and measure a photo edge with a ruler before using expensive photo paper.

Printer nonprintable margins vary. If edges/marks are clipped, increase margins in PhotoScpec and recalculate; do not fix clipping by scaling the page. Preview cutting marks belong only to sheets and never appear in the individual photo.

PDF uses 72 points per inch and 25.4 mm per inch. A 35 × 45 mm placement is 35/25.4×72 by 45/25.4×72 PDF points. Raster output stores DPI metadata but some software ignores it. If printing JPG/PNG, explicitly confirm paper size and 100% scaling.

Pixels are rounded consistently half-up: floor(positive value + 0.5). Thus 35 × 45 mm at 300 DPI becomes 413 × 531 px; 2 inches at 300 DPI is 600 px. Each raster edge is rounded from its absolute millimeter coordinate, avoiding accumulated spacing error. PDF physical geometry stays exact even when the underlying image resolution was rounded.

Copy count is independent of capacity. A page that holds eight with seven requested contains seven photos. Fixed grids are rows × columns and must fit in full, even if fewer copies are requested. Auto fit compares uniform grids; mixed portrait/landscape packing and multiple pages are intentionally excluded.

Insufficient-capacity errors mean choose fewer copies, reduce spacing/margins where your printer permits, or select larger paper. For example, eight 35 × 45 mm photos fit on a landscape 4 × 6 inch page with 3 mm margins and 2 mm spacing. The 4-column × 2-row grid occupies 146 × 92 mm inside 146.4 × 95.6 mm of usable page.
