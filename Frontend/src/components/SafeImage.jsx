import { fallbackProducts } from "../data/fallbackProducts";

const fallbackSrc = fallbackProducts[0].images[0].secure_url;

export function SafeImage({ src, alt, ...props }) {
  return (
    <img
      src={src || fallbackSrc}
      alt={alt}
      onError={(event) => {
        if (event.currentTarget.src !== fallbackSrc) {
          event.currentTarget.src = fallbackSrc;
        }
      }}
      {...props}
    />
  );
}
