import asyncio
import random
import re
import sys
from pathlib import Path

from sqlalchemy import delete, func, insert, select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import async_session
from app.models.catalog import Category, Collection, Fabric, Product, ProductCollection, ProductImage, Variant
from app.models.enums import Gender, ProductStatus

SEED_PREFIX = "seed"
PRODUCTS_PER_CATEGORY = 100

CATEGORIES = [
    {
        "name": "Dresses",
        "slug": "dresses",
        "description": "Occasion dresses, clean columns, slip silhouettes, and ceremony-ready pieces.",
        "query": "fashion,dress,model,editorial",
        "gender": Gender.WOMEN,
        "styles": ["Column Dress", "Slip Dress", "Wrap Dress", "Ceremony Dress", "Draped Dress"],
    },
    {
        "name": "Two-Piece Sets",
        "slug": "two-piece-sets",
        "description": "Coordinated tops and trousers, soft tailoring, and travel-ready sets.",
        "query": "fashion,two-piece,set,model",
        "gender": Gender.WOMEN,
        "styles": ["Draped Set", "Linen Set", "Tailored Set", "Resort Set", "Evening Set"],
    },
    {
        "name": "Tops",
        "slug": "tops",
        "description": "Blouses, shirts, tanks, and sculptural layers for everyday styling.",
        "query": "fashion,top,shirt,model",
        "gender": Gender.UNISEX,
        "styles": ["Linen Shirt", "Silk Blouse", "Rib Tank", "Wrap Top", "Utility Shirt"],
    },
    {
        "name": "Bottoms",
        "slug": "bottoms",
        "description": "Tailored trousers, easy skirts, and structured staples.",
        "query": "fashion,trousers,skirt,model",
        "gender": Gender.UNISEX,
        "styles": ["Wide Trouser", "Column Skirt", "Cargo Trouser", "Pleated Pant", "Wrap Skirt"],
    },
    {
        "name": "Outerwear",
        "slug": "outerwear",
        "description": "Layering pieces, jackets, coats, and refined utility silhouettes.",
        "query": "fashion,jacket,coat,model",
        "gender": Gender.UNISEX,
        "styles": ["Utility Jacket", "Cropped Blazer", "Long Coat", "Kimono Jacket", "Field Jacket"],
    },
    {
        "name": "Menswear",
        "slug": "menswear",
        "description": "Tailored shirts, relaxed sets, and clean everyday pieces for men.",
        "query": "menswear,shirt,trouser,model",
        "gender": Gender.MEN,
        "styles": ["Tailored Shirt", "Resort Shirt", "Structured Set", "Linen Tunic", "Utility Overshirt"],
    },
    {
        "name": "Womenswear",
        "slug": "womenswear",
        "description": "Dresses, sets, separates, and polished everyday pieces for women.",
        "query": "womenswear,dress,set,model",
        "gender": Gender.WOMEN,
        "styles": ["Bias Dress", "Draped Blouse", "Tailored Set", "Soft Trouser", "Occasion Top"],
    },
    {
        "name": "Children",
        "slug": "children",
        "description": "Easy occasion pieces, soft sets, and polished everyday clothing for children.",
        "query": "kidswear,children,clothing",
        "gender": Gender.KIDS,
        "styles": ["Play Set", "Cotton Shirt", "Occasion Dress", "Soft Trouser", "Layered Jacket"],
    },
    {
        "name": "Shirts",
        "slug": "shirts",
        "description": "Button-downs, relaxed collars, and crisp shirting staples.",
        "query": "fashion,shirt,model",
        "gender": Gender.MEN,
        "styles": ["Camp Shirt", "Oxford Shirt", "Linen Shirt", "Pleated Shirt", "Short Sleeve Shirt"],
    },
    {
        "name": "Trousers",
        "slug": "trousers",
        "description": "Clean trousers, wide-leg pants, and tailored bottoms.",
        "query": "fashion,trousers,pants,model",
        "gender": Gender.MEN,
        "styles": ["Wide Trouser", "Tapered Trouser", "Pleated Pant", "Drawstring Pant", "Cargo Pant"],
    },
    {
        "name": "Knitwear",
        "slug": "knitwear",
        "description": "Soft layers, ribbed tanks, polos, and lightweight knits.",
        "query": "fashion,knitwear,model",
        "gender": Gender.UNISEX,
        "styles": ["Rib Polo", "Knit Tank", "Soft Cardigan", "Sleeveless Knit", "Textured Pullover"],
    },
    {
        "name": "Accessories",
        "slug": "accessories",
        "description": "Finishing pieces, bags, scarves, and small styling details.",
        "query": "fashion,accessories,bag,scarf",
        "gender": Gender.UNISEX,
        "styles": ["Structured Bag", "Silk Scarf", "Travel Tote", "Leather Belt", "Evening Pouch"],
    },
]

FABRICS = [
    ("Linen", "linen"),
    ("Cotton", "cotton"),
    ("Silk", "silk"),
    ("Crepe", "crepe"),
    ("Denim", "denim"),
    ("Satin", "satin"),
]

COLLECTIONS = [
    ("New Ceremony", "new-ceremony"),
    ("Resort Ease", "resort-ease"),
    ("Lagos Edit", "lagos-edit"),
    ("Quiet Occasion", "quiet-occasion"),
]

COLORS = [
    ("Ivory", "#f6eee2"),
    ("Black", "#111111"),
    ("Olive", "#69715d"),
    ("Clay", "#a65b45"),
    ("Cocoa", "#5b4035"),
    ("Indigo", "#293a5f"),
]

PEXELS_IMAGE_IDS = [
    994523,
    985635,
    1036623,
    1462637,
    1536619,
    1559486,
    1926769,
    2065200,
    2703202,
    291762,
    5325881,
    6311392,
    7679720,
    7691168,
    7691168,
    7691178,
    7691224,
    845434,
    1040945,
    1040945,
    1043474,
    1183266,
    1300550,
    1311590,
    1620760,
    1689731,
    1707828,
    2090785,
    2613260,
    298863,
]

IMAGE_POOLS = {
    "dresses": [
        994523,
        985635,
        1036623,
        1462637,
    ],
    "two-piece-sets": [
        1536619,
        1559486,
        1926769,
        2065200,
    ],
    "tops": [
        2703202,
        291762,
        5325881,
        6311392,
    ],
    "bottoms": [
        7679720,
        7691168,
        7691168,
        7691178,
    ],
    "outerwear": [
        7691224,
        845434,
        1040945,
        1040945,
    ],
    "menswear": [
        1043474,
        1183266,
        1300550,
        1311590,
    ],
    "womenswear": [
        994523,
        985635,
        1536619,
        1926769,
    ],
    "children": [
        3662667,
        3661350,
        5560019,
        5623126,
    ],
    "shirts": [
        1620760,
        1689731,
        1707828,
        2090785,
    ],
    "trousers": [
        2613260,
        298863,
        1043474,
        1183266,
    ],
    "knitwear": [
        1300550,
        1311590,
        1620760,
        1689731,
    ],
    "accessories": [
        994523,
        2065200,
        2703202,
        7691224,
    ],
}

SIZES = ["XS", "S", "M", "L", "XL"]
NAME_PREFIXES = ["Ari", "Nara", "Eko", "Oro", "Sade", "Mina", "Zuri", "Ife", "Lumi", "Ayo"]


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def image_url(category: dict, product_index: int, image_index: int) -> str:
    pool = IMAGE_POOLS[category["slug"]]
    image_id = pool[(product_index + image_index) % len(pool)]
    return f"https://images.pexels.com/photos/{image_id}/pexels-photo-{image_id}.jpeg?auto=compress&cs=tinysrgb&w=900&h=1200&fit=crop"


async def get_or_create_taxonomy(session):
    categories = {}
    for sort_order, item in enumerate(CATEGORIES, start=1):
        category = (await session.execute(select(Category).where(Category.slug == item["slug"]))).scalar_one_or_none()
        if category is None:
            category = Category(
                name=item["name"],
                slug=item["slug"],
                description=item["description"],
                banner_url=image_url(item, 0, 0),
                sort_order=sort_order,
            )
            session.add(category)
            await session.flush()
        else:
            category.name = item["name"]
            category.description = item["description"]
            category.banner_url = image_url(item, 0, 0)
            category.sort_order = sort_order
        categories[item["slug"]] = category

    fabrics = {}
    for sort_order, (name, slug) in enumerate(FABRICS, start=1):
        fabric = (await session.execute(select(Fabric).where(Fabric.slug == slug))).scalar_one_or_none()
        if fabric is None:
            fabric = Fabric(name=name, slug=slug, description=f"{name} pieces for warm-weather dressing.", sort_order=sort_order)
            session.add(fabric)
            await session.flush()
        fabrics[slug] = fabric

    collections = {}
    for sort_order, (name, slug) in enumerate(COLLECTIONS, start=1):
        collection = (await session.execute(select(Collection).where(Collection.slug == slug))).scalar_one_or_none()
        if collection is None:
            collection = Collection(name=name, slug=slug, description=f"The {name} seasonal edit.", sort_order=sort_order)
            session.add(collection)
            await session.flush()
        collections[slug] = collection

    return categories, fabrics, collections


async def delete_existing_seed_products(session):
    seed_products = (await session.execute(select(Product.id).where(Product.slug.like(f"{SEED_PREFIX}-%")))).scalars().all()
    if not seed_products:
        return 0
    await session.execute(delete(ProductCollection).where(ProductCollection.product_id.in_(seed_products)))
    await session.execute(delete(Variant).where(Variant.product_id.in_(seed_products)))
    await session.execute(delete(ProductImage).where(ProductImage.product_id.in_(seed_products)))
    await session.execute(delete(Product).where(Product.id.in_(seed_products)))
    return len(seed_products)


def product_name(category: dict, index: int) -> str:
    prefix = NAME_PREFIXES[index % len(NAME_PREFIXES)]
    style = category["styles"][index % len(category["styles"])]
    return f"{prefix} {style} {index + 1:03d}"


def build_product_row(category_data, category, fabrics, collections, index):
    name = product_name(category_data, index)
    slug = f"{SEED_PREFIX}-{category_data['slug']}-{slugify(name)}"
    fabric = list(fabrics.values())[index % len(fabrics)]
    collection = list(collections.values())[index % len(collections)]
    base_price = 28000 + ((index * 1700) % 89000)
    is_sale = index % 11 == 0

    return {
        "name": name,
        "slug": slug,
        "description": (
            f"{name} in {fabric.name.lower()}, designed for polished everyday dressing, events, "
            f"and repeat styling across seasons."
        ),
        "price": base_price,
        "compare_at_price": base_price + 14000 if is_sale else None,
        "category_id": category.id,
        "fabric_id": fabric.id,
        "gender": category_data["gender"].value,
        "status": ProductStatus.ACTIVE.value,
        "is_featured": index % 9 == 0,
        "is_bestseller": index % 13 == 0,
        "is_sale": is_sale,
        "is_new_arrival": index % 7 == 0,
        "is_coming_soon": False,
        "is_preorder": index % 29 == 0,
        "search_vector": f"{name} {category.name} {fabric.name} {collection.name}",
    }


def build_child_rows(product_id, product_slug, product_name_value, category_data, collections, index):
    collection = list(collections.values())[index % len(collections)]
    product_collections = [{"product_id": product_id, "collection_id": collection.id}]
    images = []
    variants = []

    for image_index in range(3):
        images.append(
            {
                "product_id": product_id,
                "url": image_url(category_data, index, image_index),
                "secure_url": image_url(category_data, index, image_index),
                "public_id": f"online/{product_slug}/{image_index}",
                "alt": f"{product_name_value} editorial product image {image_index + 1}",
                "sort_order": image_index,
                "is_primary": image_index == 0,
                "width": 900,
                "height": 1200,
                "format": "jpg",
                "resource_type": "image",
            }
        )

    for variant_index, size in enumerate(SIZES):
        color_name, color_hex = COLORS[(index + variant_index) % len(COLORS)]
        variants.append(
            {
                "product_id": product_id,
                "sku": f"SEED-{category_data['slug'][:4].upper()}-{index + 1:03d}-{size}",
                "size": size,
                "color": color_name,
                "color_hex": color_hex,
                "stock_qty": random.randint(8, 44),
                "reserved_qty": 0,
                "additional_price": 0 if size in {"XS", "S", "M"} else 2500,
            }
        )
    return product_collections, images, variants


async def main():
    random.seed(42)
    async with async_session() as session:
        categories, fabrics, collections = await get_or_create_taxonomy(session)
        deleted = await delete_existing_seed_products(session)
        await session.commit()

        product_rows = []
        product_meta = []
        for category_data in CATEGORIES:
            category = categories[category_data["slug"]]
            for index in range(PRODUCTS_PER_CATEGORY):
                row = build_product_row(category_data, category, fabrics, collections, index)
                product_rows.append(row)
                product_meta.append((category_data, index, row["slug"], row["name"]))

        inserted = (
            await session.execute(
                insert(Product)
                .returning(Product.id, Product.slug)
                .execution_options(sort_by_parameter_order=True),
                product_rows,
            )
        ).all()
        product_ids_by_slug = {slug: product_id for product_id, slug in inserted}

        product_collection_rows = []
        image_rows = []
        variant_rows = []
        for category_data, index, product_slug, product_name_value in product_meta:
            product_id = product_ids_by_slug[product_slug]
            product_collections, images, variants = build_child_rows(
                product_id, product_slug, product_name_value, category_data, collections, index
            )
            product_collection_rows.extend(product_collections)
            image_rows.extend(images)
            variant_rows.extend(variants)

        await session.execute(insert(ProductCollection), product_collection_rows)
        await session.execute(insert(ProductImage), image_rows)
        await session.execute(insert(Variant), variant_rows)

        await session.commit()

        counts = (
            await session.execute(
                select(Category.slug, func.count(Product.id))
                .join(Product, Product.category_id == Category.id)
                .where(Product.slug.like(f"{SEED_PREFIX}-%"))
                .group_by(Category.slug)
                .order_by(Category.slug)
            )
        ).all()
        total = sum(count for _, count in counts)
        print(f"Deleted existing seed products: {deleted}")
        print(f"Created seed products: {total}")
        for slug, count in counts:
            print(f"{slug}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
