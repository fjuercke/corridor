# Running the Corridor Network Workflow in the GRASS GUI

This guide describes how to perform the steps in `_archaeology_corridor_network.py` using the GRASS GIS graphical interface.

## 1) Prepare a Location and Mapset
1. Start GRASS GIS and select (or create) the GIS database (`$GISDBASE`), location, and mapset that will contain your corridor data.
2. Ensure the location projection matches the corridor rasters you will import.

## 2) Import Corridor Rasters
⚠︎ Skip this step if the corridor rasters are already in the current mapset.

1. Open **File ▸ Import Raster Data ▸ Common import formats (r.in.gdal)**.
2. For each corridor GeoTIFF, set **Source input** to the file path and choose an **Output raster map name**.
3. Check **Extend current region to match new dataset** to align the default region to the first import.
4. Repeat for all corridor rasters that should be part of the network.

## 3) Review Available Rasters
1. In the **Layer Manager**, expand **Raster Map List** to confirm all corridor rasters are present.
2. Optionally rename them so they share a common pattern (e.g., `corridor_XXXX_YYYY_costdist`).

## 4) Byte-Stretch Each Raster to 1–255
For every corridor raster:
1. Set the computational region to the raster via **Settings ▸ Region ▸ Set region** and select the raster in **Match region to raster**.
2. Compute statistics with **Raster ▸ Reports and statistics ▸ Basic raster metadata (r.univar)**; note the **minimum** and **maximum** values.
3. Open **Raster ▸ Map algebra ▸ Simple calculator (r.mapcalc)** and enter an expression using the min/max values:
   ```
   <output_name> = (<input_raster> - <min>) * (255 - 1) / (<max> - <min>) + 1
   ```
   A possible output name pattern could be: input_raster_stretch_1255
4. Run the command and verify the new raster appears in the map list (e.g., `corridor_XXXX_YYYY_costdist_stretch_1255`).

## 5) Combine Stretched Rasters Using the Minimum
1. In **Raster ▸ Map algebra ▸ Simple calculator (r.mapcalc)**, use the `nmin()` function with all stretched rasters separated by commas:
   ```
   corridors_mid4th_wY_minjoined = nmin(raster1_stretch_1255, raster2_stretch_1255, ...)
   ```
2. Execute to create a merged corridor raster that keeps the lowest cost cell at each position.

## 6) Prepare the Output for Export
For smaller file size round the output network raster to integer values:
1. In **Raster ▸ Map algebra ▸ Simple calculator (r.mapcalc)**, multiply the merged raster by 100:
   ```
   corridors_mid4th_wY_minjoined_mult100 = corridors_mid4th_wY_minjoined * 100
   ```
2. Run another **r.mapcalc** to round the result to integers:
   ```
   corridors_mid4th_wY_minjoined_mult100_rounded = round(corridors_mid4th_wY_minjoined_mult100)
   ```

## 7) Export to GeoTIFF
1. Open **File ▸ Export Raster Map ▸ Common export formats (r.out.gdal)**.
2. Choose the rounded raster as **Input raster** and set **Output file** to a `.tif` path.
3. Set **Format** to `GTiff` and **Output type** to `Int16`.
4. Enable **Force output to specific data type** and run the export.

## 8) Clean Up and Validate
- Note the computation times in the **Console** tab for each step.
- Open the GeoTIFF in QGIS to confirm the output looks correct.

Following these steps reproduces the automated workflow of `_archaeology_corridor_network.py` entirely within the GRASS GUI.
