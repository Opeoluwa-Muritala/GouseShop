const PAYSTACK_INLINE_SRC = "https://js.paystack.co/v2/inline.js";

let sdkPromise;

export function paystackAccessCode(payment) {
  return payment?.provider_response?.initialize?.data?.access_code;
}

export function paystackCheckoutUrl(payment) {
  return payment?.provider_checkout_url;
}

export async function openPaystackSdk(accessCode) {
  if (!accessCode) {
    throw new Error("Paystack access code is missing.");
  }

  const PaystackConstructor = await loadPaystackSdk();
  const popup = new PaystackConstructor();

  if (typeof popup.resumeTransaction !== "function") {
    throw new Error("Paystack SDK did not expose resumeTransaction.");
  }

  popup.resumeTransaction(accessCode);
}

function loadPaystackSdk() {
  if (window.Paystack || window.PaystackPop) {
    return Promise.resolve(window.Paystack || window.PaystackPop);
  }

  if (sdkPromise) return sdkPromise;

  sdkPromise = new Promise((resolve, reject) => {
    const existingScript = document.querySelector(`script[src="${PAYSTACK_INLINE_SRC}"]`);

    if (existingScript) {
      existingScript.addEventListener("load", () => resolve(window.Paystack || window.PaystackPop), { once: true });
      existingScript.addEventListener("error", () => reject(new Error("Unable to load Paystack SDK.")), { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = PAYSTACK_INLINE_SRC;
    script.async = true;
    script.onload = () => {
      const PaystackConstructor = window.Paystack || window.PaystackPop;
      if (PaystackConstructor) {
        resolve(PaystackConstructor);
      } else {
        reject(new Error("Paystack SDK loaded but no checkout object was found."));
      }
    };
    script.onerror = () => reject(new Error("Unable to load Paystack SDK."));
    document.body.appendChild(script);
  });

  return sdkPromise;
}
