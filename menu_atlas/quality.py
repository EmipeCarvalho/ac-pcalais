import math
import pandas as pd
import great_expectations as gx
from .schema import Menu

REQUIRED = ["category", "name", "price", "currency"]

def validate_menu(raw: dict, max_price: float = 1000) -> dict:
    menu = Menu.model_validate(raw)
    rows = [i.model_dump() for i in menu.items]
    columns = ["category", "name", "description", "price", "currency", "attributes"]
    df = pd.DataFrame(rows, columns=columns)
    # Espaço em branco é missing. Não preenchemos com valores inventados.
    for col in ["category", "name", "currency"]:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) and x.strip() else None)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").astype(float)
    df["duplicate_key"] = df.apply(lambda r: "|".join(str(r[c]).casefold() for c in ["category", "name", "price", "currency"]), axis=1)
    checks = []
    if rows:
        context = gx.get_context(mode="ephemeral")
        source = context.data_sources.add_pandas(name="menu")
        asset = source.add_dataframe_asset(name="items")
        batch = asset.add_batch_definition_whole_dataframe("all").get_batch(batch_parameters={"dataframe": df})
        expectations = [gx.expectations.ExpectColumnValuesToNotBeNull(column=c) for c in REQUIRED]
        expectations += [
            gx.expectations.ExpectColumnValuesToBeBetween(column="price", min_value=0, strict_min=True, max_value=max_price),
            gx.expectations.ExpectColumnValuesToBeInSet(column="category", value_set=menu.categories),
            gx.expectations.ExpectColumnValuesToBeUnique(column="duplicate_key"),
            gx.expectations.ExpectColumnValueLengthsToBeBetween(column="name", min_value=2, max_value=250),
            gx.expectations.ExpectColumnValuesToMatchRegex(column="currency", regex=r"^[A-Z]{3}$"),
        ]
        for exp in expectations:
            result = batch.validate(exp).to_json_dict()
            checks.append({"rule": exp.__class__.__name__, "column": exp.column, "success": result["success"], "result": result["result"]})
    duplicate = df.duplicated("duplicate_key", keep=False).tolist()
    reviewed = []
    missing = int(df[REQUIRED].isna().sum().sum())
    reasonable = 0
    for idx, row in enumerate(df.to_dict("records")):
        issues = [f"missing:{c}" for c in REQUIRED if pd.isna(row[c])]
        price = row["price"]
        valid_price = not pd.isna(price) and math.isfinite(price) and 0 < price <= max_price
        reasonable += int(valid_price)
        if not pd.isna(price) and not valid_price:
            issues.append("price_out_of_range")
        if row["category"] not in menu.categories:
            issues.append("unknown_category")
        if duplicate[idx]:
            issues.append("possible_duplicate")
        if row["name"] is not None and not 2 <= len(row["name"]) <= 250:
            issues.append("name_length")
        if row["currency"] is not None and (len(row["currency"]) != 3 or not row["currency"].isascii() or not row["currency"].isupper() or not row["currency"].isalpha()):
            issues.append("currency_format")
        row.pop("duplicate_key")
        row["price"] = float(price) if not pd.isna(price) and math.isfinite(price) else None
        row["issues"] = issues
        row["status"] = "review" if issues else "valid"
        reviewed.append(row)
    n = len(rows)
    return {"items": reviewed, "checks": checks, "item_count": n,
            "missing_cells": missing, "required_cells": n * len(REQUIRED),
            "reasonable_prices": reasonable,
            "missing_pct": 100 * missing / (n * len(REQUIRED)) if n else None,
            "reasonable_price_pct": 100 * reasonable / n if n else None,
            "needs_review": not n or any(i["issues"] for i in reviewed) or any(not c["success"] for c in checks) or bool(menu.warnings),
            "max_price": max_price}
