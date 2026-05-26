import { fallbackProducts } from "../data/fallbackProducts";

export function money(value, currency = "NGN") {
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value || 0);
}

export function getImage(product) {
  const image = product.images?.find((item) => item.is_primary) || product.images?.[0];
  return image?.secure_url || image?.url || fallbackProducts[0].images[0].secure_url;
}
