"""Product photos (<pack>/product_images.json): one verified image per genset product.

Each entry is {"file", "image_url", "page_url", "basis"}: basis says how close the photo is
("model" = that exact model, "series" = another size of the series, "family" = the maker's range
image). apply() copies the file into the frontend's public folder, and sets image, image_src and
image_basis on the product so the Products page shows it. A product with no entry keeps no image;
nothing is borrowed from another maker.
"""
import os
import shutil


def apply(data, images, src_dir, dest_dir):
    prods = data.get("PRODUCTS") or {}
    os.makedirs(dest_dir, exist_ok=True)
    n = missing = 0
    for pid, im in images.items():
        p = prods.get(pid)
        f = os.path.join(src_dir, im.get("file") or "")
        if p is None or not os.path.isfile(f):
            missing += 1
            continue
        shutil.copyfile(f, os.path.join(dest_dir, im["file"]))
        p["image"] = "/product-images/" + im["file"]
        p["image_src"] = im.get("page_url") or im.get("image_url")
        p["image_basis"] = im.get("basis")
        n += 1
    return {"set": n, "missing": missing, "without": len(prods) - n}


if __name__ == "__main__":
    import tempfile
    t = tempfile.mkdtemp()
    open(os.path.join(t, "a.jpg"), "wb").write(b"x")
    d = {"PRODUCTS": {"A-P1": {}, "A-P2": {}}}
    r = apply(d, {"A-P1": {"file": "a.jpg", "page_url": "https://x", "basis": "series"}, "GONE": {"file": "z.jpg"}}, t, os.path.join(t, "out"))
    assert r == {"set": 1, "missing": 1, "without": 1}, r
    assert d["PRODUCTS"]["A-P1"]["image"] == "/product-images/a.jpg" and "image" not in d["PRODUCTS"]["A-P2"]
    assert os.path.isfile(os.path.join(t, "out", "a.jpg"))
    print("ok")
