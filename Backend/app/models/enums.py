from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class ProductStatus(str, Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
    COMING_SOON = "coming_soon"
    PRE_ORDER = "pre_order"


class Gender(str, Enum):
    WOMEN = "women"
    MEN = "men"
    UNISEX = "unisex"
    KIDS = "kids"


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentProvider(str, Enum):
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    FAKE = "fake"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    INITIALIZED = "initialized"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
