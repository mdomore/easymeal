#!/usr/bin/env python3
"""
Assign suggested tags to meals from their name (heuristic).
Works on SQLite (default data/easymeal.db) or DATABASE_URL.
Usage: python3 scripts/apply_meal_tags.py
"""
import json
import os
import re
import sqlite3
import sys

DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "easymeal.db")


def get_db_path():
    url = os.getenv("DATABASE_URL", "")
    if url.strip().lower().startswith("sqlite"):
        path = url.split("sqlite:///", 1)[-1].split("?")[0]
        if path and path != ":memory:":
            return path
    return DEFAULT_DB


def tags_for_name(name: str) -> list[str]:
    n = (name or "").lower()
    tags = set()

    # Type / moment
    sweet = any(k in n for k in ("cookie", "dessert", "chocolat", "pêches grillées"))
    sweet = sweet or ("muffin" in n and "pommes de terre" not in n and "pomme de terre" not in n and "patate" not in n)
    if sweet:
        tags.add("Dessert")
        if "cookie" in n or "muffin" in n:
            tags.add("Goûter")
    if "nectarine" in n and "poulet" in n:
        tags.discard("Dessert")
        tags.discard("Goûter")
    if any(k in n for k in ("apéro", "gougère", "empanada", "tempura")):
        tags.add("Apéro")
    if any(k in n for k in ("salade", "melon - jambon", "tomate mozza", "taboulé")):
        tags.add("Entrée")
        if "salade" in n:
            tags.add("Salade")
    if "soupe" in n:
        tags.add("Soupe")
        tags.add("Entrée")
    if any(k in n for k in ("oeuf", "omelette", "petit")) and "dessert" not in tags:
        if "oeuf" in n or "omelette" in n:
            tags.add("Petit-déjeuner")

    # Default plat if nothing else and looks like a main
    protein_or_main = any(
        k in n
        for k in (
            "poulet", "boeuf", "bœuf", "porc", "dinde", "saucisse", "jambon",
            "steak", "hâchis", "hachis", "lasagne", "pizza", "pâtes", "pates",
            "riz", "risotto", "couscous", "chili", "curry", "gratin", "quiche",
            "tartiflette", "raclette", "burrito", "burito", "wrap", "nugget",
            "poisson", "saumon", "cordon", "escalope", "rôti", "roti", "pavé",
            "pave", "parmentier", "tomates farcies", "ratatouille", "risotto",
            "kebbe", "tantuni", "moujadara", "rougail", "croque", "galette",
            "fondue", "tian", "jardinière", "jardiniere", "poisson", "viande",
            "boulette", "empanada", "frites", "purée", "puree",
        )
    )
    if protein_or_main and "Dessert" not in tags and "Apéro" not in tags:
        tags.add("Plat")
    if not tags:
        tags.add("Plat")

    # Protein / diet
    if any(k in n for k in ("poisson", "saumon")):
        tags.add("Poisson")
    if any(
        k in n
        for k in (
            "poulet", "boeuf", "bœuf", "porc", "dinde", "saucisse", "jambon",
            "steak", "lardon", "viande", "chorizo", "speck", "canard", "boulette",
            "hâchis", "hachis", "cordon", "kebbe", "tantuni",
        )
    ):
        tags.add("Viande")

    veg_signals = any(
        k in n
        for k in (
            "végétarien", "vegetarien", "vegan", "ratatouille", "tian",
            "chou-fleur", "légume", "legume", "lentille", "moujadara",
            "tempura de légumes", "fondue de légumes", "jardinière",
            "fleurettes", "haricots verts -", "pdt - carottes rôties",
            "potimarron", "salade méditerranéenne", "salade de chou",
            "galettes croustillantes aux légumes",
        )
    )
    meat_free_name = not any(
        k in n
        for k in (
            "poulet", "boeuf", "bœuf", "porc", "dinde", "saucisse", "jambon",
            "steak", "lardon", "viande", "chorizo", "speck", "canard",
            "saumon", "poisson", "cordon", "hâchis", "hachis",
        )
    )
    if veg_signals and meat_free_name:
        tags.add("Végétarien")
    if "vegan" in n:
        tags.add("Vegan")
        tags.discard("Végétarien")

    # Prep
    if any(k in n for k in ("four", "rôti", "roti", "gratin", "papillote", "papilotte", "tian")):
        tags.add("Four")
    if any(k in n for k in ("poêle", "poele", "plancha", "sauté", "saute", "teriyaki")):
        tags.add("Poêle")
    if any(k in n for k in ("rapide", "omelette", "oeufs à la coque", "croque", "wrap", "salade")):
        tags.add("Rapide")
    if any(k in n for k in ("batch", "couscous", "chili", "curry", "lasagne", "gratin", "parmentier")):
        tags.add("Batch cooking")

    # Format
    if "pâtes" in n or "pates" in n or "ravioli" in n or "macaroni" in n or "lasagne" in n:
        tags.add("Pâtes")
    if "salade" in n:
        tags.add("Salade")
    if "soupe" in n:
        tags.add("Soupe")

    # Cuisine
    if any(k in n for k in ("teriyaki", "chinois", "tempura", "riz chinois")):
        tags.add("Asiatique")
    if any(k in n for k in ("carbonara", "parmesan", "risotto", "mozza", "ravioli", "lasagne", "arrabiata")):
        tags.add("Italien")
    if any(k in n for k in ("mexicain", "burrito", "burito", "chili", "empanada", "chimuchurri")):
        tags.add("Mexicain")

    # Cap at 12
    ordered = [
        "Entrée", "Plat", "Dessert", "Petit-déjeuner", "Goûter", "Apéro",
        "Viande", "Poisson", "Végétarien", "Vegan",
        "Rapide", "Four", "Poêle", "Batch cooking",
        "Soupe", "Salade", "Pâtes",
        "Asiatique", "Italien", "Mexicain",
    ]
    result = [t for t in ordered if t in tags]
    return result[:12]


def ensure_tags_column(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info(meals)").fetchall()}
    if "tags" not in cols:
        conn.execute("ALTER TABLE meals ADD COLUMN tags JSON")
        conn.commit()


def main():
    db_path = get_db_path()
    if not os.path.isfile(db_path):
        print(f"DB not found: {db_path}")
        return 1

    conn = sqlite3.connect(db_path)
    ensure_tags_column(conn)
    rows = conn.execute("SELECT id, name FROM meals").fetchall()
    updated = 0
    for meal_id, name in rows:
        tags = tags_for_name(name)
        conn.execute(
            "UPDATE meals SET tags = ? WHERE id = ?",
            (json.dumps(tags, ensure_ascii=False), meal_id),
        )
        updated += 1
        print(f"{meal_id:4d}  {name}  ->  {', '.join(tags)}")
    conn.commit()
    conn.close()
    print(f"\nTagged {updated} meals in {db_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
