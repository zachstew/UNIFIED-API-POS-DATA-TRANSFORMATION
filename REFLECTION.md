# Unified API POS Data Transformation Reflection

I built a two-part system, one being a fake Trillionaire source API that serves items as JSON and orders as SOAP/XML, and a unified ETL pipeline that ingests both, transforms them, and stores them in SQLite behind its own REST API. The main change was in the transformation step: the source sends `sku_id` as an integer. I changed the model column to a String and prefixed each value with "SPTBG-" in `normalize_item` and `normalize_order`, leaving the source untouched.

What surprised me was how small the code change was compared with how many pieces had to agree, and that I had to delete `etl_staging.db` because the old schema kept the integer column. For orders, I converted the XML text to an int before adding the prefix, which cleaned the data.

Curl results: the trigger returned a success message, and both the items (100 records) and orders (100 records) endpoints returned values like `"sku_id":"SPTBG-1"`, with every record verified as prefixed. I want to learn more about handling ID collisions across multiple sources.